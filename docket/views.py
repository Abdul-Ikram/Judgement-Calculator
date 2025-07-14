from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction
from .models import CaseDetails, Transaction
from decimal import Decimal
from django.utils import timezone
from rest_framework.generics import ListAPIView
from .serializers import CaseCreateSerializer, CaseListSerializer, TransactionCreateSerializer, TransactionDetailSerializer, TransactionUpdateSerializer
from django.db import transaction as db_transaction
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from .models import CaseDetails
from django.utils.timezone import now


class AddCaseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CaseCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    user = request.user
                    data = serializer.validated_data

                    case = CaseDetails.objects.create(
                        user=user,
                        case_name=data['case_name'],
                        court_name=data['court_name'],
                        court_case_number=data['court_case_number'],
                        judgment_amount=data['judgment_amount'],
                        interest_rate=data['interest_rate'],
                        judgment_date=data['judgment_date'],
                        total_payments=data.get('principal_reduction', Decimal('0.00')),
                        accrued_interest=data['total_interest'],
                        payoff_amount=data['grand_total_amount'],
                        last_payment_date=data['judgment_date'] if 'principal_reduction' in data else None,
                    )

                    # Save transactions if provided
                    if 'principal_reduction' in data:
                        Transaction.objects.create(
                            case=case,
                            transaction_type='PAYMENT',
                            amount=data['principal_reduction'],
                            principal_balance=case.payoff_amount,
                            accrued_interest=data['total_interest'],
                            date=timezone.now()
                        )

                    if 'costs_after_judgment' in data:
                        Transaction.objects.create(
                            case=case,
                            transaction_type='COST',
                            amount=data['costs_after_judgment'],
                            principal_balance=case.payoff_amount,
                            accrued_interest=data['total_interest'],
                            date=timezone.now()
                        )

                    return Response({
                        'status_code': 201,
                        'message': 'Case created successfully.',
                        'data': {
                            'case_id': case.id,
                            'grand_total_amount': str(case.payoff_amount)
                        }
                    }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({
                    'status_code': 500,
                    'message': f'Error creating case: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'status_code': 400,
            'message': 'Validation failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CaseListView(ListAPIView):
    serializer_class = CaseListSerializer

    def get_queryset(self):
        # Return only active cases for the authenticated user
        return CaseDetails.objects.filter(user=self.request.user, is_active=True).order_by('-created_at')


class CreateTransactionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TransactionCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                with transaction.atomic():
                    case = CaseDetails.objects.get(id=data['case_id'], user=request.user, is_active=True)

                    # Create transaction
                    tx = Transaction.objects.create(
                        case=case,
                        transaction_type=data['transaction_type'],
                        amount=data['amount'],
                        accrued_interest=case.accrued_interest,
                        principal_balance=data['new_balance'],
                        date=data['date'],
                        description=data.get('description', '')
                    )

                    # Update case payoff
                    case.payoff_amount = data['new_balance']

                    # Update payments if it's a payment
                    if data['transaction_type'] == 'PAYMENT':
                        case.total_payments += data['amount']
                        case.last_payment_date = data['date']

                    case.save()

                    return Response({
                        'status_code': 201,
                        'message': 'Transaction added successfully.',
                        'transaction_id': tx.id
                    }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({
                    'status_code': 500,
                    'message': f"An error occurred: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'status_code': 400,
            'message': 'Invalid input',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TransactionListByCaseView(ListAPIView):
    serializer_class = TransactionDetailSerializer

    def get_queryset(self):
        case_id = self.kwargs.get('case_id')

        # Ensure user owns this case
        case = CaseDetails.objects.filter(id=case_id, user=self.request.user, is_active=True).first()
        if not case:
            return Transaction.objects.none()

        return Transaction.objects.filter(case=case).order_by('-date')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({
                "status_code": 404,
                "message": "No transactions found or case not accessible."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status_code": 200,
            "message": "Transactions retrieved successfully.",
            "transactions": serializer.data
        }, status=status.HTTP_200_OK)


class UpdateTransactionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, transaction_id):
        try:
            tx = Transaction.objects.select_related('case').get(id=transaction_id, case__user=request.user)
        except Transaction.DoesNotExist:
            return Response({
                'status_code': 404,
                'message': 'Transaction not found or access denied.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TransactionUpdateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            with db_transaction.atomic():
                case = tx.case

                # If transaction type is PAYMENT and amount changed, adjust total_payments
                if tx.transaction_type == 'PAYMENT':
                    case.total_payments -= tx.amount  # Subtract old
                if data['transaction_type'] == 'PAYMENT':
                    case.total_payments += data['amount']  # Add new
                    case.last_payment_date = data['date']

                # Update case payoff
                case.payoff_amount = data['new_balance']
                case.save()

                # Update transaction
                tx.transaction_type = data['transaction_type']
                tx.amount = data['amount']
                tx.date = data['date']
                tx.description = data['description']
                tx.principal_balance = data['new_balance']
                tx.save()

                return Response({
                    'status_code': 200,
                    'message': 'Transaction updated successfully.'
                }, status=status.HTTP_200_OK)

        return Response({
            'status_code': 400,
            'message': 'Invalid input.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class GeneratePayoffPDFView(APIView):
    def get(self, request, case_id):
        try:
            case = CaseDetails.objects.get(id=case_id, user=request.user)
        except CaseDetails.DoesNotExist:
            return HttpResponse("Case not found.", status=404)

        transactions = case.transactions.all().order_by('date')
        daily_interest = case.judgment_amount * (case.interest_rate / 100) / 365

        html_string = render_to_string('docket/payoff_statement.html', {
            'case': case,
            'transactions': transactions,
            'daily_interest': f"{daily_interest:.2f}",
            'interest_start_date': now().date(),
            'today': now().date(),
            'lawyer': {
                'name': 'John A. Smith, Esq.',
                'firm': 'Smith Jones & Kaplan LLP',
                'address': '201 South Figueroa Street 15th Floor',
                'city_state_zip': 'Los Angeles California 90012',
                'phone': '(213) 555-5200',
                'email': 'jsmith@sjkllp.law',
                'date': now().strftime('%B %d, %Y')
            }
        })

        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=payoff_statement_case_{case_id}.pdf'
        return response