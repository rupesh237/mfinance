import decimal
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import calendar
from django.db.models import Q

from .forms import (ReceiptForm,  GetRecurringDepositsPaidForm, ClientDepositsAccountsForm , PaymentForm,GetFixedDepositsPaidForm, ClientLoanAccountsForm, GetLoanDemandsForm,
                    GetFixedDepositsForm, GetRecurringDepositsForm,)
from micro_admin.models import (Branch, Receipts, PaymentTypes, Payments, LoanAccount,
                                Group, Client, FixedDeposits, RecurringDeposits,
                                GroupMemberLoanAccount)
from .utils import send_email_template

d = decimal.Decimal


@login_required
def client_loan_accounts_view(request):
    form = ClientLoanAccountsForm()
    if request.method == 'POST':
        form = ClientLoanAccountsForm(request.POST)
        if form.is_valid():
            if form.client:
                loan_accounts_filter = LoanAccount.objects.filter(
                    client=form.client,
                    status='Approved'
                ).filter(Q(total_loan_balance__gt=0) | Q(interest_charged__gt=0)).exclude(
                    loan_issued_by__isnull=True, loan_issued_date__isnull=True
                )
                
                member_loan_has_payments = [
                    loan.id for loan in loan_accounts_filter if Payments.objects.filter(
                        client=form.client, loan_account=loan
                    ).exists()
                ]

                loan_accounts = loan_accounts_filter.filter(
                    id__in=member_loan_has_payments
                ).values_list("account_no", "loan_amount")

                groups = form.client.group_set.all()
                default_group = groups.first()
                
                if default_group:
                    group_accounts_filter1 = LoanAccount.objects.filter(
                        group=default_group,
                        status='Approved'
                    ).exclude(
                        loan_issued_by__isnull=True, loan_issued_date__isnull=True
                    )

                    group_accounts_filter = GroupMemberLoanAccount.objects.filter(
                        group_loan_account__in=group_accounts_filter1,
                        client=form.client, status="Approved"
                    )
                    
                    group_loan_has_payments = [
                        loan.group_loan_account.id for loan in group_accounts_filter if Payments.objects.filter(
                            group=default_group, loan_account=loan.group_loan_account
                        ).exists()
                    ]
                    
                    group_accounts = group_accounts_filter.filter(
                        group_loan_account__in=group_loan_has_payments
                    ).values_list("account_no", "loan_amount")
                else:
                    group_accounts = []

                fixed_deposit_accounts = FixedDeposits.objects.filter(
                    client=form.client,
                    status='Opened'
                ).values_list("fixed_deposit_number", "fixed_deposit_amount")

                recurring_deposit_accounts = RecurringDeposits.objects.filter(
                    client=form.client,
                    status="Opened"
                ).values_list("reccuring_deposit_number", "recurring_deposit_amount")

                group = {
                    "group_name": default_group.name if default_group else "",
                    "group_account_number": default_group.account_number if default_group else ""
                }

                data = {
                    "error": False,
                    "loan_accounts": list(loan_accounts),
                    "group_accounts": list(group_accounts),
                    "fixed_deposit_accounts": list(fixed_deposit_accounts),
                    "recurring_deposit_accounts": list(recurring_deposit_accounts),
                    "group": group if default_group else False
                }
            else:
                data = {
                    "error": False,
                    "loan_accounts": [],
                    "group_accounts": [],
                    "fixed_deposit_accounts": [],
                    "recurring_deposit_accounts": [],
                    "group": False
                }
        else:
            data = {"error": True, "errors": form.errors}
        return JsonResponse(data)


@login_required
def get_loan_demands_view(request):
    form = GetLoanDemandsForm()
    if request.method == 'POST':
        form = GetLoanDemandsForm(request.POST)
        if form.is_valid():
            data = {
                "error": False,
                "demand_loanprinciple": form.loan_account.principle_repayment or 0,
                "demand_loaninterest": form.loan_account.interest_charged or 0
            }
        else:
            data = {"error": True, "errors": form.errors}
        return JsonResponse(data)


