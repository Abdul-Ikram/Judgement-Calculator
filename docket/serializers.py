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
    class Meta:
        model = CaseDetails
        fields = ['id', 'case_name', 'court_name', 'court_case_number', 'payoff_amount']


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
    

class TransactionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'date',
            'transaction_type',
            'amount',
            'accrued_interest',
            'principal_balance',
            'description',
        ]


class TransactionUpdateSerializer(serializers.ModelSerializer):
    new_balance = serializers.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        model = Transaction
        fields = ['transaction_type', 'amount', 'date', 'description', 'new_balance']
