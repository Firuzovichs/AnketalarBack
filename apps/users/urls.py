from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from .views import (
    SendOTPView, VerifyOTPView, RegisterView, LoginView,
    MeView, ProfileSetupView, FaceScanView, TermsStatusView, TermsAcceptView,
    PhotoUploadView, PhotoDeleteView,
    InterestListView, GoalListView,
    PasswordResetRequestView, PasswordResetConfirmView,
    BlockUserView, UnblockUserView,
    AccountDeletionRequestView,
    UserDetailView,
)

urlpatterns = [
    # Auth
    path('send-otp/',    SendOTPView.as_view(),    name='send-otp'),
    path('verify-otp/',  VerifyOTPView.as_view(),  name='verify-otp'),
    path('register/',    RegisterView.as_view(),   name='register'),
    path('login/',       LoginView.as_view(),      name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/',      TokenBlacklistView.as_view(), name='logout'),

    # Profile
    path('me/',          MeView.as_view(),          name='me'),
    path('terms-status/', TermsStatusView.as_view(),  name='terms-status'),
    path('terms-accept/', TermsAcceptView.as_view(),  name='terms-accept'),
    path('profile/setup/', ProfileSetupView.as_view(), name='profile-setup'),
    path('profile/face-scan/', FaceScanView.as_view(), name='face-scan'),

    # Photos
    path('photos/',        PhotoUploadView.as_view(),      name='photos'),
    path('photos/<int:pk>/', PhotoDeleteView.as_view(),    name='photo-delete'),

    # Lookups
    path('interests/', InterestListView.as_view(), name='interests'),
    path('goals/',     GoalListView.as_view(),     name='goals'),

    # Parolni tiklash
    path('password-reset/',         PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    # Bloklash (+ adminga avtomatik shikoyat)
    path('block/<int:user_id>/',   BlockUserView.as_view(),   name='block-user'),
    path('unblock/<int:user_id>/', UnblockUserView.as_view(), name='unblock-user'),

    # Hisobni o'chirish so'rovi (admin tasdiqlasa is_active=False bo'ladi)
    path('account/delete-request/', AccountDeletionRequestView.as_view(), name='account-delete-request'),

    # Boshqa foydalanuvchi profili
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]
