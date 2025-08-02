from rest_framework import serializers
from .models import CaseDetails, Transaction
from decimal import Decimal

class NullableDateField(serializers.DateField):
    def to_internal_value(self, value):
        if value in ("", None):
            return None
        return super().to_internal_value(value)

class CaseCreateSerializer(serializers.ModelSerializer):
    caseName = serializers.CharField()
    courtName = serializers.CharField()
    courtCaseNumber = serializers.CharField()
    judgmentAmount = serializers.DecimalField(max_digits=12, decimal_places=4)
    judgmentDate = serializers.DateField()
    # lastPaymentDate = serializers.DateField(required=False)
    # lastPaymentDate = serializers.DateField(required=False, allow_null=True)
    lastPaymentDate = NullableDateField(required=False, allow_null=True)
    totalPayments = serializers.DecimalField(max_digits=12, decimal_places=4)
    accruedInterest = serializers.DecimalField(max_digits=12, decimal_places=4)
    principalBalance = serializers.DecimalField(max_digits=12, decimal_places=4)
    payoffAmount = serializers.DecimalField(max_digits=12, decimal_places=4)
    interestRate = serializers.DecimalField(max_digits=6, decimal_places=4)
    isEnded = serializers.BooleanField(required=False)
    debtorInfo = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = CaseDetails
        fields = [
            'id',
            'caseName',
            'courtName',
            'courtCaseNumber',
            'judgmentAmount',
            'judgmentDate',
            'lastPaymentDate',
            'totalPayments',
            'accruedInterest',
            'principalBalance',
            'payoffAmount',
            'interestRate',
            'isEnded',
            'debtorInfo'
        ]

    def validate(self, data):
        return data


class CaseListSerializer(serializers.ModelSerializer):
    caseName = serializers.CharField(source='case_name')
    courtName = serializers.CharField(source='court_name')
    courtCaseNumber = serializers.CharField(source='court_case_number')
    payoffAmount = serializers.DecimalField(source='payoff_amount', max_digits=12, decimal_places=4)

    class Meta:
        model = CaseDetails
        fields = ['id', 'caseName', 'courtName', 'courtCaseNumber', 'payoffAmount']

class CaseDetailSerializer(serializers.ModelSerializer):
    caseName = serializers.CharField(source='case_name')
    courtName = serializers.CharField(source='court_name')
    courtCaseNumber = serializers.CharField(source='court_case_number')
    judgmentAmount = serializers.DecimalField(source='judgment_amount', max_digits=12, decimal_places=4)
    judgmentDate = serializers.DateField(source='judgment_date')
    lastPaymentDate = serializers.DateField(source='last_payment_date', allow_null=True)
    createdAt = serializers.DateTimeField(source='created_at')
    totalPayments = serializers.DecimalField(source='total_payments', max_digits=12, decimal_places=4)
    accruedInterest = serializers.DecimalField(source='accrued_interest', max_digits=12, decimal_places=4)
    principalBalance = serializers.SerializerMethodField()
    payoffAmount = serializers.DecimalField(source='today_payoff', max_digits=12, decimal_places=4)

    class Meta:
        model = CaseDetails
        fields = [
            'id',
            'caseName',
            'courtName',
            'courtCaseNumber',
            'judgmentAmount',
            'judgmentDate',
            'lastPaymentDate',
            'totalPayments',
            'accruedInterest',
            'principalBalance',
            'payoffAmount',
            'createdAt',
        ]

    def get_principalBalance(self, obj):
        # Principal = judgment_amount - total_payments
        return obj.judgment_amount - obj.total_payments

class TransactionCreateSerializer(serializers.Serializer):
    case_id = serializers.IntegerField()
    transaction_type = serializers.ChoiceField(choices=['PAYMENT', 'COST'])
    amount = serializers.DecimalField(max_digits=12, decimal_places=4)
    date = serializers.DateField()
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    # new_balance = serializers.DecimalField(max_digits=12, decimal_places=4)

    def validate_case_id(self, value):
        request = self.context.get('request')
        if not CaseDetails.objects.filter(id=value, user=request.user, is_active=True).exists():
            raise serializers.ValidationError("Case not found or access denied.")
        return value
    

# class TransactionDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Transaction
#         fields = [
#             'id',
#             'date',
#             'transaction_type',
#             'amount',
#             'accrued_interest',
#             'principal_balance',
#             'description',
#         ]

class TransactionDetailSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='transaction_type')
    interestRate = serializers.SerializerMethodField()
    calculatedInterest = serializers.DecimalField(source='accrued_interest', max_digits=12, decimal_places=4)
    newBalance = serializers.DecimalField(source='principal_balance', max_digits=12, decimal_places=4)

    class Meta:
        model = Transaction
        fields = [
            'id',
            'type',
            'amount',
            'date',
            'description',
            'interestRate',
            'calculatedInterest',
            'newBalance',
        ]

    def get_interestRate(self, obj):
        # Access interest rate from related CaseDetails
        return float(obj.case.interest_rate)

class TransactionUpdateSerializer(serializers.ModelSerializer):
    new_balance = serializers.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        model = Transaction
        fields = ['transaction_type', 'amount', 'date', 'description', 'new_balance']
