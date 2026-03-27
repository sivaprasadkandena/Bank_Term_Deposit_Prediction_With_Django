from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('auth/callback/', views.callback_view, name='callback'),
    path('predict/', views.predict_view, name='predict'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('unauthorized-access/', views.unauthorized_access, name='unauthorized_access'),
]