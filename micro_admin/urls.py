from django.urls import path
from . import views

app_name = 'micro_admin'
urlpatterns = [
    # Index and Authentication
    path('', views.index, name='microadmin_index'),
    path('login/', views.getin, name='login'),
    path('logout/', views.getout, name="logout"),

    # Branch model URLs
    path('branch/create/', views.create_branch_view, name='createbranch'),
    path('branch/edit/<int:pk>/', views.update_branch_view, name='editbranch'),
    path('branch/view/', views.branch_list_view, name='viewbranch'),
    path('branch/delete/<int:pk>/', views.branch_inactive_view, name='deletebranch'),
    path('branch/profile/<int:pk>/', views.branch_profile_view, name='branchprofile'),

    # User model URLs
    path('users/list/', views.users_list_view, name='userslist'),
    path('user/create/', views.create_user_view, name='createuser'),
    path('user/edit/<int:pk>/', views.update_user_view, name='edituser'),
    path('user/profile/<int:pk>/', views.user_profile_view, name='userprofile'),
    path('user/delete/<int:pk>/', views.user_inactive_view, name='deleteuser'),

    # Client model URLs
    path('clients/list/', views.clients_list_view, name='viewclient'),
    path('client/create/', views.create_client_view, name='createclient'),
    path('client/edit/<int:pk>/', views.update_client_view, name='editclient'),
    path('client/delete/<int:pk>/', views.client_inactive_view, name='deleteclient'),
    path('client/profile/<int:pk>/', views.client_profile_view, name='clientprofile'),
    path('client/profile/update/<int:pk>/', views.updateclientprofileview, name='updateclientprofile'),

    # for centers detailed added after adding heading in the nav bar as centers
    path('centers/list/', views.center_list, name="centerslist"),
    path('center/create/', views.create_center, name='createcenter'),

    # Group URLs
    path('group/create/', views.create_group_view, name='creategroup'),
    path('group/<int:group_id>/profile/', views.group_profile_view, name='groupprofile'),
    path('groups/list/', views.groups_list_view, name='groupslist'),
    path('group/<int:group_id>/delete/', views.group_inactive_view, name='deletegroup'),

    # Group - Assign Staff
    path('group/<int:group_id>/assign-staff/', views.group_assign_staff_view, name='assignstaff'),

    # Group Members (add, remove, view)
    path('group/<int:group_id>/members/add/', views.group_add_members_view, name='addmember'),
    path('group/<int:group_id>/members/list/', views.group_members_list_view, name='viewmembers'),
    path('group/<int:group_id>/member/<int:client_id>/remove/', views.group_remove_members_view, name='removemember'),

    # Group Meeting (list, add)
    path('group/<int:group_id>/meetings/list/', views.group_meetings_list_view, name='groupmeetings'),
    path('group/<int:group_id>/meetings/add/', views.group_meetings_add_view, name='addgroupmeeting'),

    # Receipts (create, list)
    path('transactions/', views.transactions, name="transactions"),
    path('deposits/', views.deposits, name="deposits"),
    path('reports/', views.reports, name="reports"),
    path('receiptslist/', views.receipts_list, name="receiptslist"),

    # General Ledger
    path('generalledger/', views.general_ledger, name="generalledger"),

    # Fixed Deposits
    path('fixeddeposits/', views.fixed_deposits_view, name="fixeddeposits"),
    path('clientfixeddepositsprofile/<int:fixed_deposit_id>/', views.client_fixed_deposits_profile, name="clientfixeddepositsprofile"),
    path('viewclientfixeddeposits/', views.view_client_fixed_deposits, name="viewclientfixeddeposits"),
    path('viewparticularclientfixeddeposits/<int:client_id>/', views.view_particular_client_fixed_deposits, name="viewparticularclientfixeddeposits"),

    path('clientrecurringdepositsprofile/<int:recurring_deposit_id>/', views.client_recurring_deposits_profile, name="clientrecurringdepositsprofile"),
    path('viewclientrecurringdeposits/', views.view_client_recurring_deposits, name="viewclientrecurringdeposits"),
    path('viewparticularclientrecurringdeposits/<int:client_id>/', views.view_particular_client_recurring_deposits, name="viewparticularclientrecurringdeposits"),
    path('get-results-list/', views.get_results_list, name='get_results_list'),
    path('day-book/<str:date>/', views.day_book_function, name='day_book_function'),
    path('viewdaybook/', views.day_book_view, name='viewdaybook'),
    path('recurringdeposits/', views.recurring_deposits_view, name="recurringdeposits"),

    # path('payslip/', pay_slip, name="payslip"),
    path('paymentslist/', views.payments_list, name="paymentslist"),
    # path('generalledgerpdfdownload/', GeneralLedgerPdfDownload, name="generalledgerpdfdownload"),
    path('daybookpdfdownload/<str:date>/', views.daybook_pdf_download, name="daybookpdfdownload"),
    path('userchangepassword/', views.user_change_password, name="userchangepassword"),
    path('generalledgerpdfdownload/', views.general_ledger_pdf_download, name="general_ledgerpdf_download"),
]