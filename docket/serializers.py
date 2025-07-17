from rest_framework import serializers
from .models import CaseDetails, Transaction
from decimal import Decimal


class CaseCreateSerializer(serializers.ModelSerializer):
    # Frontend-named fields
    principal_reduction = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    costs_after_judgment = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    total_interest = serializers.DecimalField(max_digits=12, decimal_places=2)
    grand_total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        model = CaseDetails
        fields = [
            'case_name',
            'court_name',
            'court_case_number',
            'judgment_amount',
            'interest_rate',
            'judgment_date',
            'principal_reduction',
            'costs_after_judgment',
            'total_interest',
            'grand_total_amount',
            'debtor_info',
        ]

    def validate(self, data):
        return data


class CaseListSerializer(serializers.ModelSerializer):
    caseName = serializers.CharField(source='case_name')
    courtName = serializers.CharField(source='court_name')
    courtCaseNumber = serializers.CharField(source='court_case_number')
    payoffAmount = serializers.DecimalField(source='payoff_amount', max_digits=12, decimal_places=2)

    class Meta:
        model = CaseDetails
        fields = ['id', 'caseName', 'courtName', 'courtCaseNumber', 'payoffAmount']

class CaseDetailSerializer(serializers.ModelSerializer):
    caseName = serializers.CharField(source='case_name')
    courtName = serializers.CharField(source='court_name')
    courtCaseNumber = serializers.CharField(source='court_case_number')
    judgmentAmount = serializers.DecimalField(source='judgment_amount', max_digits=12, decimal_places=2)
    judgmentDate = serializers.DateField(source='judgment_date')
    lastPaymentDate = serializers.DateField(source='last_payment_date', allow_null=True)
    totalPayments = serializers.DecimalField(source='total_payments', max_digits=12, decimal_places=2)
    accruedInterest = serializers.DecimalField(source='accrued_interest', max_digits=12, decimal_places=2)
    principalBalance = serializers.SerializerMethodField()
    payoffAmount = serializers.DecimalField(source='payoff_amount', max_digits=12, decimal_places=2)

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
        ]

    def get_principalBalance(self, obj):
        # Principal = judgment_amount - total_payments
        return obj.judgment_amount - obj.total_payments

class TransactionCreateSerializer(serializers.Serializer):
    case_id = serializers.IntegerField()
    transaction_type = serializers.ChoiceField(choices=['PAYMENT', 'COST'])
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    date = serializers.DateField()
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    new_balance = serializers.DecimalField(max_digits=12, decimal_places=2)

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
    calculatedInterest = serializers.DecimalField(source='accrued_interest', max_digits=12, decimal_places=2)
    newBalance = serializers.DecimalField(source='principal_balance', max_digits=12, decimal_places=2)

    class Meta:
        model = Transaction
        fields = [
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
    new_balance = serializers.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        model = Transaction
        fields = ['transaction_type', 'amount', 'date', 'description', 'new_balance']
