from django.urls import path
from .views import (
    CreateCheckoutSessionView,
    CheckoutSuccessView,
    StripeWebhookView,
    SubscriptionDetailView,
    CancelSubscriptionView
)

urlpatterns = [
    path('create-checkout/', CreateCheckoutSessionView.as_view(), name='create-checkout'),
    path('success/', CheckoutSuccessView.as_view(), name='checkout-success'),
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('detail/', SubscriptionDetailView.as_view(), name='subscription-detail'),
    path('cancel/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
]