from celery import shared_task
from micro_admin.models import SavingsAccount
from decimal import Decimal
from django.utils import timezone
import calendar

@shared_task
def calculate_interest_of_savings_account():
    savings_accounts = SavingsAccount.objects.filter(status='Approved')
    current_date = timezone.now().date()  # Use timezone-aware date
    year_days = 366 if calendar.isleap(current_date.year) else 365
    for savings_account in savings_accounts:
        daily_interest_rate_charged = (
            savings_account.savings_balance * savings_account.annual_interest_rate) / (Decimal(year_days) * 100)
        savings_account.savings_balance += daily_interest_rate_charged
        savings_account.save()
