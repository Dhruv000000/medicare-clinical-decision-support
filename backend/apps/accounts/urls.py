# ==============================================================================
# FILE: backend/apps/accounts/urls.py
# PURPOSE: URL routing configuration for user authentication and session management endpoints.
# VIVA EXPLANATION: Maps REST endpoints for registration (/register/), JWT issuance (/login/), token rotation (/refresh/), logout (/logout/), and profile inspection (/me/).
# ==============================================================================

from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    MeView,
    TokenRefreshCustomView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshCustomView.as_view(), name="auth-refresh"),
    path("token/refresh/", TokenRefreshCustomView.as_view(), name="auth-token-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
]
