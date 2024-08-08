import decimal
from datetime import datetime
from django.conf import settings
from django.template.loader import get_template
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse
from django.db.models import Sum
import os
from weasyprint import HTML, CSS
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.contrib.auth.models import Permission, ContentType
from .models import (
    User, Branch, Center, Group, Client, GroupMeeting, SavingsAccount,
    LoanAccount, Receipts, FixedDeposits, Payments, ClientRoles, UserRoles,
    RecurringDeposits)
from .forms import (
    BranchForm, UserForm, GroupForm, ClientForm, AddMemberForm,
    FixedDepositForm, ChangePasswordForm,RecurringDepositForm,
    GroupMeetingsForm, UpdateClientProfileForm)
from .forms import RecurringDepositForm

d = decimal.Decimal


def index(request):
    if request.user.is_authenticated:
        receipts_list = Receipts.objects.all().order_by("-id")
        payments_list = Payments.objects.all().order_by("-id")
        fixed_deposits_list = FixedDeposits.objects.all().order_by('-id')
        recurring_deposits_list = RecurringDeposits.objects.all().order_by('-id')
        branches_count = Branch.objects.count()
        staff_count = User.objects.count()
        groups_count = Group.objects.count()
        clients_count = Client.objects.count()
        return render(request, "index.html", {
            "user": request.user,
            "receipts": receipts_list,
            "payments": payments_list,
            "fixed_deposits": fixed_deposits_list,
            "groups_count": groups_count,
            "branches_count": branches_count,
            "clients_count": clients_count,
            "staff_count": staff_count,
            "recurring_deposits": recurring_deposits_list
        })
    return render(request, "login.html")


