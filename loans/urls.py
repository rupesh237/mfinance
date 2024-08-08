from django.urls import path
from . import views

app_name = 'loans'
urlpatterns = [
    # Client loan application and management
    path('client/<int:client_id>/loan/apply/', views.client_loan_application, name='clientloanapplication'),
    path('client/<int:client_id>/loans/list/', views.client_loan_list, name='clientloanaccountslist'),
    path('client/loan/<int:pk>/view/', views.client_loan_account, name='clientloanaccount'),
    path('client/<int:client_id>/loan/<int:loanaccount_id>/deposits/list/', views.client_loan_deposit_list, name='listofclientloandeposits'),
    path('client/<int:client_id>/loan/<int:loanaccount_id>/ledger/', views.client_loan_ledger_view, name='clientloanledgeraccount'),
    path('client/<int:client_id>/loan/<int:loanaccount_id>/ledger/download/csv/', views.client_ledger_csv_download, name='clientledgercsvdownload'),
    path('client/<int:client_id>/loan/<int:loanaccount_id>/ledger/download/excel/', views.client_ledger_excel_download, name='clientledgerexceldownload'),
    path('client/<int:client_id>/loan/<int:loanaccount_id>/ledger/download/pdf/', views.client_ledger_pdf_download, name='clientledgerpdfdownload'),

    # Group loan application and management
    path('group/<int:group_id>/loan/apply/', views.group_loan_application, name='grouploanapplication'),
    path('group/<int:group_id>/loans/list/', views.group_loan_list, name='grouploanaccountslist'),
    path('group/loan/<int:pk>/view/', views.group_loan_account, name='grouploanaccount'),
    path('group/<int:group_id>/loan/<int:loanaccount_id>/deposits/list/', views.group_loan_deposits_list, name='viewgrouploandeposits'),

    # Loan account status and issuance
    path('loan/<int:pk>/change-status/', views.change_loan_account_status, name='change_loan_account_status'),
    path('loan/<int:loanaccount_id>/issue/', views.issue_loan, name='issueloan'),
]
