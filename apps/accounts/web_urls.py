"""Web page routes for the accounts module."""
from django.urls import path

from .views import LoginPageView, LogoutPageView, RegisterPageView

urlpatterns = [
    path("login/", LoginPageView.as_view(), name="login-page"),
    path("logout/", LogoutPageView.as_view(), name="logout-page"),
    path("register/", RegisterPageView.as_view(), name="register-page"),
]
