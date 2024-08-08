from django.urls import path
from . import views

app_name = 'savings'
urlpatterns = [
    # Client Savings
    path('client/<int:client_id>/savings/application/', views.client_savings_application_view, name='clientsavingsapplication'),
    path('client/<int:client_id>/savings/account/view/', views.client_savings_account_view, name='clientsavingsaccount'),
    path('client/<int:client_id>/savings/deposits/list/', views.client_savings_deposits_list_view, name='listofclientsavingsdeposits'),
    path('client/<int:client_id>/savings/withdrawals/list/', views.client_savings_withdrawals_list_view, name='listofclientsavingswithdrawals'),

    # Group Savings
    path('group/<int:group_id>/savings/application/', views.group_savings_application_view, name='groupsavingsapplication'),
    path('group/<int:group_id>/savings/account/view/', views.group_savings_account_view, name='groupsavingsaccount'),
    path('group/<int:group_id>/savings/deposits/list/', views.group_savings_deposits_list_view, name='viewgroupsavingsdeposits'),
    path('group/<int:group_id>/savings/withdrawals/list/', views.group_savings_withdrawals_list_view, name='viewgroupsavingswithdrawals'),

    # Change Savings Account Status
    path('savings/account/<int:savingsaccount_id>/change-status/', views.change_savings_account_status, name='change-savings-account-status'),
]
