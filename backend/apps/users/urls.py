from django.urls import path
from .views import (
    LoginView, CreateUserView, SetPasswordView, UserListView,
    BlacklistUserView, ChangeRoleView, ProfileView, DashboardStatsView,
    VerifySetupTokenView, PingUserView, ChangePasswordView,
    ForgotPasswordView, UserStatsView,
    CookieTokenRefreshView, LogoutView,
    ResendActivationView, MeasureBreakdownView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('create-user/', CreateUserView.as_view(), name='create-user'),
    path('resend-activation/', ResendActivationView.as_view(), name='resend-activation'),
    path('set-password/', SetPasswordView.as_view(), name='set-password'),
    path('verify-token/', VerifySetupTokenView.as_view(), name='verify-token'),
    path('users/stats/', UserStatsView.as_view(), name='user-stats'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<str:public_id>/blacklist/', BlacklistUserView.as_view(), name='blacklist-user'),
    path('users/<str:public_id>/change-role/', ChangeRoleView.as_view(), name='change-role'),
    path('users/<str:public_id>/ping/', PingUserView.as_view(), name='ping-user'),
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('measure-breakdown/', MeasureBreakdownView.as_view(), name='measure-breakdown'),
]