def getin(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active and user.is_staff:
                login(request, user)
                data = {"error": False, "errors": "Logged in successfully"}
            else:
                data = {"error": True, "errors": "User is not active."}
        else:
            data = {"error": True, "errors": "Username and password were incorrect."}
        return JsonResponse(data)
    else:
        if request.user.is_authenticated:
            return render(request, 'index.html', {'user': request.user})
        return render(request, "login.html")


def getout(request):
    logout(request)
    return redirect("micro_admin:login")


def transactions(request):
    return render(request, "transactions.html")


def deposits(request):
    return render(request, "deposits.html")


def reports(request):
    return render(request, "reports.html")


# --------------------------------------------------- #
# Branch Model class Based View #

def create_branch_view(request):
    if request.method == 'POST':
        form = BranchForm(request.POST)
        print(form.is_valid())  # Check if the form is valid
        if form.is_valid():
            branch = form.save()
            return JsonResponse({
                "error": False,
                "success_url": reverse('micro_admin:branchprofile', kwargs={"pk": branch.id})
            })
        else:
            print(form.errors)  # Print form errors for debugging
            return JsonResponse({"error": True, "errors": form.errors})
    else:
        form = BranchForm()

    return render(request, "branch/create.html", {'form': form})

def update_branch_view(request, pk):
    branch = get_object_or_404(Branch, id=pk)
    if not request.user.is_admin:
        return HttpResponseRedirect(reverse("micro_admin:branchlist"))
    
    form = BranchForm(instance=branch)
    if request.method == 'POST':
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            branch = form.save()
            return JsonResponse({
                "error": False,
                "success_url": reverse('micro_admin:branchprofile', kwargs={'pk': branch.id})
            })
        return JsonResponse({"error": True, "errors": form.errors})
    
    return render(request, "branch/edit.html", {'form': form, 'branch': branch})

def branch_profile_view(request, pk):
    branch = get_object_or_404(Branch, id=pk)
    return render(request, "branch/view.html", {'branch': branch})

def branch_list_view(request):
    branch_list = Branch.objects.all()
    return render(request, "branch/list.html", {'branch_list': branch_list})

def branch_inactive_view(request, pk):
    if request.user.is_admin:
        branch = get_object_or_404(Branch, id=pk)
        branch.is_active = not branch.is_active
        branch.save()
    return HttpResponseRedirect(reverse('micro_admin:branchlist'))


# --------------------------------------------------- #


# --------------------------------------------------- #
# Clinet model views
def create_client_view(request):
    branches = Branch.objects.all()
    form = ClientForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        client = form.save(commit=False)
        client.created_by = request.user
        client.save()
        return JsonResponse({
            "error": False,
            "success_url": reverse('micro_admin:clientprofile', kwargs={"pk": client.id})
        })
    return render(request, "client/create.html", {'branches': branches, 'client_roles': ClientRoles.choices, 'form': form})

def client_profile_view(request, pk):
    client = get_object_or_404(Client, id=pk)
    return render(request, "client/profile.html", {'client': client})

def update_client_view(request, pk):
    client_obj = get_object_or_404(Client, id=pk)
    branches = Branch.objects.all()
    form = ClientForm(request.POST or None, user=request.user, client=client_obj, instance=client_obj)
    if request.method == 'POST' and form.is_valid():
        client = form.save()
        return JsonResponse({
            "error": False,
            "success_url": reverse('micro_admin:clientprofile', kwargs={"pk": client.id})
        })
    return render(request, "client/edit.html", {'branches': branches, 'client_roles': ClientRoles, 'client': client_obj, 'form': form})

def updateclientprofileview(request, pk):
    client_obj = get_object_or_404(Client, pk=pk)
    form = UpdateClientProfileForm(request.POST or None, files=request.FILES or None, instance=client_obj)
    
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return JsonResponse({
                "error": False,
                "success_url": reverse('micro_admin:clientprofile', kwargs={"pk": client_obj.id})
            })
        else:
            return JsonResponse({"error": True, "errors": form.errors})

    photo = str(client_obj.photo).split('/')[-1] if client_obj.photo else None
    signature = str(client_obj.signature).split('/')[-1] if client_obj.signature else None

    return render(request, "client/update-profile.html", {
        'form': form,
        'photo': photo,
        'signature': signature
    })



# def update_client_profile_view(request, pk):
#     client_obj = get_object_or_404(Client, pk=pk)
#     form = UpdateClientProfileForm(request.POST or None, files=request.FILES or None)
#     if request.method == 'POST' and form.is_valid():
#         client_obj.photo = request.FILES.get("photo", client_obj.photo)
#         client_obj.signature = request.FILES.get("signature", client_obj.signature)
#         client_obj.save()
#         return JsonResponse({
#             "error": False,
#             "success_url": reverse('micro_admin:clientprofile', kwargs={"pk": client_obj.id})
#         })
#     photo = client_obj.photo.url.split('/')[-1] if client_obj.photo else None
#     signature = client_obj.signature.url.split('/')[-1] if client_obj.signature else None
#     return render(request, "client/update-profile.html", {
#         'form': form, 'photo': photo, 'signature': signature})


def clients_list_view(request):
    client_list = Client.objects.all()
    return render(request, "client/list.html", {'client_list': client_list})

def client_inactive_view(request, pk):
    client = get_object_or_404(Client, id=pk)
    if client.is_active:
        loans = LoanAccount.objects.filter(client=client)
        savings_account = SavingsAccount.objects.filter(client=client).last()
        if (savings_account and savings_account.savings_balance != 0) or \
           (loans and loans.exclude(total_loan_balance=0).exists()):
            raise Http404("Oops! Member is involved in active financial transactions and cannot be deactivated.")
        client.is_active = False
        client.save()
    return HttpResponseRedirect(reverse("micro_admin:clientslist"))

# #################################
# User model
############################
def create_user_view(request):
    branches = Branch.objects.all()
    content_type = ContentType.objects.get_for_model(User)
    permissions = Permission.objects.filter(content_type=content_type, codename="branch_manager")
    form = UserForm(request.POST or None)
    
    if request.method == 'POST':
        print(request.POST['username'])
        print(form.is_valid())
        if form.is_valid():
            user = form.save()
            print(user)
            user_permissions = request.POST.getlist("user_permissions")
        
            if user_permissions:
                user.user_permissions.set(user_permissions)
            
            if request.POST.get("user_roles") == "BranchManager":
                if not user.user_permissions.filter(codename="branch_manager").exists():
                    user.user_permissions.add(Permission.objects.get(codename="branch_manager"))
            
            return JsonResponse({
                "error": False,
                "success_url": reverse('micro_admin:userprofile', kwargs={"pk": user.id})
            })
        else:
            print(form.errors)  # Print form errors for debugging
            return JsonResponse({"error": True, "errors": form.errors})
    
    return render(request, "user/create.html", {
        'form': form, 
        'userroles': UserRoles.choices, 
        'branches': branches, 
        'permissions': permissions
    })


def update_user_view(request, pk):
    branches = Branch.objects.all()
    content_type = ContentType.objects.get_for_model(User)
    permissions = Permission.objects.filter(content_type=content_type, codename="branch_manager")
    selected_user = get_object_or_404(User, id=pk)
    form = UserForm(request.POST or None, instance=selected_user)
    
    if request.method == 'POST' and form.is_valid():
        if not (request.user.is_admin or 
                request.user == selected_user or 
                (request.user.has_perm("branch_manager") and request.user.branch == selected_user.branch)):
            return JsonResponse({
                "error": True,
                "message": "You are not authorized to edit this staff's details.",
                "success_url": reverse('micro_admin:userslist')
            })
        
        user = form.save()
        user_permissions = request.POST.getlist("user_permissions")
        user.user_permissions.set(user_permissions)
        
        if request.POST.get("user_roles") == "BranchManager":
            if not user.user_permissions.filter(codename="branch_manager").exists():
                user.user_permissions.add(Permission.objects.get(codename="branch_manager"))
        
        return JsonResponse({
            "error": False,
            "success_url": reverse('micro_admin:userprofile', kwargs={"pk": user.id})
        })
    
    return render(request, "user/edit.html", {
        'form': form, 
        'userroles': UserRoles, 
        'branches': branches, 
        'permissions': permissions, 
        'selecteduser': selected_user
    })

def user_profile_view(request, pk):
    selected_user = get_object_or_404(User, id=pk)
    return render(request, "user/profile.html", {'selecteduser': selected_user})

def users_list_view(request):
    list_of_users = User.objects.filter(is_admin=False)
    return render(request, "user/list.html", {'list_of_users': list_of_users})

def user_inactive_view(request, pk):
    user = get_object_or_404(User, id=pk)
    
    if request.user.is_admin or (request.user.has_perm("branch_manager") and request.user.branch == user.branch):
        user.is_active = not user.is_active
        user.save()
    
    return HttpResponseRedirect(reverse('micro_admin:userslist'))

#####################################Centers##############################
from .forms import CenterForm
def center_list(request):
    centers =Center.objects.all()
    form = CenterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            center = form.save()
            return JsonResponse({
                "error": False,
                "success_url": reverse('micro_admin:groupprofile', kwargs={"group_id": 1})
            })
        else:
            print(form.errors)  # Print form errors for debugging
            return JsonResponse({"error": True, "errors": form.errors})
    return render(request, "center/list.html", {
        'centers': centers
    })

def create_center(request):
    form = CenterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return JsonResponse({
                'error': False,
                'success_url': reverse('micro_admin:centerslist')
            })
        else:
            print(form.errors)
            return JsonResponse({
                'error': True,
                'errors': form.errors
            })
    return render(request, 'center/create.html',{
        'form':form
    })


####################################################################
# Group
##########################################
def create_group_view(request):
    branches = Branch.objects.all()
    form = GroupForm(request.POST or None)
    
    if request.method == 'POST':
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            return JsonResponse({
                "error": False,
                "success_url": reverse('micro_admin:groupprofile', kwargs={"group_id": group.id})
            })
        else:
            print(form.errors)  # Print form errors for debugging
            return JsonResponse({"error": True, "errors": form.errors})
    
    return render(request, "group/create.html", {'form': form, 'branches': branches})

def group_profile_view(request, group_id):
    group_obj = get_object_or_404(Group, id=group_id)
    clients_list = group_obj.clients.all()
    group_meetings = GroupMeeting.objects.filter(group_id=group_obj.id).order_by('-id')
    clients_count = clients_list.count()
    latest_group_meeting = group_meetings.first() if group_meetings.exists() else None
    
    return render(request, "group/profile.html", {
        'clients_list': clients_list, 
        'clients_count': clients_count, 
        'latest_group_meeting': latest_group_meeting, 
        'group': group_obj
    })

def groups_list_view(request):
    groups_list = Group.objects.all().prefetch_related("clients", "staff", "branch")
    return render(request, "group/list.html", {'groups_list': groups_list})

def group_inactive_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    if request.user.is_admin:
        group.is_active = not group.is_active
        group.save()
    
    return HttpResponseRedirect(reverse('micro_admin:groupslist'))

def group_assign_staff_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    users_list = User.objects.filter(is_admin=False)
    
    if request.method == 'POST':
        staff_id = request.POST.get("staff")
        if staff_id:
            staff = get_object_or_404(User, id=staff_id)
            group.staff.set([staff])
            group.save()
            return JsonResponse({
                "error": False,
                "success_url": reverse('micro_admin:groupprofile', kwargs={"group_id": group.id})
            })
        else:
            return JsonResponse({"error": True, "message": {"staff": "This field is required"}})
    
    return render(request, "group/assign_staff.html", {'users_list': users_list, 'group': group})

def group_add_members_view(request, group_id):
    form = AddMemberForm(request.POST or None)
    clients_list = Client.objects.filter(status="UnAssigned", is_active=True)
    group = get_object_or_404(Group, id=group_id)
    
    if request.method == 'POST' and form.is_valid():
        client_ids = request.POST.getlist("clients")
        for client_id in client_ids:
            client = Client.objects.filter(id=client_id, status="UnAssigned", is_active=True).first()
            if client:
                group.clients.add(client)
                client.status = "Assigned"
                client.save()
        return JsonResponse({
            "error": False,
            "success_url": reverse('micro_admin:groupprofile', kwargs={"group_id": group.id})
        })
    
    return render(request, "group/add_member.html", {'form': form, 'clients_list': clients_list, 'group': group})

def group_members_list_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    clients_list = group.clients.all()
    return render(request, "group/view-members.html", {'group': group, 'clients_list': clients_list})

def group_remove_members_view(request, group_id, client_id):
    group = get_object_or_404(Group, id=group_id)
    client = get_object_or_404(Client, id=client_id)
    
    group_loan_accounts = LoanAccount.objects.filter(group=group, client__isnull=True)
    group_savings_account = SavingsAccount.objects.filter(group=group, client__isnull=True).last()
    client_savings_account = SavingsAccount.objects.filter(client=client).last()

    if group_loan_accounts.exists() or (group_savings_account and client_savings_account):
        if client_savings_account and client_savings_account.savings_balance != 0:
            raise Http404("Oops! Unable to delete this member, Savings Account Not yet Closed.")
        
        if group_loan_accounts.exists():
            if any(loan_account.total_loan_balance != 0 for loan_account in group_loan_accounts):
                raise Http404("Oops! Unable to delete this member, Group Loan Not yet Closed.")
        
        group.clients.remove(client)
        client.status = "UnAssigned"
        client.save()
    
    return HttpResponseRedirect(reverse('micro_admin:groupprofile', kwargs={'group_id': group.id}))

def group_meetings_list_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    group_meetings = GroupMeeting.objects.filter(group=group).order_by('-id')
    return render(request, "group/meetings/list.html", {'group': group, 'group_meetings': group_meetings})


def group_meetings_add_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    if request.method == 'POST':
        form = GroupMeetingsForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.group = group
            meeting.save()
            return JsonResponse({"error": False, "group_id": group.id})
        else:
            return JsonResponse({"error": True, "errors": form.errors})
    
    return render(request, "group/meetings/add.html", {'group': group})

def receipts_list(request):
    receipt_list = Receipts.objects.all().order_by("-id")
    return render(request, "listof_receipts.html", {'receipt_list': receipt_list})

# def general_ledger(request):
#     ledgers_list = Receipts.objects.all().values("date").distinct().order_by("-date").annotate(
#         sum_sharecapital_amount=Sum('sharecapital_amount'),
#         sum_entrancefee_amount=Sum('entrancefee_amount'),
#         sum_membershipfee_amount=Sum('membershipfee_amount'),
#         sum_bookfee_amount=Sum('bookfee_amount'),
#         sum_loanprocessingfee_amount=Sum('loanprocessingfee_amount'),
#         sum_savingsdeposit_thrift_amount=Sum('savingsdeposit_thrift_amount'),
#         sum_fixeddeposit_amount=Sum('fixeddeposit_amount'),
#         sum_recurringdeposit_amount=Sum('recurringdeposit_amount'),
#         sum_loanprinciple_amount=Sum('loanprinciple_amount'),
#         sum_loaninterest_amount=Sum('loaninterest_amount'),
#         sum_insurance_amount=Sum('insurance_amount'),
#         total_sum=Sum('sharecapital_amount') +
#                   Sum('entrancefee_amount') +
#                   Sum('membershipfee_amount') +
#                   Sum('bookfee_amount') +
#                   Sum('loanprocessingfee_amount') +
#                   Sum('savingsdeposit_thrift_amount') +
#                   Sum('fixeddeposit_amount') +
#                   Sum('recurringdeposit_amount') +
#                   Sum('loanprinciple_amount') +
#                   Sum('loaninterest_amount') +
#                   Sum('insurance_amount')
#     )
#     return render(request, "generalledger.html", {'ledgers_list': ledgers_list})

def fixed_deposits_view(request):
    form = FixedDepositForm(request.POST or None, request.FILES or None)
    
    if request.method == 'POST' and form.is_valid():
        fixed_deposit = form.save(commit=False)
        fixed_deposit.status = "Opened"
        fixed_deposit.client = form.cleaned_data['client']
        
        interest_charged = (fixed_deposit.fixed_deposit_amount * 
                            (fixed_deposit.fixed_deposit_interest_rate / 12)) / 100
        fixed_deposit_interest_charged = interest_charged * fixed_deposit.fixed_deposit_period
        fixed_deposit.maturity_amount = (fixed_deposit.fixed_deposit_amount +
                                         fixed_deposit_interest_charged)
        fixed_deposit.fixed_deposit_interest = (
            fixed_deposit.maturity_amount - fixed_deposit.fixed_deposit_amount
        )
        fixed_deposit.save()
        url = reverse('micro_admin:clientfixeddepositsprofile', kwargs={"fixed_deposit_id": fixed_deposit.id})
        return JsonResponse({"error": False, "success_url": url})
    
    return render(request, "client/fixed-deposits/fixed_deposit_application.html", {'form': form})

def client_fixed_deposits_profile(request, fixed_deposit_id):
    fixed_deposit = get_object_or_404(FixedDeposits, id=fixed_deposit_id)
    return render(request, "client/fixed-deposits/fixed_deposits_profile.html", {'fixed_deposit': fixed_deposit})

def view_client_fixed_deposits(request):
    fixed_deposits = FixedDeposits.objects.all()
    return render(request, "client/fixed-deposits/view_fixed_deposits.html", {'fixed_deposits': fixed_deposits})

def view_particular_client_fixed_deposits(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    client_fixed_deposits = FixedDeposits.objects.filter(client=client).order_by("-id")
    return render(request, "client/fixed-deposits/view_fixed_deposits.html", {
        'client': client,
        'client_fixed_deposits': client_fixed_deposits
    })

# 2024-07-21
def client_recurring_deposits_profile(request, recurring_deposit_id):
    recurring_deposit = get_object_or_404(RecurringDeposits, id=recurring_deposit_id)
    return render(request, "client/recurring-deposits/recurring_deposit_profile.html", {
        'recurring_deposit': recurring_deposit
    })

def view_client_recurring_deposits(request):
    recurring_deposit_list = RecurringDeposits.objects.all().order_by("-id")
    return render(request, "client/recurring-deposits/view_recurring_deposits.html", {
        'recurring_deposit_list': recurring_deposit_list
    })

def view_particular_client_recurring_deposits(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    recurring_deposit_list = RecurringDeposits.objects.filter(client=client).order_by("-id")
    return render(request, "client/recurring-deposits/view_recurring_deposits.html", {
        'recurring_deposit_list': recurring_deposit_list
    })

def get_results_list(receipts_list, group_id, thrift_deposit_sum_list, loanprinciple_amount_sum_list,
                     loaninterest_amount_sum_list, entrancefee_amount_sum_list,
                     membershipfee_amount_sum_list, bookfee_amount_sum_list,
                     loanprocessingfee_amount_sum_list, insurance_amount_sum_list,
                     fixed_deposit_sum_list, recurring_deposit_sum_list, share_capital_amount_sum_list):
    
    group = Group.objects.filter(id=group_id).first() if group_id else None

    sums = {
        "thrift_deposit_sum": 0,
        "loanprinciple_amount_sum": 0,
        "loaninterest_amount_sum": 0,
        "entrancefee_amount_sum": 0,
        "membershipfee_amount_sum": 0,
        "bookfee_amount_sum": 0,
        "loanprocessingfee_amount_sum": 0,
        "insurance_amount_sum": 0,
        "fixed_deposit_sum": 0,
        "recurring_deposit_sum": 0,
        "share_capital_amount_sum": 0
    }

    receipt_lists = {
        "thrift_deposit": [],
        "loanprinciple": [],
        "loaninterest": [],
        "entrancefee": [],
        "membershipfee": [],
        "bookfee": [],
        "loanprocessingfee": [],
        "insurance": [],
        "fixed_deposit": [],
        "recurring_deposit": [],
        "share_capital": []
    }

    for receipt in receipts_list:
        for key in sums.keys():
            amount = getattr(receipt, f"{key}_amount")
            if amount and amount > 0:
                if group:
                    receipt_lists[f"{key}"].append(receipt)
                sums[key] += d(amount)

    # Generate results for each category
    def generate_result(key, receipt_list_key):
        return {
            f"{key}_sum": sums[key],
            "group_name": group.name if group else receipt.client.first_name,
            "account_number": group.account_number if group else receipt.client.account_number,
            "receipt_number": receipt_lists[receipt_list_key] if group else receipt.receipt_number,
            "has_list": bool(group)
        }

    share_capital_amount_sum_list.append(generate_result("share_capital_amount", "share_capital"))
    recurring_deposit_sum_list.append(generate_result("recurring_deposit_sum", "recurring_deposit"))
    fixed_deposit_sum_list.append(generate_result("fixed_deposit_sum", "fixed_deposit"))
    thrift_deposit_sum_list.append(generate_result("thrift_deposit_sum", "thrift_deposit"))
    loanprinciple_amount_sum_list.append(generate_result("loanprinciple_amount_sum", "loanprinciple"))
    loaninterest_amount_sum_list.append(generate_result("loaninterest_amount_sum", "loaninterest"))
    entrancefee_amount_sum_list.append(generate_result("entrancefee_amount_sum", "entrancefee"))
    membershipfee_amount_sum_list.append(generate_result("membershipfee_amount_sum", "membershipfee"))
    bookfee_amount_sum_list.append(generate_result("bookfee_amount_sum", "bookfee"))
    loanprocessingfee_amount_sum_list.append(generate_result("loanprocessingfee_amount_sum", "loanprocessingfee"))
    insurance_amount_sum_list.append(generate_result("insurance_amount_sum", "insurance"))

    return (
        thrift_deposit_sum_list, loanprinciple_amount_sum_list, loaninterest_amount_sum_list,
        entrancefee_amount_sum_list, membershipfee_amount_sum_list, bookfee_amount_sum_list,
        loanprocessingfee_amount_sum_list, insurance_amount_sum_list, fixed_deposit_sum_list,
        recurring_deposit_sum_list, share_capital_amount_sum_list
    )


def day_book_function(request, date):
    selected_date = date
    query_set = Receipts.objects.filter(date=selected_date)
    grouped_receipts_list = query_set.values_list('group_id', flat=True).distinct()
    receipts_list = []

    results_lists = {
        'thrift_deposit_sum_list': [],
        'loanprinciple_amount_sum_list': [],
        'loaninterest_amount_sum_list': [],
        'entrancefee_amount_sum_list': [],
        'membershipfee_amount_sum_list': [],
        'bookfee_amount_sum_list': [],
        'loanprocessingfee_amount_sum_list': [],
        'insurance_amount_sum_list': [],
        'fixed_deposit_sum_list': [],
        'recurring_deposit_sum_list': [],
        'share_capital_amount_sum_list': []
    }

    for group_id in grouped_receipts_list:
        if group_id:
            receipts_list = Receipts.objects.filter(group=group_id, date=selected_date)
            results_lists = get_results_list(
                receipts_list, group_id, 
                *[results_lists[key] for key in results_lists.keys()]
            )
        else:
            receipts_list = Receipts.objects.filter(group=None, date=selected_date)
            for receipt in receipts_list:
                results_lists = get_results_list(
                    [receipt], None,
                    *[results_lists[key] for key in results_lists.keys()]
                )

    total_dict = {f"total_{key}": sum([i.get(f"{key}_sum", 0) for i in results_lists[key]]) for key in results_lists}
    total = sum(total_dict.values())

    payments_list = Payments.objects.filter(date=selected_date)
    payment_types = [
        "TravellingAllowance", "Loans", "Paymentofsalary", "PrintingCharges", 
        "StationaryCharges", "OtherCharges", "SavingsWithdrawal", 
        "FixedWithdrawal", "RecurringWithdrawal"
    ]
    dict_payments = {payment_type: list(payments_list.filter(payment_type=payment_type)) for payment_type in payment_types}
    dict_payments_totals = {key: sum([p.total_amount for p in value]) for key, value in dict_payments.items()}

    total_payments = sum(dict_payments_totals.values())

    return {
        'receipts_list': list(receipts_list),
        'total_payments': total_payments,
        'travellingallowance_list': dict_payments.get("TravellingAllowance", []),
        'loans_list': dict_payments.get("Loans", []),
        'paymentofsalary_list': dict_payments.get("Paymentofsalary", []),
        'printingcharges_list': dict_payments.get("PrintingCharges", []),
        'stationarycharges_list': dict_payments.get("StationaryCharges", []),
        'othercharges_list': dict_payments.get("OtherCharges", []),
        'savingswithdrawal_list': dict_payments.get("SavingsWithdrawal", []),
        'fixedwithdrawal_list': dict_payments.get("FixedWithdrawal", []),
        'recurringwithdrawal_list': dict_payments.get("RecurringWithdrawal", []),
        'total': total,
        'dict_payments': dict_payments_totals,
        'total_dict': total_dict,
        'selected_date': selected_date,
        'grouped_receipts_list': list(grouped_receipts_list),
        'thrift_deposit_sum_list': results_lists['thrift_deposit_sum_list'],
        'loanprinciple_amount_sum_list': results_lists['loanprinciple_amount_sum_list'],
        'loaninterest_amount_sum_list': results_lists['loaninterest_amount_sum_list'],
        'entrancefee_amount_sum_list': results_lists['entrancefee_amount_sum_list'],
        'membershipfee_amount_sum_list': results_lists['membershipfee_amount_sum_list'],
        'bookfee_amount_sum_list': results_lists['bookfee_amount_sum_list'],
        'loanprocessingfee_amount_sum_list': results_lists['loanprocessingfee_amount_sum_list'],
        'insurance_amount_sum_list': results_lists['insurance_amount_sum_list'],
        'fixed_deposit_sum_list': results_lists['fixed_deposit_sum_list'],
        'recurring_deposit_sum_list': results_lists['recurring_deposit_sum_list'],
        'share_capital_amount_sum_list': results_lists['share_capital_amount_sum_list']
    }

def day_book_view(request):
    if request.method == 'POST':
        date_str = request.POST.get("date")
        try:
            date = datetime.strptime(date_str, "%m/%d/%Y").date()
        except (ValueError, TypeError):
            return render(request, "day_book.html", {"error_message": "Invalid date format. Use MM/DD/YYYY."})
    else:
        date_str = request.GET.get("date")
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.now().date()
        except (ValueError, TypeError):
            return render(request, "day_book.html", {"error_message": "Invalid date format. Use YYYY-MM-DD."})

    context = day_book_function(request, date)
    context['date_formated'] = date.strftime("%m/%d/%Y")
    return render(request, "day_book.html", context)

def recurring_deposits_view(request):
    if request.method == 'POST':
        form = RecurringDepositForm(request.POST, request.FILES)
        if form.is_valid():
            recurring_deposit = form.save(commit=False)
            recurring_deposit.status = "Opened"
            recurring_deposit.client = form.cleaned_data['client']
            recurring_deposit.save()
            url = reverse('micro_admin:clientrecurringdepositsprofile',
                          kwargs={"recurring_deposit_id": recurring_deposit.id})
            return JsonResponse({"error": False, "success_url": url})
        else:
            return JsonResponse({"error": True, "message": form.errors.as_json()})
    form = RecurringDepositForm()
    return render(request, "client/recurring-deposits/application.html", {'form': form})

def payments_list(request):
    payments_list = Payments.objects.all().order_by("-id")
    return render(request, "list_of_payments.html", {'payments_list': payments_list})


def daybook_pdf_download(request, date):
    # Ensure 'date' is correctly retrieved
    date = request.GET.get("date") or date

    receipts_data = day_book_function(request, date)
    
    try:
        context = {
            'pagesize': 'A4',
            "mediaroot": settings.MEDIA_ROOT,
            "receipts_list": receipts_data['receipts_list'],
            "total_payments": receipts_data['total_payments'],
            "loans_list": receipts_data['loans_list'],
            "selected_date": receipts_data['selected_date'],
            "fixedwithdrawal_list": receipts_data['fixedwithdrawal_list'],
            "total": receipts_data['total'],
            "dict_payments": receipts_data['dict_payments'],
            "dict": receipts_data['total_dict'],
            "travellingallowance_list": receipts_data['travellingallowance_list'],
            "paymentofsalary_list": receipts_data['paymentofsalary_list'],
            "printingcharges_list": receipts_data['printingcharges_list'],
            "stationarycharges_list": receipts_data['stationarycharges_list'],
            "othercharges_list": receipts_data['othercharges_list'],
            "savingswithdrawal_list": receipts_data['savingswithdrawal_list'],
            "recurringwithdrawal_list": receipts_data['recurringwithdrawal_list'],
            "grouped_receipts_list": receipts_data['grouped_receipts_list'],
            "thrift_deposit_sum_list": receipts_data['thrift_deposit_sum_list'],
            "loanprinciple_amount_sum_list": receipts_data['loanprinciple_amount_sum_list'],
            "loaninterest_amount_sum_list": receipts_data['loaninterest_amount_sum_list'],
            "entrancefee_amount_sum_list": receipts_data['entrancefee_amount_sum_list'],
            "membershipfee_amount_sum_list": receipts_data['membershipfee_amount_sum_list'],
            "bookfee_amount_sum_list": receipts_data['bookfee_amount_sum_list'],
            "insurance_amount_sum_list": receipts_data['insurance_amount_sum_list'],
            "share_capital_amount_sum_list": receipts_data['share_capital_amount_sum_list'],
            "recurring_deposit_sum_list": receipts_data['recurring_deposit_sum_list'],
            "fixed_deposit_sum_list": receipts_data['fixed_deposit_sum_list'],
            "loanprocessingfee_amount_sum_list": receipts_data['loanprocessingfee_amount_sum_list']
        }

        html_template = get_template("pdf_daybook.html")
        rendered_html = html_template.render(context).encode(encoding="UTF-8")
        css_files = [
            CSS(os.path.join(settings.STATIC_ROOT, 'css', 'mf.css')),
            CSS(os.path.join(settings.STATIC_ROOT, 'css', 'pdf_stylesheet.css'))
        ]

        pdf_file = HTML(string=rendered_html).write_pdf(stylesheets=css_files)

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="report.pdf"'

        return response

    except Exception as err:
        return HttpResponse(f'Error generating PDF: {err}', status=500)

# def daybook_pdf_download(request, date):
#     date = request.GET.get("date")
#     receipts_list, total_payments, travellingallowance_list, \
#         loans_list, paymentofsalary_list, printingcharges_list, \
#         stationarycharges_list, othercharges_list, savingswithdrawal_list, \
#         recurringwithdrawal_list, fixedwithdrawal_list, total, \
#         dict_payments, total_dict, selected_date, grouped_receipts_list, \
#         thrift_deposit_sum_list, loanprinciple_amount_sum_list, \
#         loaninterest_amount_sum_list, entrancefee_amount_sum_list, \
#         membershipfee_amount_sum_list, bookfee_amount_sum_list, \
#         loanprocessingfee_amount_sum_list, insurance_amount_sum_list, \
#         fixed_deposit_sum_list, recurring_deposit_sum_list, \
#         share_capital_amount_sum_list = day_book_function(request, date)

#     try:
#         context = {
#             'pagesize': 'A4',
#             "mediaroot": settings.MEDIA_ROOT,
#             "receipts_list": receipts_list, "total_payments": total_payments,
#             "loans_list": loans_list, "selected_date": selected_date,
#             "fixedwithdrawal_list": fixedwithdrawal_list, "total": total,
#             "dict_payments": dict_payments, "dict": total_dict,
#             "travellingallowance_list": travellingallowance_list,
#             "paymentofsalary_list": paymentofsalary_list,
#             "printingcharges_list": printingcharges_list,
#             "stationarycharges_list": stationarycharges_list,
#             "othercharges_list": othercharges_list,
#             "savingswithdrawal_list": savingswithdrawal_list,
#             "recurringwithdrawal_list": recurringwithdrawal_list,
#             "grouped_receipts_list": grouped_receipts_list,
#             "thrift_deposit_sum_list": thrift_deposit_sum_list,
#             "loanprinciple_amount_sum_list": loanprinciple_amount_sum_list,
#             "loaninterest_amount_sum_list": loaninterest_amount_sum_list,
#             "entrancefee_amount_sum_list": entrancefee_amount_sum_list,
#             "membershipfee_amount_sum_list": membershipfee_amount_sum_list,
#             "bookfee_amount_sum_list": bookfee_amount_sum_list,
#             "insurance_amount_sum_list": insurance_amount_sum_list,
#             "share_capital_amount_sum_list": share_capital_amount_sum_list,
#             "recurring_deposit_sum_list": recurring_deposit_sum_list,
#             "fixed_deposit_sum_list": fixed_deposit_sum_list,
#             "loanprocessingfee_amount_sum_list": loanprocessingfee_amount_sum_list
#         }

#         html_template = get_template("pdf_daybook.html")
#         rendered_html = html_template.render(context).encode(encoding="UTF-8")
#         css_files = [
#             CSS(os.path.join(settings.STATIC_ROOT, 'css', 'mf.css')),
#             CSS(os.path.join(settings.STATIC_ROOT, 'css', 'pdf_stylesheet.css'))
#         ]

#         pdf_file = HTML(string=rendered_html).write_pdf(stylesheets=css_files)

#         response = HttpResponse(pdf_file, content_type='application/pdf')
#         response['Content-Disposition'] = 'attachment; filename="report.pdf"'

#         return response

#     except Exception as err:
#         return HttpResponse(f'Error generating PDF: {err}', status=500)



def general_ledger_function():
    ledgers_list = Receipts.objects.all().values("date").distinct().order_by("-date").annotate(
        sum_sharecapital_amount=Sum('sharecapital_amount'),
        sum_entrancefee_amount=Sum('entrancefee_amount'),
        sum_membershipfee_amount=Sum('membershipfee_amount'),
        sum_bookfee_amount=Sum('bookfee_amount'),
        sum_loanprocessingfee_amount=Sum('loanprocessingfee_amount'),
        sum_savingsdeposit_thrift_amount=Sum('savingsdeposit_thrift_amount'),
        sum_fixeddeposit_amount=Sum('fixeddeposit_amount'),
        sum_recurringdeposit_amount=Sum('recurringdeposit_amount'),
        sum_loanprinciple_amount=Sum('loanprinciple_amount'),
        sum_loaninterest_amount=Sum('loaninterest_amount'),
        sum_insurance_amount=Sum('insurance_amount'),
        total_sum=Sum('sharecapital_amount') +
                  Sum('entrancefee_amount') +
                  Sum('membershipfee_amount') +
                  Sum('bookfee_amount') +
                  Sum('loanprocessingfee_amount') +
                  Sum('savingsdeposit_thrift_amount') +
                  Sum('fixeddeposit_amount') +
                  Sum('recurringdeposit_amount') +
                  Sum('loanprinciple_amount') +
                  Sum('loaninterest_amount') +
                  Sum('insurance_amount')
    )
    return ledgers_list

def general_ledger(request):
    ledgers_list = general_ledger_function()
    return render(request, "generalledger.html", {'ledgers_list': ledgers_list})

def general_ledger_pdf_download(request):
    general_ledger_list = general_ledger_function()
    try:
        html_template = get_template("pdfgeneral_ledger.html")
        context = {
            'pagesize': 'A4',
            "list": general_ledger_list,
            "mediaroot": settings.MEDIA_ROOT
        }
        rendered_html = html_template.render(context).encode(encoding="UTF-8")
        css_files = [
            CSS(os.path.join(settings.STATIC_ROOT, 'css', 'mf.css')),
            CSS(os.path.join(settings.STATIC_ROOT, 'css', 'pdf_stylesheet.css'))
        ]
        pdf_file = HTML(string=rendered_html).write_pdf(stylesheets=css_files)
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="General_Ledger.pdf"'
        return response
    except Exception as err:
        return HttpResponse(f'Error generating PDF: {err}', status=500)


def user_change_password(request):
    form = ChangePasswordForm()
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            user = request.user
            user.set_password(form.cleaned_data.get("new_password"))
            user.save()
            return JsonResponse({"error": False, "message": "You have changed your password!"})
        else:
            return JsonResponse({"error": True, "errors": form.errors})

    return render(request, "user_change_password.html", {'form': form})



#general_ledger_pdf_download
# def general_ledger_pdf_download(request):

#     def get(self, request, *args, **kwargs):
#         general_ledger_list = general_ledger_function()
#         print (general_ledger_list)
#         try:
#             template = get_template("pdfgeneral_ledger.html")
#             # context = Context(
#             #     {'pagesize': 'A4', "list": general_ledger_list,
#             #      "mediaroot": settings.MEDIA_ROOT})
#             context = dict(
#                 {'pagesize': 'A4', "list": general_ledger_list,
#                  "mediaroot": settings.MEDIA_ROOT})
#             # return render(request, 'pdfgeneral_ledg
#             # # return render(request, 'pdfgeneral_ledger.html', context)
#             # html = template.render(context)
#             # result = StringIO.StringIO()
#             # # pdf = pisa.pisaDocument(StringIO.StringIO(html), dest=result)
#             # if not pdf.err:
#             #     return HttpResponse(result.getvalue(),
#             #                         content_type='application/pdf')
#             # else:
#             #     return HttpResponse('We had some errors')
#             # html = template.render(context)
#             # import pdfkit

#             # pdfkit.from_string(html, 'out.pdf')
#             # pdf = open("out.pdf")
#             # response = HttpResponse(pdf.read(), content_type='application/pdf')
#             # response['Content-Disposition'] = 'attachment; filename=General Ledger.pdf'
#             # pdf.close()
#             # os.remove("out.pdf")
#             # return response
#             html_template = get_template("pdfgeneral_ledger.html")
#             context = dict({
#                'pagesize': 'A4',
#                "list": general_ledger_list,
#                "mediaroot": settings.MEDIA_ROOT
#                })
#             rendered_html = html_template.render(context).encode(encoding="UTF-8")
#             pdf_file = HTML(string=rendered_html).write_pdf(stylesheets=[CSS(settings.COMPRESS_ROOT + '/css/mf.css'), CSS(settings.COMPRESS_ROOT + '/css/pdf_stylesheet.css')])

#             http_response = HttpResponse(pdf_file, content_type='application/pdf')
#             http_response['Content-Disposition'] = 'filename="report.pdf"'

#             return http_response

#         except Exception as err:
#             errmsg = "%s" % (err)
#             return HttpResponse(errmsg)