@login_required
def get_fixed_deposit_accounts_view(request):
    form = GetFixedDepositsForm()
    if request.method == 'POST':
        form = GetFixedDepositsForm(request.POST)
        if form.is_valid():
            data = {
                "error": False,
                "fixeddeposit_amount": form.fixed_deposit_account.fixed_deposit_amount or 0
            }
        else:
            data = {"error": True, "errors": form.errors}
        return JsonResponse(data)


@login_required
def get_recurring_deposit_accounts_view(request):
    form = GetRecurringDepositsForm()
    if request.method == 'POST':
        form = GetRecurringDepositsForm(request.POST)
        if form.is_valid():
            data = {
                "error": False,
                "recurringdeposit_amount": form.recurring_deposit_account.recurring_deposit_amount or 0
            }
        else:
            data = {"error": True, "errors": form.errors}
        return JsonResponse(data)


@login_required
def loan_valid(request, loan_account):
    form = ReceiptForm()
    if loan_account.status == "Approved":
        if loan_account.loan_issued_date:
            if any([
                d(loan_account.total_loan_balance),
                d(loan_account.interest_charged),
                d(loan_account.loan_repayment_amount),
                d(loan_account.principle_repayment)
            ]):
                if form.is_valid() and (form.cleaned_data.get("loanprinciple_amount") or form.cleaned_data.get("loaninterest_amount")):
                    # Repayment logic
                    if d(loan_account.total_loan_amount_repaid) == d(loan_account.loan_amount) and d(loan_account.total_loan_balance) == d(0):
                        if form.cleaned_data.get("loaninterest_amount") == loan_account.interest_charged:
                            if form.cleaned_data.get("loanprinciple_amount") == loan_account.principle_repayment:
                                loan_account.loan_repayment_amount = 0
                                loan_account.principle_repayment = 0
                                loan_account.interest_charged = 0
                            elif form.cleaned_data.get("loanprinciple_amount") < loan_account.principle_repayment:
                                balance_principle = loan_account.principle_repayment - form.cleaned_data.get("loanprinciple_amount")
                                loan_account.principle_repayment = balance_principle
                                loan_account.loan_repayment_amount = balance_principle
                                loan_account.interest_charged = 0
                        else:
                            if form.cleaned_data.get("loaninterest_amount") < loan_account.interest_charged:
                                if form.cleaned_data.get("loanprinciple_amount") == loan_account.principle_repayment:
                                    balance_interest = loan_account.interest_charged - form.cleaned_data.get("loaninterest_amount")
                                    loan_account.interest_charged = balance_interest
                                    loan_account.loan_repayment_amount = balance_interest
                                    loan_account.principle_repayment = 0

                    elif d(loan_account.total_loan_amount_repaid) < d(loan_account.loan_amount) and d(loan_account.total_loan_balance):
                        if int(loan_account.no_of_repayments_completed) >= int(loan_account.loan_repayment_period):
                            if form.cleaned_data.get("loaninterest_amount") == loan_account.interest_charged:
                                if loan_account.interest_type == "Flat":
                                    loan_account.interest_charged = (int(loan_account.loan_repayment_every) * (loan_account.loan_amount * (loan_account.annual_interest_rate / 12)) / 100)
                                elif loan_account.interest_type == "Declining":
                                    loan_account.interest_charged = (int(loan_account.loan_repayment_every) * ((loan_account.total_loan_balance * (loan_account.annual_interest_rate / 12)) / 100))
                            elif form.cleaned_data.get("loaninterest_amount") < loan_account.interest_charged:
                                balance_interest = loan_account.interest_charged - form.cleaned_data.get("loaninterest_amount")
                                if loan_account.interest_type == "Flat":
                                    interest_charged = (int(loan_account.loan_repayment_every) * (loan_account.loan_amount * (loan_account.annual_interest_rate / 12)) / 100)
                                elif loan_account.interest_type == "Declining":
                                    interest_charged = (int(loan_account.loan_repayment_every) * (loan_account.total_loan_balance * (loan_account.annual_interest_rate / 12)) / 100)
                                loan_account.interest_charged = balance_interest + interest_charged

                            if form.cleaned_data.get("loanprinciple_amount") == loan_account.principle_repayment:
                                loan_account.principle_repayment = loan_account.total_loan_balance
                                loan_account.loan_repayment_amount = loan_account.total_loan_balance + loan_account.interest_charged
                            elif form.cleaned_data.get("loanprinciple_amount") < loan_account.principle_repayment:
                                principle_repayable = loan_account.loan_amount / loan_account.loan_repayment_period
                                lastmonth_bal = (loan_account.loan_repayment_amount - principle_repayable)
                                loan_account.principle_repayment = lastmonth_bal
                                loan_account.loan_repayment_amount = lastmonth_bal
                                loan_account.interest_charged = (int(loan_account.loan_repayment_every) * (loan_account.loan_amount * (loan_account.annual_interest_rate / 12)) / 100)

                    loan_account.save()
                    return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid loan account"})


