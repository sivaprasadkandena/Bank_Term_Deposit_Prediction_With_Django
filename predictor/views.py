from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.conf import settings
from urllib.parse import urlencode
import pandas as pd
import os
from joblib import load
import io

CAT_COLUMNS = ['job', 'marital', 'education', 'contact', 'month', 'poutcome']
BOOL_COLUMNS = ['housing', 'loan']

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

    df = df[model_columns]
    return df

def home(request):
    return render(request, 'predictor/index.html')

@login_required
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

def register_view(request):
    params = {
        'client_id': settings.OIDC_RP_CLIENT_ID,
        'response_type': 'code',
        'scope': 'openid email profile',
        'redirect_uri': request.build_absolute_uri('/oidc/callback/'),
        'kc_action': 'register',
    }
    register_url = f"{settings.OIDC_OP_AUTHORIZATION_ENDPOINT}?{urlencode(params)}"
    return redirect(register_url)

def logout_view(request):
    logout(request)
    return redirect('/')