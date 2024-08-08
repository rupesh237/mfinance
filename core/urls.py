from django.urls import path
from . import views

app_name = 'core'
urlpatterns = [
    path('getmemberloanaccounts/', views.client_loan_accounts_view, name='getmemberloanaccounts'),
    path('getloandemands/', views.get_loan_demands_view, name='getloandemands'),
    path('getmemberfixeddepositaccounts/', views.get_fixed_deposit_accounts_view, name='getmemberfixeddepositaccounts'),
    path('getmemberrecurringdepositaccounts/', views.get_recurring_deposit_accounts_view, name='getmemberrecurringdepositaccounts'),
    path('receiptsdeposit/', views.receipts_deposit, name='receiptsdeposit'),
    path('payslip/', views.payslip_create_view, name='payslip'),
    path('loanaccounts/group/', views.get_group_loan_accounts, name='get_group_loan_accounts'),
    path('loanaccounts/member/', views.get_member_loan_accounts, name='get_member_loan_accounts'),
    path('getmemberdepositaccounts/', views.client_deposit_accounts_view, name='getmemberdepositaccounts'),
    path('getmemberfixeddepositpaidaccounts/', views.get_fixed_deposit_paid_accounts_view, name='getmemberfixeddepositpaidaccounts'),
    path('getmemberrecurringdepositpaidaccounts/', views.get_recurring_deposit_paid_accounts_view, name='getmemberrecurringdepositpaidaccounts'),
]
