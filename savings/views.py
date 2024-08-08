from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from micro_admin.models import Group, Client, SavingsAccount, Receipts, Payments
from micro_admin.forms import SavingsAccountForm
from django.db.models import Sum
from core.utils import unique_random_number
import decimal
import datetime

d = decimal.Decimal


# Client Savings
@login_required
def client_savings_application_view(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if SavingsAccount.objects.filter(client=client).exists():
        return HttpResponseRedirect(reverse("savings:clientsavingsaccount", kwargs={'client_id': client.id}))
    
    form = SavingsAccountForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj_sav_acc = form.save(commit=False)
        obj_sav_acc.status = "Applied"
        obj_sav_acc.created_by = request.user
        obj_sav_acc.client = client
        obj_sav_acc.save()
        return HttpResponseRedirect(reverse("savings:clientsavingsaccount", kwargs={'client_id': client.id}))
    elif request.method == 'POST':
        return JsonResponse({"error": True, "errors": form.errors})
    
    account_no = unique_random_number(SavingsAccount)
    return render(request, "client/savings/application.html", {'client': client, 'account_no': account_no, 'form': form})


@login_required
def client_savings_account_view(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    account_object = get_object_or_404(SavingsAccount, client=client)
    return render(request, "client/savings/account.html", {'client': client, 'account_object': account_object})


@login_required
def client_savings_deposits_list_view(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    savings_deposit_list = Receipts.objects.filter(client=client).exclude(savingsdeposit_thrift_amount=0)
    savings_account = get_object_or_404(SavingsAccount, client=client)
    return render(request, "client/savings/list_of_savings_deposits.html", {
        'savings_account': savings_account, 'savings_deposit_list': savings_deposit_list})


@login_required
def client_savings_withdrawals_list_view(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    payments_list = Payments.objects.filter(client=client, payment_type="SavingsWithdrawal")
    return render(request, "client/savings/list_of_savings_withdrawals.html", {
        'client': client, 'payments_list': payments_list})


# Group Savings
@login_required
def group_savings_application_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if SavingsAccount.objects.filter(group=group).exists():
        return HttpResponseRedirect(reverse("savings:groupsavingsaccount", kwargs={'group_id': group.id}))
    
    form = SavingsAccountForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj_sav_acc = form.save(commit=False)
        obj_sav_acc.status = "Applied"
        obj_sav_acc.created_by = request.user
        obj_sav_acc.group = group
        obj_sav_acc.save()
        return HttpResponseRedirect(reverse("savings:groupsavingsaccount", kwargs={'group_id': group.id}))
    elif request.method == 'POST':
        return JsonResponse({"error": True, "errors": form.errors})
    
    account_no = unique_random_number(SavingsAccount)
    return render(request, "group/savings/application.html", {'group': group, 'account_no': account_no, 'form': form})


@login_required
def group_savings_account_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    savings_account = get_object_or_404(SavingsAccount, group=group)
    totals = group.clients.aggregate(
        sharecapital_amount=Sum('sharecapital_amount'),
        entrancefee_amount=Sum('entrancefee_amount'),
        membershipfee_amount=Sum('membershipfee_amount'),
        bookfee_amount=Sum('bookfee_amount'),
        insurance_amount=Sum('insurance_amount'),
    )
    return render(request, "group/savings/account.html", {
        'group': group, 'savings_account': savings_account, 'totals': totals})


@login_required
def group_savings_deposits_list_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    savings_account = get_object_or_404(SavingsAccount, group=group)
    receipts_list = Receipts.objects.filter(group=group).exclude(savingsdeposit_thrift_amount=0)
    return render(request, "group/savings/list_of_savings_deposits.html", {
        'group': group, 'savings_account': savings_account, 'receipts_list': receipts_list})


@login_required
def group_savings_withdrawals_list_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    payments_list = Payments.objects.filter(group=group, payment_type="SavingsWithdrawal")
    return render(request, "group/savings/list_of_savings_withdrawals.html", {
        'group': group, 'payments_list': payments_list})


# Change Group/Client Savings account status
@login_required
def change_savings_account_status(request, savingsaccount_id):
    savings_account = get_object_or_404(SavingsAccount, id=savingsaccount_id)
    group = savings_account.group
    client = savings_account.client
    branch_id = group.branch.id if group else client.branch.id if client else None
    
    if not branch_id:
        return JsonResponse({"error": True, "error_message": "Branch ID not Found"})
    
    if request.user.is_admin or (request.user.has_perm("branch_manager") and request.user.branch.id == branch_id):
        status = request.POST.get("status")
        if status in ['Closed', 'Withdrawn', 'Rejected', 'Approved']:
            savings_account.status = status
            savings_account.approved_date = datetime.datetime.now()
            savings_account.save()
            return JsonResponse({"error": False})
        else:
            return JsonResponse({"error": True, "error_message": "Invalid status. Selected status is not in available choices."})
    
    return JsonResponse({"error": True, "error_message": "You don't have permission to change the status."})
