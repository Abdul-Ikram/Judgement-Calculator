from django.db import models
from django.conf import settings

class Subscription(models.Model):
    PLAN_INTERVAL_CHOICES = [
        ('month', 'Monthly'),
        ('year', 'Yearly'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
        ('past_due', 'Past Due'),
        ('unpaid', 'Unpaid'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    
    # Stripe references
    stripe_customer_id = models.CharField(max_length=255)
    stripe_subscription_id = models.CharField(max_length=255)
    stripe_price_id = models.CharField(max_length=255)
    stripe_product_id = models.CharField(max_length=255)
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)

    # Plan details
    plan_name = models.CharField(max_length=100)
    interval = models.CharField(max_length=10, choices=PLAN_INTERVAL_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='usd')

    # Status & Dates
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription'

    def __str__(self):
        return f"{self.user.email} - {self.plan_name} ({self.interval})"