@login_required
def save_payment(request):
    form = PaymentForm()
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data.get("amount")
            loan = form.cleaned_data.get("loan_account")
            if amount > 0 and loan and loan.status == 'Approved':
                # Save payment
                payment = Payments(
                    amount=amount,
                    loan_account=loan,
                    payment_type=form.cleaned_data.get("payment_type"),
                    payment_date=datetime.now(),
                    client=form.cleaned_data.get("client"),
                )
                payment.save()

                # Update loan account status
                loan_account = LoanAccount.objects.get(id=loan.id)
                loan_account.total_loan_balance -= amount
                loan_account.save()

                return JsonResponse({"success": True})
            else:
                return JsonResponse({"error": "Invalid amount or loan account"})
        else:
            return JsonResponse({"error": True, "errors": form.errors})

    return JsonResponse({"error": "Invalid request method"})


@login_required
def save_receipt(request):
    form = ReceiptForm()
    if request.method == 'POST':
        form = ReceiptForm(request.POST)
        if form.is_valid():
            receipt = Receipts(
                receipt_number=form.cleaned_data.get("receipt_number"),
                client=form.cleaned_data.get("client"),
                receipt_date=datetime.now(),
                amount=form.cleaned_data.get("amount"),
                payment_type=form.cleaned_data.get("payment_type"),
                remarks=form.cleaned_data.get("remarks"),
            )
            receipt.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"error": True, "errors": form.errors})

    return JsonResponse({"error": "Invalid request method"})


