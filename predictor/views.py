from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.conf import settings
from django.views.decorators.cache import never_cache
from urllib.parse import urlencode
from functools import wraps
import pandas as pd
import os
from joblib import load
import io
import jwt

from authlib.integrations.django_client import OAuth


CAT_COLUMNS = ['job', 'marital', 'education', 'contact', 'month', 'poutcome']
BOOL_COLUMNS = ['housing', 'loan']

APP_CLIENT_ID = "app3-bank-client"
APP_REQUIRED_ROLE = "app3_user"


oauth = OAuth()
oauth.register(
    name='keycloak',
    client_id=settings.AUTHLIB_OAUTH_CLIENTS['keycloak']['client_id'],
    client_secret=settings.AUTHLIB_OAUTH_CLIENTS['keycloak']['client_secret'],
    server_metadata_url=settings.AUTHLIB_OAUTH_CLIENTS['keycloak']['server_metadata_url'],
    client_kwargs=settings.AUTHLIB_OAUTH_CLIENTS['keycloak']['client_kwargs'],
)


def preprocess(df, model_columns):
    for col in CAT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna('missing')
            dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
            df = pd.concat([df.drop(col, axis=1), dummies], axis=1)

    for col in BOOL_COLUMNS:
        if col in df.columns:
            df[col + '_new'] = df[col].apply(lambda x: 1 if str(x).lower() == 'yes' else 0)
            df.drop(col, axis=1, inplace=True)

    for col in model_columns:
        if col not in df.columns:
            df[col] = 0

    return df[model_columns]


def has_required_role(access_token, client_id, required_role):
    try:
        decoded = jwt.decode(
            access_token,
            options={"verify_signature": False, "verify_aud": False}
        )
    except Exception:
        return False

    realm_roles = decoded.get("realm_access", {}).get("roles", [])
    resource_access = decoded.get("resource_access", {})
    client_roles = resource_access.get(client_id, {}).get("roles", [])

    return required_role in realm_roles or required_role in client_roles


def require_app_role(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'user' not in request.session:
            return redirect('login')

        access_token = request.session.get('access_token')
        if not access_token:
            request.session.flush()
            return redirect('login')

        if not has_required_role(access_token, APP_CLIENT_ID, APP_REQUIRED_ROLE):
            return redirect('unauthorized_access')

        return view_func(request, *args, **kwargs)
    return wrapper


def home(request):
    return render(request, 'predictor/index.html', {
        'session_user': request.session.get('user')
    })

@never_cache
def login_view(request):
    if 'user' in request.session and request.GET.get("reauth") != "1":
        return redirect('home')

    redirect_uri = request.build_absolute_uri('/auth/callback/')

    if request.GET.get("reauth") == "1":
        return oauth.keycloak.authorize_redirect(
            request,
            redirect_uri,
            prompt="login"
        )

    return oauth.keycloak.authorize_redirect(request, redirect_uri)


@never_cache
def callback_view(request):
    error = request.GET.get("error")
    if error:
        return redirect('login')

    try:
        token = oauth.keycloak.authorize_access_token(request)
    except Exception:
        return redirect('login')

    access_token = token.get('access_token')
    if not access_token:
        return redirect('login')

    if not has_required_role(access_token, APP_CLIENT_ID, APP_REQUIRED_ROLE):
        request.session['id_token'] = token.get('id_token')
        return redirect('unauthorized_access')

    userinfo = token.get('userinfo')
    if not userinfo:
        userinfo = oauth.keycloak.userinfo(token=token)

    request.session['user'] = {
        'sub': userinfo.get('sub'),
        'username': userinfo.get('preferred_username'),
        'email': userinfo.get('email'),
        'name': userinfo.get('name'),
    }
    request.session['access_token'] = access_token
    request.session['id_token'] = token.get('id_token')

    return redirect('home')


@never_cache
def register_view(request):
    params = {
        'client_id': settings.AUTHLIB_OAUTH_CLIENTS['keycloak']['client_id'],
        'response_type': 'code',
        'scope': 'openid email profile',
        'redirect_uri': request.build_absolute_uri('/auth/callback/'),
        'kc_action': 'register',
    }
    register_url = (
        f"{settings.KEYCLOAK_SERVER_URL}/realms/"
        f"{settings.KEYCLOAK_REALM}/protocol/openid-connect/auth?{urlencode(params)}"
    )
    return redirect(register_url)


@never_cache
def unauthorized_access(request):
    id_token = request.session.get('id_token')

    request.session.pop('user', None)
    request.session.pop('access_token', None)
    request.session.pop('id_token', None)
    request.session.flush()

    post_logout_redirect_uri = request.build_absolute_uri('/login/?reauth=1')

    params = {
        "client_id": settings.AUTHLIB_OAUTH_CLIENTS['keycloak']['client_id'],
        "post_logout_redirect_uri": post_logout_redirect_uri,
    }

    if id_token:
        params["id_token_hint"] = id_token

    logout_url = (
        f"{settings.KEYCLOAK_SERVER_URL}/realms/"
        f"{settings.KEYCLOAK_REALM}/protocol/openid-connect/logout?"
        + urlencode(params)
    )
    return redirect(logout_url)


@never_cache
def logout_view(request):
    id_token = request.session.get('id_token')

    request.session.pop('user', None)
    request.session.pop('access_token', None)
    request.session.pop('id_token', None)
    request.session.flush()

    post_logout_redirect_uri = request.build_absolute_uri('/')

    params = {
        "client_id": settings.AUTHLIB_OAUTH_CLIENTS['keycloak']['client_id'],
        "post_logout_redirect_uri": post_logout_redirect_uri,
    }

    if id_token:
        params["id_token_hint"] = id_token

    logout_url = (
        f"{settings.KEYCLOAK_SERVER_URL}/realms/"
        f"{settings.KEYCLOAK_REALM}/protocol/openid-connect/logout?"
        + urlencode(params)
    )
    return redirect(logout_url)


@never_cache
@require_app_role
def predict_view(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        df = pd.read_csv(request.FILES['csv_file'])

        if 'y' in df.columns:
            df = df.drop(columns=['y'])

        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, 'model', 'term_deposit_prediction_model.joblib')

        if os.path.exists(model_path):
            model = load(model_path)
            model_columns = model.feature_names_in_

            df_processed = preprocess(df.copy(), model_columns)
            preds = model.predict(df_processed)
            preds = ['Yes' if p == 1 else 'No' for p in preds]

            df['Prediction'] = preds

            buffer = io.StringIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)

            response = HttpResponse(buffer.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=predictions.csv'
            return response

        return HttpResponse("Model file not found. Please train the model first.", status=500)

    return redirect('/')