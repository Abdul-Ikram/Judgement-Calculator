import json
import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from finance.models import Subscription
# from datetime import timezone
from django.utils import timezone
from authentication.models import User
from dateutil.relativedelta import relativedelta


stripe.api_key = settings.STRIPE_SECRET_KEY


# class CreateCheckoutSessionView(APIView):
#     """
#     API view to create a Stripe Checkout Session.
#     """
#     # permission_classes = [AllowAny]

#     def post(self, request):
#         data = request.data
#         user = request.user

#         try:
#             checkout_session = stripe.checkout.Session.create(
#                 line_items=[
#                     {
#                         "price_data": {
#                             "currency": "usd",
#                             "product_data": {
#                                 "name": "Django Stripe Checkout",
#                             },
#                             "unit_amount": int(data.get("price")) * 100,
#                         },
#                         "quantity": 1,
#                     }
#                 ],
#                 metadata={
#                     "user_id": user.id,
#                     "email": user.email,
#                 },
#                 mode="payment",
#                 success_url=settings.BASE_URL + "/stripe/api/success/?session_id={CHECKOUT_SESSION_ID}",
#                 cancel_url=settings.BASE_URL + "/cancel/",
#                 customer_email=data.get("email"),
#             )

#             print("Checkout URL:", checkout_session.url)
#             return JsonResponse({"checkout_url": checkout_session.url}, status=status.HTTP_200_OK)

#         except Exception as e:
#             print("Stripe error:", str(e))
#             return JsonResponse({
#                 "status_code": 500,
#                 "message": "Stripe session creation failed."
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class PaymentSuccessView(APIView):
#     """
#     API view to handle successful payments and retrieve session details.
#     """
#     permission_classes = [AllowAny]

#     def get(self, request):
#         session_id = request.GET.get("session_id")
#         if not session_id:
#             return JsonResponse({
#                 "status_code": 400,
#                 "message": "Missing session_id"
#             }, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             session = stripe.checkout.Session.retrieve(session_id)
#             customer = session.get("customer_details", {})
#             amount_total = session.get("amount_total", 0) / 100
#             currency = session.get("currency", "usd").upper()

#             print("✅ Payment Successful")
#             print("Session ID:", session_id)
#             print("Amount:", amount_total, currency)
#             print("Email:", customer.get("email"))
#             print("Name:", customer.get("name"))
#             print("Payment Status:", session.get("payment_status"))
#             print("Metadata:", session.get("metadata"))

#             return JsonResponse({
#                 "message": "Payment successful!",
#                 "session_id": session_id,
#                 "amount": f"{amount_total} {currency}",
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             print("Error fetching session:", str(e))
#             return JsonResponse({
#                 "status_code": 400,
#                 "message": "Invalid session ID"
#             }, status=status.HTTP_400_BAD_REQUEST)


# @method_decorator(csrf_exempt, name='dispatch')
# class StripeWebhookView(APIView):
#     """
#     API view to handle Stripe Webhook events.
#     """
#     permission_classes = [AllowAny]

#     def post(self, request):
#         payload = request.body
#         sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
#         event = None

#         try:
#             if settings.STRIPE_WEBHOOK_SECRET and sig_header:
#                 event = stripe.Webhook.construct_event(
#                     payload=payload,
#                     sig_header=sig_header,
#                     secret=settings.STRIPE_WEBHOOK_SECRET
#                 )
#             else:
#                 event = json.loads(payload)
#         except Exception as e:
#             print("⚠️  Webhook error:", e)
#             return HttpResponseBadRequest(str(e))

#         print(f"✅ Received event: {event['type']}")

#         if event["type"] == "checkout.session.completed":
#             session_data = event["data"]["object"]

#             print("✅ Checkout session completed:")
#             print("Session ID:", session_data["id"])
#             print("Email:", session_data["customer_details"]["email"])
#             print("Name:", session_data["customer_details"].get("name"))
#             print("Amount:", session_data["amount_total"] / 100)
#             print("Currency:", session_data["currency"])
#             print("Payment Status:", session_data["payment_status"])
#             print("Metadata:", session_data["metadata"])

#         return HttpResponse(status=200)

class CreateCheckoutSessionView(APIView):
    """
    API view to create a Stripe Checkout Session for subscriptions.
    """

    def post(self, request):
        data = request.data
        user = request.user

        price = data.get("price")
        interval = data.get("interval")
        email = data.get("email", user.email)

        if not price or not interval:
            return JsonResponse({
                "status_code": 400,
                "message": "Price and interval ('month' or 'year') are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        if interval not in ["month", "year"]:
            return JsonResponse({
                "status_code": 400,
                "message": "Invalid interval. Must be 'month' or 'year'."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create a product & recurring price in Stripe
            product = stripe.Product.create(name="Subscription Plan")

            stripe_price = stripe.Price.create(
                unit_amount=int(price) * 100,  # Convert to cents
                currency="usd",
                recurring={"interval": interval},
                product=product.id,
            )

            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        "price": stripe_price.id,
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                metadata={
                    "user_id": user.id,
                    "email": email,
                    "interval": interval,
                    "price": price
                },
                # success_url=settings.BASE_URL + "/stripe/api/success/?session_id={CHECKOUT_SESSION_ID}",
                success_url = "https://calcjuris.vercel.app/home?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=settings.BASE_URL + "/cancel/",
                customer_email=email,
            )

            return JsonResponse(
                {"checkout_url": checkout_session.url},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            print("Stripe error:", str(e))
            return JsonResponse({
                "status_code": 500,
                "message": f"Stripe session creation failed: {str(e)}"
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

            return JsonResponse({
                "message": "Payment successful!",
                "session_id": session_id,
                "amount": f"{amount_total} {currency}",
                "payment_status": session.get("payment_status"),
                "email": customer.get("email"),
                "name": customer.get("name"),
                "metadata": session.get("metadata")
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
            metadata = session_data.get("metadata", {})
            user_id = metadata.get("user_id")
            price = metadata.get("price")
            interval = metadata.get("interval")

            try:
                user = User.objects.get(id=user_id)
                user.is_paid = True
                user.payment_status = "paid"  # or "premium"
                user.amount = price
                user.save()

                # Save subscription record
                Subscription.objects.create(
                    user=user,
                    stripe_customer_id=session_data.get("customer"),
                    stripe_subscription_id=session_data.get("subscription"),
                    stripe_price_id=session_data.get("items", [{}])[0].get("price", ""),
                    stripe_product_id="",
                    plan_name="Subscription Plan",
                    interval=interval,
                    amount=price,
                    currency=session_data.get("currency", "usd"),
                    status="active",
                    start_date=timezone.now(),
                    end_date=timezone.now() + relativedelta(months=1 if interval == "month" else 12)
                )

                print(f"💾 Subscription saved for user {user.email}")

            except User.DoesNotExist:
                print(f"⚠️ User with ID {user_id} not found.")

        return HttpResponse(status=200)