@login_required
def receipts_deposit(request):
    form = ReceiptForm()
    
    if request.method == 'POST':
        form = ReceiptForm(request.POST)
        
        if form.is_valid():
            client = form.client
            client_group = form.client_group

            # Update client amounts
            if form.cleaned_data.get("sharecapital_amount"):
                client.sharecapital_amount += d(form.cleaned_data.get("sharecapital_amount", 0))
            if form.cleaned_data.get("entrancefee_amount"):
                client.entrancefee_amount += d(form.cleaned_data.get("entrancefee_amount", 0))
            if form.cleaned_data.get("membershipfee_amount"):
                client.membershipfee_amount += d(form.cleaned_data.get("membershipfee_amount", 0))
            if form.cleaned_data.get("bookfee_amount"):
                client.bookfee_amount += d(form.cleaned_data.get("bookfee_amount", 0))

            # Handle loan accounts
            loan_account = form.loan_account
            group_loan_account = form.group_loan_account
            var_demand_loanprinciple_amount_atinstant = d(0)
            var_demand_loaninterest_amount_atinstant = d(0)

            if loan_account and loan_account.status == "Approved":
                if form.cleaned_data.get("loan_account_no"):
                    if form.cleaned_data.get("loanprocessingfee_amount"):
                        loan_account.loanprocessingfee_amount += d(form.cleaned_data.get("loanprocessingfee_amount", 0))
                if any([loan_account.total_loan_balance, loan_account.interest_charged, loan_account.loan_repayment_amount, loan_account.principle_repayment]):
                    var_demand_loanprinciple_amount_atinstant = loan_account.principle_repayment
                    var_demand_loaninterest_amount_atinstant = loan_account.interest_charged

            if group_loan_account and group_loan_account.status == "Approved":
                if form.cleaned_data.get("group_loan_account_no"):
                    if form.cleaned_data.get("loanprocessingfee_amount"):
                        group_loan_account.loanprocessingfee_amount += d(form.cleaned_data.get("loanprocessingfee_amount", 0))
                if any([group_loan_account.total_loan_balance, group_loan_account.interest_charged, group_loan_account.loan_repayment_amount, group_loan_account.principle_repayment]):
                    var_demand_loanprinciple_amount_atinstant = form.group_member_loan_account.principle_repayment
                    var_demand_loaninterest_amount_atinstant = form.group_member_loan_account.interest_charged

            # Handle savings accounts
            savings_account = form.savings_account
            if savings_account:
                if form.cleaned_data.get("savingsdeposit_thrift_amount"):
                    amount = d(form.cleaned_data.get("savingsdeposit_thrift_amount"))
                    savings_account.savings_balance += amount
                    savings_account.total_deposits += amount

                if form.cleaned_data.get('recurring_deposit_account_no'):
                    recurring_deposit_account = RecurringDeposits.objects.filter(
                        reccuring_deposit_number=form.cleaned_data.get('recurring_deposit_account_no')
                    ).first()
                    if recurring_deposit_account:
                        recurring_amount = d(form.cleaned_data.get('recurringdeposit_amount'))
                        if recurring_amount == d(recurring_deposit_account.recurring_deposit_amount):
                            savings_account.recurringdeposit_amount += recurring_amount
                            recurring_deposit_account.number_of_payments += 1
                            if recurring_deposit_account.number_of_payments >= recurring_deposit_account.recurring_deposit_period:
                                recurring_deposit_account.status = 'Paid'
                            recurring_deposit_account.save()

                if form.cleaned_data.get('fixed_deposit_account_no'):
                    fixed_deposit_account = FixedDeposits.objects.filter(
                        fixed_deposit_number=form.cleaned_data.get('fixed_deposit_account_no')
                    ).first()
                    if fixed_deposit_account:
                        fixed_amount = d(form.cleaned_data.get('fixeddeposit_amount'))
                        if fixed_amount == d(fixed_deposit_account.fixed_deposit_amount):
                            savings_account.fixeddeposit_amount += fixed_amount
                            fixed_deposit_account.status = 'Paid'
                            fixed_deposit_account.save()

            # Handle group savings accounts
            group_savings_account = form.group_savings_account
            if group_savings_account and form.cleaned_data.get("savingsdeposit_thrift_amount"):
                amount = d(form.cleaned_data.get("savingsdeposit_thrift_amount"))
                group_savings_account.savings_balance += amount
                group_savings_account.total_deposits += amount

            # Update insurance amount
            if form.cleaned_data.get("insurance_amount"):
                client.insurance_amount += d(form.cleaned_data.get("insurance_amount", 0))

            # Create and save receipt
            receipt_data = {
                'date': form.cleaned_data.get("date"),
                'branch': Branch.objects.get(id=form.data.get("branch")),
                'receipt_number': form.cleaned_data.get("receipt_number"),
                'client': client,
                'group': client_group,
                'staff': request.user
            }
            
            receipt = Receipts.objects.create(**receipt_data)

            if form.cleaned_data.get("sharecapital_amount"):
                receipt.sharecapital_amount = d(form.cleaned_data.get("sharecapital_amount"))
            if form.cleaned_data.get("entrancefee_amount"):
                receipt.entrancefee_amount = d(form.cleaned_data.get("entrancefee_amount"))
            if form.cleaned_data.get("membershipfee_amount"):
                receipt.membershipfee_amount = d(form.cleaned_data.get("membershipfee_amount"))
            if form.cleaned_data.get("bookfee_amount"):
                receipt.bookfee_amount = d(form.cleaned_data.get("bookfee_amount"))
            if form.cleaned_data.get("loanprocessingfee_amount"):
                receipt.loanprocessingfee_amount = d(form.cleaned_data.get("loanprocessingfee_amount"))
                if form.loan_account:
                    receipt.member_loan_account = loan_account
                if form.group_loan_account:
                    receipt.group_loan_account = group_loan_account
            if form.cleaned_data.get("savingsdeposit_thrift_amount"):
                receipt.savingsdeposit_thrift_amount = d(form.cleaned_data.get("savingsdeposit_thrift_amount"))
                receipt.savings_balance_atinstant = savings_account.savings_balance
            if form.savings_account:
                if form.cleaned_data.get('fixed_deposit_account_no'):
                    if form.cleaned_data.get("fixeddeposit_amount"):
                        receipt.fixed_deposit_account = FixedDeposits.objects.filter(
                            fixed_deposit_number=form.cleaned_data.get('fixed_deposit_account_no')
                        ).first()
                if form.cleaned_data.get("fixeddeposit_amount"):
                    receipt.fixeddeposit_amount = d(form.cleaned_data.get("fixeddeposit_amount"))
                if form.cleaned_data.get("recurringdeposit_amount"):
                    if form.cleaned_data.get('recurring_deposit_account_no'):
                        receipt.recurring_deposit_account = RecurringDeposits.objects.filter(
                            reccuring_deposit_number=form.cleaned_data.get('recurring_deposit_account_no')
                        ).first()
                    receipt.recurringdeposit_amount = d(form.cleaned_data.get("recurringdeposit_amount"))
            if form.cleaned_data.get("insurance_amount"):
                receipt.insurance_amount = d(form.cleaned_data.get("insurance_amount"))
            if form.cleaned_data.get("loanprinciple_amount"):
                receipt.loanprinciple_amount = d(form.cleaned_data.get("loanprinciple_amount"))
                if form.loan_account:
                    receipt.member_loan_account = loan_account
                if form.group_loan_account:
                    receipt.group_loan_account = group_loan_account
            if form.cleaned_data.get("loaninterest_amount"):
                receipt.loaninterest_amount = d(form.cleaned_data.get("loaninterest_amount"))
                if form.loan_account:
                    receipt.member_loan_account = loan_account
                if form.group_loan_account:
                    receipt.group_loan_account = group_loan_account
            if form.loan_account:
                receipt.demand_loanprinciple_amount_atinstant = var_demand_loanprinciple_amount_atinstant
                receipt.demand_loaninterest_amount_atinstant = var_demand_loaninterest_amount_atinstant
                receipt.principle_loan_balance_atinstant = loan_account.total_loan_balance
            if form.group_loan_account:
                receipt.demand_loanprinciple_amount_atinstant = var_demand_loanprinciple_amount_atinstant
                receipt.demand_loaninterest_amount_atinstant = var_demand_loaninterest_amount_atinstant
                receipt.principle_loan_balance_atinstant = group_loan_account.total_loan_balance

            receipt.save()
            client.save()
            if form.loan_account:
                if d(loan_account.total_loan_amount_repaid) == d(loan_account.loan_amount) and d(loan_account.total_loan_balance) == d(0) and d(loan_account.interest_charged) == d(0):
                    loan_account.status = "Closed"
                    loan_account.closed_date = datetime.now().date()
                    if loan_account.client and loan_account.client.email:
                        send_email_template(
                            subject=f"Your application for the Personal Loan (ID: {loan_account.account_no}) has been Closed.",
                            template_name="emails/client/loan_closed.html",
                            receipient=loan_account.client.email,
                            ctx={"client": loan_account.client, "loan_account": loan_account, "link_prefix": settings.SITE_URL}
                        )
                    loan_account.save()
            if form.group_loan_account:
                if d(group_loan_account.total_loan_amount_repaid) == d(group_loan_account.loan_amount) and d(group_loan_account.total_loan_balance) == d(0) and d(group_loan_account.interest_charged) == d(0):
                    group_loan_account.status = "Closed"
                group_loan_account.save()
                group_member_loan_accounts = GroupMemberLoanAccount.objects.filter(group_loan_account=form.group_loan_account)
                if group_member_loan_accounts.count() == group_member_loan_accounts.filter(status="Closed").count():
                    group_loan = LoanAccount.objects.get(id=form.group_loan_account.id)
                    group_loan.status = "Closed"
                    group_loan.interest_charged = 0
                    group_loan.save()
                    for client in group_loan.group.clients.all():
                        if client.email:
                            send_email_template(
                                subject=f"Group Loan (ID: {group_loan.account_no}) application has been Closed.",
                                template_name="emails/group/loan_closed.html",
                                receipient=client.email,
                                ctx={"client": client, "loan_account": group_loan, "link_prefix": settings.SITE_URL}
                            )
            if form.savings_account:
                savings_account.save()
            if form.group_savings_account:
                group_savings_account.save()

            data = {"error": False}
        else:
            data = {"error": True, "message": form.errors}
        
        return JsonResponse(data)
    else:
        branches = Branch.objects.all()
        return render(request, "core/receiptsform.html", {'branches': branches})



