from django.urls import path
from .views import (
    CreateCheckoutSessionView,
    PaymentSuccessView,
    StripeWebhookView,
)

urlpatterns = [
    path('checkout/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('success/', PaymentSuccessView.as_view(), name='payment-success'),
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]
