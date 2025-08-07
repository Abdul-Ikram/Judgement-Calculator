import json
import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status


stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSessionView(APIView):
    """
    API view to create a Stripe Checkout Session.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": "Django Stripe Checkout",
                            },
                            "unit_amount": int(data.get("price")) * 100,
                        },
                        "quantity": 1,
                    }
                ],
                metadata={
                    "user_id": data.get("user_id"),
                    "email": data.get("email"),
                    "request_id": data.get("request_id"),
                },
                mode="payment",
                success_url=settings.BASE_URL + "/stripe/api/success/?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=settings.BASE_URL + "/cancel/",
                customer_email=data.get("email"),
            )

            print("Checkout URL:", checkout_session.url)
            return JsonResponse({"checkout_url": checkout_session.url}, status=status.HTTP_200_OK)

        except Exception as e:
            print("Stripe error:", str(e))
            return JsonResponse({
                "status_code": 500,
                "message": "Stripe session creation failed."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentSuccessView(APIView):
    """
    API view to handle successful payments and retrieve session details.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        session_id = request.GET.get("session_id")
        if not session_id:
            return JsonResponse({
                "status_code": 400,
                "message": "Missing session_id"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = stripe.checkout.Session.retrieve(session_id)
            customer = session.get("customer_details", {})
            amount_total = session.get("amount_total", 0) / 100
            currency = session.get("currency", "usd").upper()

            print("✅ Payment Successful")
            print("Session ID:", session_id)
            print("Amount:", amount_total, currency)
            print("Email:", customer.get("email"))
            print("Name:", customer.get("name"))
            print("Payment Status:", session.get("payment_status"))
            print("Metadata:", session.get("metadata"))

            return JsonResponse({
                "message": "Payment successful!",
                "session_id": session_id,
                "amount": f"{amount_total} {currency}",
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print("Error fetching session:", str(e))
            return JsonResponse({
                "status_code": 400,
                "message": "Invalid session ID"
            }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    API view to handle Stripe Webhook events.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        event = None

        try:
            if settings.STRIPE_WEBHOOK_SECRET and sig_header:
                event = stripe.Webhook.construct_event(
                    payload=payload,
                    sig_header=sig_header,
                    secret=settings.STRIPE_WEBHOOK_SECRET
                )
            else:
                event = json.loads(payload)
        except Exception as e:
            print("⚠️  Webhook error:", e)
            return HttpResponseBadRequest(str(e))

        print(f"✅ Received event: {event['type']}")

        if event["type"] == "checkout.session.completed":
            session_data = event["data"]["object"]

            print("✅ Checkout session completed:")
            print("Session ID:", session_data["id"])
            print("Email:", session_data["customer_details"]["email"])
            print("Name:", session_data["customer_details"].get("name"))
            print("Amount:", session_data["amount_total"] / 100)
            print("Currency:", session_data["currency"])
            print("Payment Status:", session_data["payment_status"])
            print("Metadata:", session_data["metadata"])

        return HttpResponse(status=200)
