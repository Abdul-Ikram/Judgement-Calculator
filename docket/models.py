from django.db import models
from authentication.models import User
from django.utils import timezone
from decimal import Decimal


class CaseDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    case_name = models.CharField(max_length=100)
    court_name = models.CharField(max_length=100)
    court_case_number = models.CharField(max_length=50, unique=True)

    judgment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual interest rate (%)")
    judgment_date = models.DateField()

    last_payment_date = models.DateField(null=True, blank=True)
    total_payments = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    accrued_interest = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    payoff_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'case_details'

    def __str__(self):
        return f"{self.case_name} - {self.court_case_number}"


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('COST', 'Cost'),
        ('INTEREST', 'Interest'),
        ('PAYMENT', 'Payment'),
    ]

    case = models.ForeignKey(CaseDetails, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    accrued_interest = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    principal_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    description = models.TextField(null=True, blank=True)

    date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True, null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-date']

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} on {self.date}"