@login_required
def payslip_create_view(request):
    form = PaymentForm()
    if request.method == 'POST':
        form = PaymentForm(request.POST, user=request.user)
        if form.is_valid():
            pay_slip = form.save()
            if pay_slip.loan_account:
                loan_account = LoanAccount.objects.get(id=pay_slip.loan_account.id)
                loan_account.loan_issued_date = pay_slip.date
                loan_account.save()
                group_members = GroupMemberLoanAccount.objects.filter(group_loan_account=pay_slip.loan_account)
                if group_members.exists():
                    group_members.update(loan_issued_date=pay_slip.date)
            data = {"error": False, 'pay_slip': pay_slip.id}
        else:
            data = {"error": True, "errors": form.errors}
        return JsonResponse(data)
    else:
        branches = Branch.objects.all()
        return render(request, "core/paymentform.html", {'branches': branches, 'voucher_types': PaymentTypes})

@login_required
def get_group_loan_accounts(request):
    group_name = request.GET.get("group_name")
    group_account_number = request.GET.get('group_account_no')
    loan_accounts_data = []

    if group_name and group_account_number:
        group = Group.objects.filter(name__iexact=group_name, account_number=group_account_number).first()
        if group:
            loan_accounts = LoanAccount.objects.filter(group=group, status='Approved', loan_issued_date__isnull=True)
            loan_accounts_data = loan_accounts.values_list("id", "account_no", "loan_amount")
        else:
            return JsonResponse({"error": True, "data": loan_accounts_data})

    return JsonResponse({"error": False, "data": list(loan_accounts_data)})

