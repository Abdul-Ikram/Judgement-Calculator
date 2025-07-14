from django.urls import path
from .views import *

urlpatterns = [
    path('add-docket/', AddCaseView.as_view(), name='add_docket'),
    path('cases/', CaseListView.as_view(), name='case_list'),
    path('transactions/create/', CreateTransactionView.as_view(), name='create_transaction'),
    path('cases/<int:case_id>/transactions/', TransactionListByCaseView.as_view(), name='transactions_by_case'),
    path('transactions/<int:transaction_id>/update/', UpdateTransactionView.as_view(), name='update-transaction'),
    path('cases/<int:case_id>/payoff-statement/', GeneratePayoffPDFView.as_view(), name='generate-payoff-pdf'),
]