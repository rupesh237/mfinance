from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.template.response import TemplateResponse
from micro_admin.models import User, Group, Client, LoanAccount, Receipts, Payments, LoanRepaymentEvery, GroupMemberLoanAccount
from micro_admin.forms import LoanAccountForm
from core.utils import send_email_template, unique_random_number
from django.utils.encoding import smart_str
from django.conf import settings
import decimal
import datetime
import csv
import xlwt
from io import BytesIO

d = decimal.Decimal

def client_loan_application(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    form = LoanAccountForm()
    group = Group.objects.filter(clients__id__in=[client_id]).first()
    account_no = unique_random_number(LoanAccount)
    loan_pay = LoanRepaymentEvery.objects.all()

    if request.method == 'POST':
        form = LoanAccountForm(request.POST)
        if form.is_valid():
            loan_account = form.save(commit=False)
            loan_account.status = "Applied"
            loan_account.created_by = request.user
            loan_account.client = client
            interest_charged = d((d(loan_account.loan_amount) * (d(loan_account.annual_interest_rate) / 12)) / 100)
            loan_account.principle_repayment = d(
                int(loan_account.loan_repayment_every) * (d(loan_account.loan_amount) / d(loan_account.loan_repayment_period))
            )
            loan_account.interest_charged = d(int(loan_account.loan_repayment_every) * interest_charged)
            loan_account.loan_repayment_amount = d(loan_account.principle_repayment + loan_account.interest_charged)
            loan_account.total_loan_balance = d(loan_account.loan_amount)
            if group:
                loan_account.group = group
            loan_account.save()

            if client.email:
                send_email_template(
                    subject=f"Your application for the Personal Loan (ID: {loan_account.account_no}) has been Received.",
                    template_name="emails/client/loan_applied.html",
                    recipient=client.email,
                    ctx={
                        "client": client,
                        "loan_account": loan_account,
                        "link_prefix": settings.SITE_URL,
                    },
                )
            return JsonResponse({"error": False, "loanaccount_id": loan_account.id})
        else:
            return JsonResponse({"error": True, "message": form.errors})

    context = {
        'form': form, 
        'client': client, 
        'account_no': account_no,
        'loan_repayment_every': loan_pay
    }
    return render(request, "client/loan/application.html", context)

def client_loan_list(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    loan_accounts = LoanAccount.objects.filter(client=client)
    return render(request, "client/loan/list_of_loan_accounts.html", {
        'client': client, 
        'loan_accounts_list': loan_accounts
    })

def client_loan_account(request, pk):
    loan_account = get_object_or_404(LoanAccount, id=pk)
    loan_disbursements = Payments.objects.filter(loan_account=loan_account)
    no_of_repayments_completed = loan_account.no_of_repayments_completed // loan_account.loan_repayment_every
    context = {
        "loanaccount": loan_account, 
        'loan_disbursements': loan_disbursements,
        "no_of_repayments_completed": no_of_repayments_completed
    }
    return render(request, 'client/loan/account.html', context)

def client_loan_deposit_list(request, client_id, loanaccount_id):
    client = get_object_or_404(Client, id=client_id)
    loanaccount = get_object_or_404(LoanAccount, id=loanaccount_id)
    receipts = Receipts.objects.filter(client=client, member_loan_account=loanaccount).exclude(
        demand_loanprinciple_amount_atinstant=0,
        demand_loaninterest_amount_atinstant=0
    )
    context = {'receipts_lists': receipts, 'loanaccount': loanaccount}
    return render(request, 'client/loan/view_loan_deposits.html', context)

def client_loan_ledger_view(request, client_id, loanaccount_id):
    client = get_object_or_404(Client, id=client_id)
    loanaccount = get_object_or_404(LoanAccount, id=loanaccount_id)
    receipts = Receipts.objects.filter(client=client, member_loan_account=loanaccount).exclude(
        demand_loanprinciple_amount_atinstant=0,
        demand_loaninterest_amount_atinstant=0
    )
    context = {'client': client, 'loanaccount': loanaccount, 'receipts_list': receipts}
    return render(request, 'client/loan/client_ledger_account.html', context)

def client_ledger_csv_download(request, client_id, loanaccount_id):
    client = get_object_or_404(Client, id=client_id)
    loanaccount = get_object_or_404(LoanAccount, id=loanaccount_id)
    receipts = Receipts.objects.filter(
        client=client,
        member_loan_account=loanaccount
    ).exclude(
        demand_loanprinciple_amount_atinstant=0,
        demand_loaninterest_amount_atinstant=0
    )
    try:
        response = HttpResponse(content_type='application/csv')
        response['Content-Disposition'] = f'attachment; filename={client.first_name}_{client.last_name}_ledger.csv'
        writer = csv.writer(response)
        response.write(u'\ufeff'.encode('utf8'))
        writer.writerow([
            "Date", "Receipt No", "Demand Principal", "Demand Interest", 
            "Collection Principal", "Collection Interest", 
            "Balance Principal", "Balance Interest", "Loan Outstanding"
        ])
        for receipt in receipts:
            balance_principle = max(d(receipt.demand_loanprinciple_amount_atinstant) - d(receipt.loanprinciple_amount), 0)
            balance_interest = max(d(receipt.demand_loaninterest_amount_atinstant) - d(receipt.loaninterest_amount), 0)
            writer.writerow([
                receipt.date,
                receipt.receipt_number,
                receipt.demand_loanprinciple_amount_atinstant,
                receipt.demand_loaninterest_amount_atinstant,
                receipt.loanprinciple_amount,
                receipt.loaninterest_amount,
                balance_principle,
                balance_interest,
                receipt.principle_loan_balance_atinstant,
            ])
        return response
    except Exception as err:
        return HttpResponse(f"Error: {err}")

def client_ledger_excel_download(request, client_id, loanaccount_id):
    client = get_object_or_404(Client, id=client_id)
    loanaccount = get_object_or_404(LoanAccount, id=loanaccount_id)
    receipts = Receipts.objects.filter(
        client=client,
        member_loan_account=loanaccount
    ).exclude(
        demand_loanprinciple_amount_atinstant=0,
        demand_loaninterest_amount_atinstant=0
    )
    try:
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename={client.first_name}_{client.last_name}_ledger.xls'
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet("Ledger")
        
        columns = [
            ("Date", 1000),
            ("Receipt Number", 1000),
            ("Demand Principal", 2000),
            ("Demand Interest", 2000),
            ("Collection Principal", 2000),
            ("Collection Interest", 2000),
            ("Balance Principal", 2000),
            ("Balance Interest", 2000),
            ("Loan Outstanding", 2000),
        ]
        
        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        for col_num, (col_title, col_width) in enumerate(columns):
            ws.write(0, col_num, col_title, font_style)
            ws.col(col_num).width = col_width

        font_style = xlwt.XFStyle()
        for row_num, receipt in enumerate(receipts, start=1):
            balance_principle = max(d(receipt.demand_loanprinciple_amount_atinstant) - d(receipt.loanprinciple_amount), 0)
            balance_interest = max(d(receipt.demand_loaninterest_amount_atinstant) - d(receipt.loaninterest_amount), 0)
            ws.write(row_num, 0, str(receipt.date), font_style)
            ws.write(row_num, 1, receipt.receipt_number, font_style)
            ws.write(row_num, 2, receipt.demand_loanprinciple_amount_atinstant, font_style)
            ws.write(row_num, 3, receipt.demand_loaninterest_amount_atinstant, font_style)
            ws.write(row_num, 4, receipt.loanprinciple_amount, font_style)
            ws.write(row_num, 5, receipt.loaninterest_amount, font_style)
            ws.write(row_num, 6, balance_principle, font_style)
            ws.write(row_num, 7, balance_interest, font_style)
            ws.write(row_num, 8, receipt.principle_loan_balance_atinstant, font_style)

        wb.save(response)
        return response
    except Exception as err:
        return HttpResponse(f"Error: {err}")

def client_ledger_pdf_download(request, client_id, loanaccount_id):
    client = get_object_or_404(Client, id=client_id)
    loanaccount = get_object_or_404(LoanAccount, id=loanaccount_id)
    receipts = Receipts.objects.filter(
        client=client,
        member_loan_account=loanaccount
    ).exclude(
        demand_loanprinciple_amount_atinstant=0,
        demand_loaninterest_amount_atinstant=0
    )
    try:
        context = {
            'pagesize': 'A4',
            'receipts_list': receipts,
            'client': client,
        }
        response = TemplateResponse(request, 'pdfledger.html', context)
        return response
    except Exception as err:
        return HttpResponse(f"Error: {err}")


def client_loan_application(request, client_id):
    form = LoanAccountForm()
    client = get_object_or_404(Client, id=client_id)
    group = Group.objects.filter(clients__id=client_id).first()
    account_no = unique_random_number(LoanAccount)
    loan_pay = LoanRepaymentEvery.objects.all()
    if request.method == 'POST':
        form = LoanAccountForm(request.POST)
        if form.is_valid():
            loan_account = form.save(commit=False)
            loan_account.status = "Applied"
            loan_account.created_by = User.objects.get(username=request.user)
            loan_account.client = client
            interest_charged = d(
                (
                    d(loan_account.loan_amount) * (
                        d(loan_account.annual_interest_rate) / 12)
                ) / 100
            )
            loan_account.principle_repayment = d(
                int(loan_account.loan_repayment_every) * (
                    d(loan_account.loan_amount) / d(
                        loan_account.loan_repayment_period)
                )
            )
            loan_account.interest_charged = d(
                int(loan_account.loan_repayment_every) * d(interest_charged))
            loan_account.loan_repayment_amount = d(
                d(loan_account.principle_repayment) + d(
                    loan_account.interest_charged)
            )
            loan_account.total_loan_balance = d(d(loan_account.loan_amount))
            if group:
                loan_account.group = group
            loan_account.save()

            if client.email and client.email.strip():
                send_email_template(
                    subject=f"Your application for the Personal Loan (ID: {loan_account.account_no}) has been Received.",
                    template_name="emails/client/loan_applied.html",
                    recipient=client.email,
                    ctx={
                        "client": client,
                        "loan_account": loan_account,
                        "link_prefix": settings.SITE_URL,
                    },
                )
            return JsonResponse({"error": False, "loanaccount_id": loan_account.id})
        else:
            return JsonResponse({"error": True, "message": form.errors})
    context = {
        'form': form, 'client': client, 'account_no': account_no,
        'loan_repayment_every': loan_pay
    }
    return render(request, "client/loan/application.html", context)


def client_loan_list(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    queryset = LoanAccount.objects.filter(client=client)
    return render(request, "client/loan/list_of_loan_accounts.html", {
        'client': client, 'loan_accounts_list': queryset
    })


def client_loan_account(request, pk):
    loan_account = get_object_or_404(LoanAccount, id=pk)
    loan_disbursements = Payments.objects.filter(loan_account=loan_account)
    no_of_repayments_completed = int((loan_account.no_of_repayments_completed) / (loan_account.loan_repayment_every))
    context = {
        "loanaccount": loan_account, 'loan_disbursements': loan_disbursements,
        "no_of_repayments_completed": no_of_repayments_completed
    }
    return render(request, 'client/loan/account.html', context)


def client_loan_deposit_list(request, client_id, loanaccount_id):
    client = get_object_or_404(Client, id=client_id)
    loanaccount = get_object_or_404(LoanAccount, id=loanaccount_id)
    queryset = Receipts.objects.filter(client=client, member_loan_account=loanaccount).exclude(
        demand_loanprinciple_amount_atinstant=0,
        demand_loaninterest_amount_atinstant=0
    )
    context = {'receipts_lists': queryset, 'loanaccount': loanaccount}
    return render(request, 'client/loan/view_loan_deposits.html', context)


def client_loan_ledger_view(request, client_id, loanaccount_id):
    client = get_object_or_404(Client, id=client_id)
    loanaccount = get_object_or_404(LoanAccount, id=loanaccount_id)
    queryset = Receipts.objects.filter(client=client, member_loan_account=loanaccount).exclude(
        demand_loanprinciple_amount_atinstant=0,
        demand_loaninterest_amount_atinstant=0
    )
    context = {'client': client, 'loanaccount': loanaccount, 'receipts_list': queryset}
    return render(request, 'client/loan/client_ledger_account.html', context)


def client_ledger_csv_download(request, client_id, loanaccount_id):
    client = get_object_or_404(Client, id=client_id)
    loanaccount = get_object_or_404(LoanAccount, id=loanaccount_id)
    receipts_list = Receipts.objects.filter(
        client=client,
        member_loan_account=loanaccount
    ).exclude(
        demand_loanprinciple_amount_atinstant=0,
        demand_loaninterest_amount_atinstant=0
    )
    try:
        response = HttpResponse(content_type='application/x-download')
        response['Content-Disposition'] = f'attachment; filename={client.first_name}{client.last_name}_ledger.csv'
        writer = csv.writer(response, csv.excel)
        response.write(u'\ufeff'.encode('utf8'))
        group = client.group_set.first()
        writer.writerow([
            smart_str(client.id),
            smart_str(client.first_name),
            smart_str(group.name if group else ''),
        ])
        writer.writerow([
            smart_str("Date"),
            smart_str("Receipt No"),
            smart_str("Demand Principal"),
            smart_str("Demand Interest"),
            smart_str("Collection Principal"),
            smart_str("Collection Interest"),
            smart_str("Balance Principal"),
            smart_str("Balance Interest"),
            smart_str("Loan Outstanding"),
        ])
        for receipt in receipts_list:
            balance_principle = max(d(receipt.demand_loanprinciple_amount_atinstant) - d(receipt.loanprinciple_amount), 0)
            balance_interest = max(d(receipt.demand_loaninterest_amount_atinstant) - d(receipt.loaninterest_amount), 0)
            writer.writerow([
                smart_str(receipt.date),
                smart_str(receipt.receipt_number),
                smart_str(receipt.demand_loanprinciple_amount_atinstant),
                smart_str(receipt.demand_loaninterest_amount_atinstant),
                smart_str(receipt.loanprinciple_amount),
                smart_str(receipt.loaninterest_amount),
                smart_str(balance_principle),
                smart_str(balance_interest),
                smart_str(receipt.principle_loan_balance_atinstant),
            ])
        return response
    except Exception as err:
        return HttpResponse(f"Error: {err}")


def client_ledger_excel_download(request, client_id, loanaccount_id):
    client = get_object_or_404(Client, id=client_id)
    loanaccount = get_object_or_404(LoanAccount, id=loanaccount_id)
    receipts_list = Receipts.objects.filter(
        client=client,
        member_loan_account=loanaccount
    ).exclude(
        demand_loanprinciple_amount_atinstant=0,
        demand_loaninterest_amount_atinstant=0
    )
    try:
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename={client.first_name}{client.last_name}_ledger.xls'
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet("Ledger")

        columns = [
            ("Date", 1000),
            ("Receipt Number", 1000),
            ("Demand Principal", 2000),
            ("Demand Interest", 2000),
            ("Collection Principal", 2000),
            ("Collection Interest", 2000),
            ("Balance Principal", 2000),
            ("Balance Interest", 2000),
            ("Loan Outstanding", 2000),
        ]

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        for col_num, (col_name, col_width) in enumerate(columns):
            ws.write(0, col_num, col_name, font_style)
            ws.col(col_num).width = col_width

        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1

        for row_num, receipt in enumerate(receipts_list, start=1):
            balance_principle = max(d(receipt.demand_loanprinciple_amount_atinstant) - d(receipt.loanprinciple_amount), 0)
            balance_interest = max(d(receipt.demand_loaninterest_amount_atinstant) - d(receipt.loaninterest_amount), 0)
            row = [
                str(receipt.date),
                receipt.receipt_number,
                receipt.demand_loanprinciple_amount_atinstant,
                receipt.demand_loaninterest_amount_atinstant,
                receipt.loanprinciple_amount,
                receipt.loaninterest_amount,
                balance_principle,
                balance_interest,
                receipt.principle_loan_balance_atinstant,
            ]
            for col_num, value in enumerate(row):
                ws.write(row_num, col_num, value, font_style)

        wb.save(response)
        return response
    except Exception as err:
        return HttpResponse(f"Error: {err}")


def group_loan_application(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    account_no = unique_random_number(LoanAccount)
    loan_repayment_every = LoanRepaymentEvery.objects.all()
    form = LoanAccountForm()
    if request.method == 'POST':
        form = LoanAccountForm(request.POST)
        if form.is_valid():
            loan_account = form.save(commit=False)
            if group.clients.exists():
                loan_account.status = "Applied"
                loan_account.created_by = User.objects.get(username=request.user)
                loan_account.group = group

                interest_charged = d(
                    (
                        d(loan_account.loan_amount) * (
                            d(loan_account.annual_interest_rate) / 12)
                    ) / 100
                )

                loan_account.principle_repayment = d(
                    int(loan_account.loan_repayment_every) *
                    (
                        d(loan_account.loan_amount) / d(
                            loan_account.loan_repayment_period)
                    )
                )
                loan_account.interest_charged = d(
                    int(loan_account.loan_repayment_every) * d(interest_charged))
                loan_account.loan_repayment_amount = d(
                    d(loan_account.principle_repayment) + d(
                        loan_account.interest_charged)
                )
                loan_account.total_loan_balance = d(d(loan_account.loan_amount))
                loan_account.save()

                loan_amount = (loan_account.loan_amount) / group.clients.count()
                for client in group.clients.all():
                    if client.email and client.email.strip():
                        send_email_template(
                            subject=f"Group Loan (ID: {loan_account.account_no}) application has been Received.",
                            template_name="emails/group/loan_applied.html",
                            recipient=client.email,
                            ctx={
                                "client": client,
                                "loan_account": loan_account,
                                "link_prefix": settings.SITE_URL,
                            },
                        )
                    GroupMemberLoanAccount.objects.create(
                        account_no=loan_account.account_no,
                        client=client, loan_amount=loan_amount,
                        group_loan_account=loan_account, loan_repayment_period=loan_account.loan_repayment_period,
                        loan_repayment_every=loan_account.loan_repayment_every,
                        total_loan_balance=d(loan_amount), status=loan_account.status,
                        annual_interest_rate=loan_account.annual_interest_rate,
                        interest_type=loan_account.interest_type
                    )

                return JsonResponse({"error": False, "loanaccount_id": loan_account.id})
            else:
                return JsonResponse({"error": True, "error_message": "Group does not contain any members."})
        else:
            return JsonResponse({"error": True, "message": form.errors})
    context = {
        'form': form, 'group': group, 'account_no': account_no,
        'loan_repayment_every': loan_repayment_every
    }
    return render(request, 'group/loan/application.html', context)


def group_loan_list(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    queryset = LoanAccount.objects.filter(group=group)
    return render(request, 'group/loan/list_of_loan_accounts.html', {
        'loan_accounts_list': queryset, 'group': group
    })


def group_loan_account(request, loanaccount_id):
    loan_object = get_object_or_404(LoanAccount, id=loanaccount_id)
    group = loan_object.group
    total_loan_amount_repaid = 0
    total_interest_repaid = 0
    loan_disbursements = Payments.objects.filter(loan_account=loan_object)
    group_members = GroupMemberLoanAccount.objects.filter(group_loan_account=loan_object)
    for member in group_members:
        total_loan_amount_repaid += member.total_loan_amount_repaid
        total_interest_repaid += member.total_interest_repaid
    context = {
        'total_loan_amount_repaid': total_loan_amount_repaid,
        'total_interest_repaid': total_interest_repaid,
        'total_loan_paid': total_loan_amount_repaid + total_interest_repaid,
        'group': group,
        'loan_disbursements': loan_disbursements
    }
    return render(request, 'group/loan/account.html', context)


def group_loan_deposits_list(request, loanaccount_id, group_id):
    loan_account = get_object_or_404(LoanAccount, id=loanaccount_id)
    group = get_object_or_404(Group, id=group_id)
    queryset = Receipts.objects.filter(
        group=group,
        group_loan_account=loan_account
    )
    context = {
        'loan_account': loan_account,
        'group': group,
        'receipts_list': queryset
    }
    return render(request, 'group/loan/list_of_loan_deposits.html', context)


def change_loan_account_status(request, pk):
    loan_object = get_object_or_404(LoanAccount, id=pk)
    branch_id = loan_object.group.branch.id if loan_object.group else loan_object.client.branch.id if loan_object.client else None
    if branch_id:
        if (request.user.is_admin or
            (request.user.has_perm("branch_manager") and
             request.user.branch.id == branch_id)):
            status = request.GET.get("status")
            if status in ['Closed', 'Withdrawn', 'Rejected', 'Approved']:
                loan_object.status = status
                loan_object.approved_date = datetime.datetime.now()
                loan_object.save()

                if loan_object.client and loan_object.status == 'Approved':
                    if loan_object.client.email and loan_object.client.email.strip():
                        send_email_template(
                            subject=f"Your application for the Personal Loan (ID: {loan_object.account_no}) has been Approved.",
                            template_name="emails/client/loan_approved.html",
                            recipient=loan_object.client.email,
                            ctx={
                                "client": loan_object.client,
                                "loan_account": loan_object,
                                "link_prefix": settings.SITE_URL,
                            },
                        )

                elif loan_object.group:
                    group_member_loans = GroupMemberLoanAccount.objects.filter(group_loan_account=loan_object)
                    group_member_loans.update(status=loan_object.status)
                    group_member_loans.update(loan_issued_date=loan_object.loan_issued_date)
                    group_member_loans.update(interest_type=loan_object.interest_type)
                    for client in loan_object.group.clients.all():
                        if client.email and client.email.strip():
                            send_email_template(
                                subject=f"Group Loan (ID: {loan_object.account_no}) application has been Approved.",
                                template_name="emails/group/loan_approved.html",
                                recipient=client.email,
                                ctx={
                                    "client": client,
                                    "loan_account": loan_object,
                                    "link_prefix": settings.SITE_URL,
                                },
                            )
                data = {"error": False}
            else:
                data = {"error": True, "error_message": "Status is not in available choices"}
        else:
            data = {"error": True, "error_message": "You don't have permission to change the status."}
    else:
        data = {"error": True, "error_message": "Branch Id not Found"}

    data["success_url"] = reverse('loans:group_loan_account', kwargs={"loanaccount_id": loan_object.id})
    return JsonResponse(data)


def issue_loan(request, loanaccount_id):
    loan_account = get_object_or_404(LoanAccount, id=loanaccount_id)
    if loan_account.group or loan_account.client:
        loan_account.loan_issued_date = datetime.datetime.now()
        loan_account.loan_issued_by = request.user
        loan_account.save()

    if loan_account.group:
        group_members = GroupMemberLoanAccount.objects.filter(group_loan_account=loan_account)
        group_members.update(loan_issued_date=datetime.datetime.now())
        url = reverse("loans:group_loan_account", kwargs={"loanaccount_id": loan_account.id})
    elif loan_account.client:
        url = reverse("loans:client_loan_account", kwargs={'loanaccount_id': loan_account.id})
    else:
        url = "/"
    return HttpResponseRedirect(url)