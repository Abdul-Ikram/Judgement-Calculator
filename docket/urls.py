from django.urls import path
from .views import *

urlpatterns = [
    path('add-docket/', AddCaseView.as_view(), name='add_docket'),
    path('cases/', CaseListView.as_view(), name='case_list'),
    path('cases/<int:case_id>/', CaseDetailView.as_view(), name='case-detail'),
    path('transactions/create/', CreateTransactionView.as_view(), name='create_transaction'),
    path('cases/<int:case_id>/transactions/', TransactionListByCaseView.as_view(), name='transactions_by_case'),
    path('transactions/<int:transaction_id>/update/', UpdateTransactionView.as_view(), name='update-transaction'),
    path('cases/<int:case_id>/payoff-statement/', GeneratePayoffPDFView.as_view(), name='generate-payoff-pdf'),
    path('cases/<int:case_id>/delete/', DeleteCaseView.as_view(), name='delete-case'),
    path('transactions/<int:transaction_id>/delete/', DeleteTransactionView.as_view(), name='delete-transaction'),
    path('transactions/<int:case_id>/download/', DownloadCaseTransactionsPDF.as_view(), name='download-transaction'),
]