from django.urls import path
from .views import *


urlpatterns = [
    path('register/', UserRegistrationView.as_view()),
    path('mail-verification/<str:token>/', EmailVerificationView.as_view()),
    path('login/', UserLoginView.as_view()),
    path('resend-verification/', ResendMailVerificationView.as_view()),
]