@login_required
def get_member_loan_accounts(request):
    client_name = request.GET.get("client_name")
    client_account_number = request.GET.get('client_account_number')
    loan_accounts_data = []

    if client_name and client_account_number:
        client = Client.objects.filter(first_name__iexact=client_name, account_number=client_account_number).first()
        if client:
            loan_accounts = LoanAccount.objects.filter(client=client, status='Approved', loan_issued_date__isnull=True)
            loan_accounts_data = loan_accounts.values_list("id", "account_no", "loan_amount")
        else:
            return JsonResponse({"error": True, "data": loan_accounts_data})

    return JsonResponse({"error": False, "data": list(loan_accounts_data)})

@login_required
def client_deposit_accounts_view(request):
    form = ClientDepositsAccountsForm(request.GET or None)
    if form.is_valid():
        fixed_deposit_accounts = []
        recurring_deposit_accounts = []

        if form.client:
            if form.pay_type == 'FixedWithdrawal':
                fixed_deposit_accounts = FixedDeposits.objects.filter(
                    client=form.client, status='Paid'
                ).values_list("fixed_deposit_number", "fixed_deposit_amount")
            elif form.pay_type == 'RecurringWithdrawal':
                recurring_deposit_accounts = RecurringDeposits.objects.filter(
                    client=form.client
                ).exclude(number_of_payments=0).exclude(status='Closed').values_list(
                    "reccuring_deposit_number", "recurring_deposit_amount")
                
        data = {
            "error": False,
            "fixed_deposit_accounts": list(fixed_deposit_accounts),
            "recurring_deposit_accounts": list(recurring_deposit_accounts)
        }
    else:
        data = {"error": True, "errors": form.errors}
    
    return JsonResponse(data)

