from django.urls import path
from . import views

urlpatterns = [
    path('', views.HealthCheckView.as_view(), name='health_check'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify-email'),
    path('regenerate-otp/', views.RegenerateOtpView.as_view(), name='regenerate-otp'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('password-reset-request/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile-update'),
    path('profile/', views.GetProfileView.as_view(), name='get-profile'),
    path('change-password/', views.ChangePasswordAPIView.as_view(), name='change-password'),
]