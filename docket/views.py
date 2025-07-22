from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction
from .models import CaseDetails, Transaction
from decimal import Decimal
from django.utils import timezone
from rest_framework.generics import ListAPIView
from .serializers import CaseCreateSerializer, CaseListSerializer, TransactionCreateSerializer, TransactionDetailSerializer, TransactionUpdateSerializer, CaseDetailSerializer
from django.db import transaction as db_transaction
from django.template.loader import render_to_string
from django.http import HttpResponse
# from weasyprint import HTML
from .models import CaseDetails
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import get_template
from datetime import datetime


class AddCaseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CaseCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            data = serializer.validated_data

            if CaseDetails.objects.filter(
                user=user,
                case_name=data['caseName'],
                court_case_number=data['courtCaseNumber'],
                is_active=True
            ).exists():
                return Response({
                    "status_code": 409,
                    "message": "A case with this name and court case number already exists."
                }, status=status.HTTP_409_CONFLICT)

            try:
                with transaction.atomic():

                    case = CaseDetails.objects.create(
                        user=user,
                        case_name=data['caseName'],
                        court_name=data['courtName'],
                        court_case_number=data['courtCaseNumber'],
                        judgment_amount=data['judgmentAmount'],
                        interest_rate=data['interestRate'],
                        judgment_date=data['judgmentDate'],
                        total_payments=data['totalPayments'],
                        accrued_interest=data['accruedInterest'],
                        payoff_amount=data['payoffAmount'],
                        debtor_info=data.get('debtorInfo', ''),
                        last_payment_date=data.get('lastPaymentDate'),
                        is_ended=data.get('isEnded', False)
                    )

                    # Add initial transactions if relevant
                    if data['totalPayments'] > 0:
                        Transaction.objects.create(
                            case=case,
                            transaction_type='PAYMENT',
                            amount=data['totalPayments'],
                            principal_balance=data['principalBalance'],
                            accrued_interest=data['accruedInterest'],
                            date=data.get('lastPaymentDate') or timezone.now()
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
                    # 'message': f'Internal Server Error',
                    'message': f'Error creating case: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'status_code': 400,
            'message': 'Validation failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CaseListView(ListAPIView):
    serializer_class   = CaseListSerializer

    def get_queryset(self):
        # Return only active cases for the authenticated user
        return CaseDetails.objects.filter(
            user=self.request.user,
            is_active=True
        ).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """
        Override the default list() to wrap the serialized data
        in your custom envelope.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            'status_code': 200,
            'message': 'List of Cases.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class CaseDetailView(APIView):
    def get(self, request, case_id):
        case = get_object_or_404(CaseDetails, id=case_id, user=request.user, is_active=True)
        serializer = CaseDetailSerializer(case)

        return Response({
            'status_code': 200,
            'message': 'Case details retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


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
                    # 'message': f"An error occurred: {str(e)}"
                    'message': f'Internal Server Error'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'status_code': 400,
            'message': 'Invalid input',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# class TransactionListByCaseView(ListAPIView):
#     serializer_class = TransactionDetailSerializer

#     def get_queryset(self):
#         case_id = self.kwargs.get('case_id')

#         # Ensure user owns this case
#         case = CaseDetails.objects.filter(id=case_id, user=self.request.user, is_active=True).first()
#         if not case:
#             return Transaction.objects.none()

#         return Transaction.objects.filter(
#             case__id=case_id,
#             case__user=self.request.user,
#             is_active=True
#         ).order_by('-date')

#     def list(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#         if not queryset.exists():
#             return Response({
#                 "status_code": 404,
#                 "message": "No transactions found or case not accessible."
#             }, status=status.HTTP_404_NOT_FOUND)

#         serializer = self.get_serializer(queryset, many=True)
#         return Response({
#             "status_code": 200,
#             "message": "Transactions retrieved successfully.",
#             "transactions": serializer.data
#         }, status=status.HTTP_200_OK)

class TransactionListByCaseView(ListAPIView):
    serializer_class = TransactionDetailSerializer

    def get_queryset(self):
        case_id = self.kwargs.get('case_id')

        # Ensure user owns this case
        case = CaseDetails.objects.filter(id=case_id, user=self.request.user, is_active=True).first()
        if not case:
            return Transaction.objects.none()

        return Transaction.objects.filter(
            case__id=case_id,
            case__user=self.request.user,
            is_active=True
        ).order_by('-date')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status_code": 200,
            "message": "Transactions retrieved successfully.",
            "transactions": serializer.data  # could be empty list []
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


# class GeneratePayoffPDFView(APIView):
#     def get(self, request, case_id):
#         try:
#             case = CaseDetails.objects.get(id=case_id, user=request.user)
#         except CaseDetails.DoesNotExist:
#             return HttpResponse("Case not found.", status=404)

#         # Optional: Get date from query parameters
#         date_str = request.GET.get('date')
#         if date_str:
#             try:
#                 end_date = datetime.strptime(date_str, "%Y-%m-%d").date()
#                 print(end_date)
#             except ValueError:
#                 return HttpResponse("Invalid date format. Use YYYY-MM-DD.", status=400)
#         else:
#             end_date = now().date()

#         # Filter only active transactions up to the given date
#         transactions = case.transactions.filter(is_active=True, date__lte=end_date).order_by('date')

#         # Calculate daily interest
#         daily_interest = case.judgment_amount * (case.interest_rate / 100) / Decimal('365')
#         days_since_judgment = (end_date - case.judgment_date).days
#         accrued_interest = Decimal(str(round(daily_interest * days_since_judgment, 2)))

#         # Calculate payoff
#         payoff_amount = case.judgment_amount + accrued_interest - case.total_payments

#         # Render HTML to string
#         html_string = render_to_string('docket/payoff_statement.html', {
#             'case': case,
#             'transactions': transactions,
#             'daily_interest': f"{daily_interest:.2f}",
#             'interest_start_date': end_date,
#             'today': end_date,
#             'payoff_amount': f"{payoff_amount:.2f}",
#             'accrued_interest': f"{accrued_interest:.2f}",
#             'lawyer': {
#                 'name': 'John A. Smith, Esq.',
#                 'firm': 'Smith Jones & Kaplan LLP',
#                 'address': '201 South Figueroa Street 15th Floor',
#                 'city_state_zip': 'Los Angeles California 90012',
#                 'phone': '(213) 555-5200',
#                 'email': 'jsmith@sjkllp.law',
#                 'date': now().strftime('%B %d, %Y')
#             }
#         })

#         # Generate PDF
#         pdf_file = BytesIO()
#         pisa_status = pisa.CreatePDF(src=html_string, dest=pdf_file)

#         if pisa_status.err:
#             return HttpResponse('Failed to generate PDF', status=500)

#         pdf_file.seek(0)
#         response = HttpResponse(pdf_file, content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename=payoff_statement_case_{case_id}.pdf'
#         return response

class GeneratePayoffPDFView(APIView):
    def get(self, request, case_id):
        try:
            case = CaseDetails.objects.get(id=case_id, user=request.user)
        except CaseDetails.DoesNotExist:
            return HttpResponse("Case not found.", status=404)

        # Optional: Get date from query parameters
        date_str = request.GET.get('date')
        if date_str:
            try:
                end_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return HttpResponse("Invalid date format. Use YYYY-MM-DD.", status=400)
        else:
            end_date = now().date()

        # Filter only active transactions up to the given date
        transactions = case.transactions.filter(is_active=True, date__lte=end_date).order_by('date')

        # Calculate daily interest
        daily_interest = case.judgment_amount * (case.interest_rate / 100) / Decimal('365')
        days_since_judgment = (end_date - case.judgment_date).days
        accrued_interest = round(daily_interest * days_since_judgment, 2)

        # Calculate payoff
        payoff_amount = case.judgment_amount + accrued_interest - case.total_payments

        # Build lawyer info from the logged-in user
        user = request.user
        lawyer_info = {
            'name': user.full_name or f"{user.first_name} {user.last_name}",
            'firm': user.company or "Law Firm",
            'address': user.location or "N/A",
            'city_state_zip': f"{user.state or ''}, {user.country or ''} {user.postal_code or ''}".strip(', '),
            'phone': user.phone_number or "N/A",
            'email': user.email,
            'date': now().strftime('%B %d, %Y')
        }

        # Render HTML from template
        html_string = render_to_string('docket/payoff_statement.html', {
            'case': case,
            'debtor_info': case.debtor_info,
            'transactions': transactions,
            'daily_interest': f"{daily_interest:.2f}",
            'interest_start_date': end_date,
            'today': end_date,
            'payoff_amount': f"{payoff_amount:.2f}",
            'accrued_interest': f"{accrued_interest:.2f}",
            'lawyer': lawyer_info,
        })

        # Generate PDF
        pdf_file = BytesIO()
        pisa_status = pisa.CreatePDF(src=html_string, dest=pdf_file)

        if pisa_status.err:
            return HttpResponse('Failed to generate PDF', status=500)

        pdf_file.seek(0)
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=payoff_statement_case_{case_id}.pdf'
        return response


class DeleteCaseView(APIView):
    def delete(self, request, case_id):
        case = get_object_or_404(CaseDetails, id=case_id, user=request.user, is_active=True)

        # Soft delete the case
        case.is_active = False
        case.deleted_at = timezone.now()
        case.deleted_by = request.user.email
        case.save()

        # Delete all related transactions
        # Transaction.objects.filter(case=case).delete()
        Transaction.objects.filter(case=case).update(
            is_active=False,
            deleted_at=timezone.now(),
            deleted_by=request.user.email
        )

        return Response({
            "success": True,
            "message": f"Case '{case.case_name}' and its related transactions have been deleted successfully."
        }, status=status.HTTP_200_OK)


# class DownloadCaseTransactionsPDF(APIView):
#     def get(self, request, case_id):
#         try:
#             case = CaseDetails.objects.get(id=case_id, user=request.user)
#             transactions = case.transactions.filter(is_active=True).order_by('date')
#             # transactions = case.transactions.all().order_by('date')

#             template_path = 'docket/case_transactions.html'
#             context = {
#                 'case': case,
#                 'transactions': transactions
#             }

#             template = get_template(template_path)
#             html = template.render(context)

#             response = HttpResponse(content_type='application/pdf')
#             response['Content-Disposition'] = f'attachment; filename=case_{case_id}_transactions.pdf'

#             pisa_status = pisa.CreatePDF(html, dest=response)

#             if pisa_status.err:
#                 return HttpResponse('We had some errors generating the PDF', status=500)
#             return response

#         except CaseDetails.DoesNotExist:
#             return HttpResponse("Case not found", status=404)

class DownloadCaseTransactionsPDF(APIView):
    def get(self, request, case_id):
        try:
            # Get the case for the authenticated user
            case = CaseDetails.objects.get(id=case_id, user=request.user)

            # Get optional end date from query params (e.g., ?end_date=2025-07-21)
            end_date_str = request.query_params.get('end_date')
            try:
                if end_date_str:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                    transactions = case.transactions.filter(is_active=True, date__lte=end_date).order_by('date')
                else:
                    transactions = case.transactions.filter(is_active=True).order_by('date')
            except ValueError:
                return HttpResponse("Invalid date format. Use YYYY-MM-DD.", status=400)

            # Prepare the template and context
            template_path = 'docket/case_transactions.html'
            context = {
                'case': case,
                'transactions': transactions,
                'today': datetime.now().date()
            }

            # Render HTML and generate PDF
            template = get_template(template_path)
            html = template.render(context)

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename=case_{case_id}_transactions.pdf'

            pisa_status = pisa.CreatePDF(html, dest=response)
            if pisa_status.err:
                return HttpResponse('We had some errors generating the PDF', status=500)

            return response

        except CaseDetails.DoesNotExist:
            return HttpResponse("Case not found", status=404)


class DeleteTransactionView(APIView):
    def delete(self, request, transaction_id):
        transaction = get_object_or_404(Transaction, id=transaction_id)

        # Ensure only the owner of the related case can delete
        if transaction.case.user != request.user:
            return Response({
                "status_code": 403,
                "message": "You are not authorized to delete this transaction."
            }, status=status.HTTP_403_FORBIDDEN)

        # Soft delete the transaction
        transaction.is_active = False
        transaction.save()

        return Response({
            "status_code": 200,
            "message": "Transaction deleted successfully (soft delete)."
        }, status=status.HTTP_200_OK)