@login_required
def get_fixed_deposit_paid_accounts_view(request):
    client_name = request.GET.get('client_name')
    client_account_number = request.GET.get('client_account_number')
    client = Client.objects.filter(
        first_name__iexact=client_name,
        account_number=client_account_number
    ).first()
    form = GetFixedDepositsPaidForm(client=client)

    if form.is_valid():
        fixed_deposit = form.fixed_deposit_account
        current_date = timezone.now().date()
        year_days = 366 if calendar.isleap(current_date.year) else 365
        interest_charged = (fixed_deposit.fixed_deposit_amount * fixed_deposit.fixed_deposit_interest_rate) / (d(year_days) * 100)
        days_to_calculate = (current_date - fixed_deposit.deposited_date).days
        calculated_interest_money_till_date = interest_charged * days_to_calculate
        total_amount = fixed_deposit.fixed_deposit_amount + calculated_interest_money_till_date
        
        data = {
            "error": False,
            "fixeddeposit_amount": fixed_deposit.fixed_deposit_amount or 0,
            "interest_charged": round(calculated_interest_money_till_date, 6),
            'total_amount': round(total_amount, 6)
        }
    else:
        data = {"error": True, "errors": form.errors}
    
    return JsonResponse(data)

@login_required
def get_recurring_deposit_paid_accounts_view(request):
    client_name = request.GET.get('client_name')
    client_account_number = request.GET.get('client_account_number')
    client = Client.objects.filter(
        first_name__iexact=client_name,
        account_number=client_account_number
    ).first()
    form = GetRecurringDepositsPaidForm(client=client)

    if form.is_valid():
        recurring_deposit = form.recurring_deposit_account
        recurring_deposit_amount = d(recurring_deposit.recurring_deposit_amount) * recurring_deposit.number_of_payments
        current_date = timezone.now().date()
        year_days = 366 if calendar.isleap(current_date.year) else 365
        interest_charged = (recurring_deposit_amount * recurring_deposit.recurring_deposit_interest_rate) / (d(year_days) * 100)
        days_to_calculate = (current_date - recurring_deposit.deposited_date).days
        recurring_deposit_interest_charged = interest_charged * days_to_calculate
        total_amount = recurring_deposit_amount + recurring_deposit_interest_charged
        
        data = {
            "error": False,
            "recurringdeposit_amount": recurring_deposit_amount,
            "interest_charged": round(recurring_deposit_interest_charged, 6),
            'total_amount': round(total_amount, 6)
        }
    else:
        data = {"error": True, "errors": form.errors}
    
    return JsonResponse(data)