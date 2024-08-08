from django.contrib import admin
from . models import *
# Register your models here.
admin.site.register(Branch)
# admin.site.register(UserManager)
admin.site.register(User)
admin.site.register(Client)
admin.site.register(Group)
admin.site.register(Center)
admin.site.register(GroupMeeting)
admin.site.register(SavingsAccount)
admin.site.register(GroupClient)
admin.site.register(LoanRepaymentEvery)
admin.site.register(LoanAccount)
admin.site.register(GroupMemberLoanAccount)
admin.site.register(FixedDeposits)
admin.site.register(RecurringDeposits)
admin.site.register(Receipts)
admin.site.register(Payments)
