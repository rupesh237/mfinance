from django import forms
from .models import (
    Branch, User, Center, Group, Client, SavingsAccount, LoanAccount, FixedDeposits, Receipts, Payments, RecurringDeposits, GroupMeeting,
    ClientBranchTransfer
)
import decimal

d = decimal.Decimal

class UpdateClientProfileForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['photo', 'signature']

    def __init__(self, *args, **kwargs):
        super(UpdateClientProfileForm, self).__init__(*args, **kwargs)

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = "__all__"
        # ["name", "opening_date", "country", "state", "district",
        #           "city", "area", "phone_number", "pincode"]

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if pincode:
            pincode = str(pincode)
            if not (len(pincode) == 5 and pincode.isdigit()):
                raise forms.ValidationError('Please enter a valid 6-digit pincode')
        return pincode

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            phone_number = str(phone_number)  # Ensure phone_number is a string
            if not (len(phone_number) == 10 and phone_number.isdigit()):
                raise forms.ValidationError('Please enter a valid 10-digit phone number')
        return phone_number

class UserForm(forms.ModelForm):
    date_of_birth = forms.DateField(required=False)
    password = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "gender", "branch",
                  "user_roles", "username", "country", "state",
                  "district", "city", "area", "mobile", "pincode"]

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['gender'].widget.attrs.update({
            'placeholder': 'Gender',
            'class': 'text-box wid-form select-box-pad'
        })
        not_required_fields = ['country', 'state', 'district', 'city', 'area', 'mobile', 'pincode', 'last_name']
        for field in not_required_fields:
            self.fields[field].required = False
        if not self.instance.pk:
            self.fields['password'].required = True

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 5:
            raise forms.ValidationError('Password must be at least 5 characters long!')
        return password

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if pincode:
            pincode = str(pincode)
            if not (len(pincode) == 5 and pincode.isdigit()):
                raise forms.ValidationError('Please enter a valid 5-digit pincode')
        return pincode

    def clean_mobile(self):
        phone_number = self.cleaned_data.get('mobile')
        if phone_number:
            phone_number = str(phone_number)
            if not (len(phone_number) == 10 and phone_number.isdigit()):
                raise forms.ValidationError('Please enter a valid 10-digit phone number')
        return phone_number

    def save(self, commit=True, *args, **kwargs):
        instance = super(UserForm, self).save(commit=False, *args, **kwargs)
        if not instance.pk:
            instance.pincode = self.cleaned_data.get('pincode')
            if self.cleaned_data.get('password'):
                instance.set_password(self.cleaned_data.get('password'))
        if commit:
            instance.save()
        return instance
    
class CenterForm(forms.ModelForm):
    class Meta:
        model = Center
        fields = "__all__"

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = "__all__"
        ["name", "code", "center"]

class ClientForm(forms.ModelForm):
    created_by = forms.CharField(max_length=100, required=False)

    class Meta:
        model = Client
        fields = [
            "first_name", "last_name", "date_of_birth", "joined_date",
            "account_number", "gender", "client_role", "occupation",
            "annual_income", "country", "state", "district", "city",
            "area", "mobile", "pincode", "branch", 'blood_group',
            'email'
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.client = kwargs.pop('client', None)
        super(ClientForm, self).__init__(*args, **kwargs)
        not_required = ['blood_group', 'email']
        for field in not_required:
            self.fields[field].required = False

    def clean_mobile(self):
        phone_number = self.cleaned_data.get('mobile')
        if phone_number:
            phone_number= str(phone_number)
            if not (len(phone_number) == 10 and phone_number.isdigit()):
                raise forms.ValidationError('Please enter a valid 10-digit phone number')
        return phone_number

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if pincode:
            pincode = str(pincode)
            if not (len(pincode) == 6 and pincode.isdigit()):
                raise forms.ValidationError('Please enter a valid 6-digit pincode')
        return pincode

    def clean_branch(self):
        branch = self.cleaned_data.get('branch')
        if self.instance.id and self.client:
            if self.client.branch != branch:
                # Check for group loan accounts
                group_account_filter = Group.objects.filter(clients=self.client)
                if group_account_filter.exists():
                    group_account = group_account_filter.first()
                    group_loan_accounts = LoanAccount.objects.filter(group=group_account).exclude(status='Closed').exclude(status='Withdrawn')
                    if group_loan_accounts.exists():
                        loan_account = group_loan_accounts.first()
                        if loan_account.status in ['Applied', 'Approved', 'Rejected']:
                            raise forms.ValidationError(
                                "This client has a Group loan A/C in {} status. Can't be moved to another branch until it is withdrawn/closed.".format(loan_account.status)
                            )
                        raise forms.ValidationError("This client has a Group loan A/C. Can't be moved to another branch until it is withdrawn/closed.")

                # Check for personal loan accounts
                loan_account_filter = LoanAccount.objects.filter(client=self.client).exclude(status='Closed').exclude(status='Withdrawn')
                if loan_account_filter.exists():
                    loan_account = loan_account_filter.first()
                    if loan_account.status in ['Applied', 'Approved', 'Rejected']:
                        raise forms.ValidationError(
                            "This client has a Personal loan A/C in {} status. Can't be moved to another branch until it is withdrawn/closed.".format(loan_account.status)
                        )
                    raise forms.ValidationError("This client has a Personal loan A/C. Can't be moved to another branch until it is withdrawn/closed.")
        return branch

    def save(self, commit=True, *args, **kwargs):
        instance = super(ClientForm, self).save(commit=False, *args, **kwargs)
        if instance.id and self.client:
            if self.client.branch != self.cleaned_data.get('branch'):
                ClientBranchTransfer.objects.create(
                    client=instance, from_branch=self.client.branch,
                    to_branch=self.cleaned_data.get('branch'),
                    changed_by=self.user
                )
        if commit:
            instance.save()
        return instance
    
class AddMemberForm(forms.ModelForm):

    class Meta:
        model = Group
        fields = ["clients"]


class SavingsAccountForm(forms.ModelForm):

    class Meta:
        model = SavingsAccount
        fields = ["account_no", "opening_date", "min_required_balance",
                  "annual_interest_rate"]


class LoanAccountForm(forms.ModelForm):

    class Meta:
        model = LoanAccount
        fields = ["account_no", "interest_type", "loan_amount",
                  "loan_repayment_period", "loan_repayment_every",
                  "annual_interest_rate", "loanpurpose_description"]

    def clean_loan_repayment_period(self):
        loan_repayment_period = self.cleaned_data.get("loan_repayment_period")
        loan_repayment_every = self.cleaned_data.get("loan_repayment_every")
        if loan_repayment_period and loan_repayment_every:
            if int(loan_repayment_period) <= int(loan_repayment_every):
                raise forms.ValidationError(
                    "Loan Repayment Period should be greater than Loan Repayment Every"
                )
        return loan_repayment_period


class ReceiptForm(forms.ModelForm):

    class Meta:
        model = Receipts
        fields = ["date", "branch", "receipt_number"]


class PaymentForm(forms.ModelForm):

    class Meta:
        model = Payments
        fields = ["branch", "voucher_number", "payment_type", "amount", "interest", "total_amount", "totalamount_in_words"]


class FixedDepositForm(forms.ModelForm):

    client_name = forms.CharField(max_length=50, required=True)
    client_account_no = forms.CharField(max_length=50, required=True)

    class Meta:
        model = FixedDeposits
        fields = ["nominee_firstname", "nominee_lastname",
                  "nominee_occupation", "fixed_deposit_number",
                  "deposited_date", "fixed_deposit_amount",
                  "fixed_deposit_period", "fixed_deposit_interest_rate",
                  "relationship_with_nominee", "nominee_photo",
                  "nominee_signature", "nominee_gender",
                  "nominee_date_of_birth"]

    def clean_client_account_no(self):
        client = Client.objects.filter(
            first_name__iexact=self.cleaned_data.get("client_name"),
            account_number=self.cleaned_data.get("client_account_no")
        ).first()
        if not client:
            raise forms.ValidationError("No Member exists with this First Name and Account Number.")
        return self.cleaned_data.get("client_account_no")


class RecurringDepositForm(forms.ModelForm):

    client_name = forms.CharField(max_length=50, required=True)
    client_account_no = forms.CharField(max_length=50, required=True)

    class Meta:
        model = RecurringDeposits
        fields = '__all__'
        # ["nominee_firstname", "nominee_lastname",
        #           "nominee_occupation", "nominee_gender",
        #           "recurring_deposit_number", "deposited_date",
        #           "recurring_deposit_amount", "recurring_deposit_period",
        #           "recurring_deposit_interest_rate",
        #           "relationship_with_nominee",
        #           "nominee_photo", "nominee_signature",
        #           "nominee_date_of_birth"]

    def clean_client_account_no(self):
        client = Client.objects.filter(
            first_name__iexact=self.cleaned_data.get("client_name"),
            account_number=self.cleaned_data.get("client_account_no")
        ).first()
        if not client:
            raise forms.ValidationError("No Member exists with this First Name and Account Number.")
        return self.cleaned_data.get("client_account_no")


class ChangePasswordForm(forms.Form):

    current_password = forms.CharField(max_length=50, required=True)
    new_password = forms.CharField(max_length=50, required=True)
    confirm_new_password = forms.CharField(max_length=50, required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    def clean_current_password(self):
        current = self.cleaned_data.get("current_password")
        if not self.user.check_password(current):
            raise forms.ValidationError("Current Password is Invalid")
        return current

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password")
        if len(password) < 5:
            raise forms.ValidationError("Password must be at least 5 characters")
        return password

    def clean_confirm_new_password(self):
        password = self.cleaned_data.get("new_password")
        confirm = self.cleaned_data.get("confirm_new_password")
        if password != confirm:
            raise forms.ValidationError("Passwords do not match")
        return confirm


class GroupMeetingsForm(forms.ModelForm):

    class Meta:
        model = GroupMeeting
        fields = ["meeting_date", "meeting_time"]




# from django import forms
# from micro_admin.models import (
#     Branch, User, Group, Client, SavingsAccount, LoanAccount, FixedDeposits, Receipts, Payments, RecurringDeposits, GroupMeetings, ClientBranchTransfer
# )

# class UpdateClientProfileForm(forms.ModelForm):
#     class Meta:
#         model = Client
#         fields = ['photo', 'signature']

#     def __init__(self, *args, **kwargs):
#         super(UpdateClientProfileForm, self).__init__(*args, **kwargs)
#         if self.instance.pk:
#             self.fields['photo'].required = False
#             self.fields['signature'].required = False

# class BranchForm(forms.ModelForm):
#     class Meta:
#         model = Branch
#         fields = ["name", "opening_date", "country", "state", "district",
#                   "city", "area", "phone_number", "pincode"]

#     def clean_pincode(self):
#         pincode = self.cleaned_data.get('pincode')
#         if pincode:
#             if not (len(pincode) == 6 and pincode.isdigit()):
#                 raise forms.ValidationError('Please enter a valid 6-digit pincode')
#         return pincode

#     def clean_phone_number(self):
#         phone_number = self.cleaned_data.get('phone_number')
#         if phone_number:
#             if not (len(phone_number) == 10 and phone_number.isdigit()):
#                 raise forms.ValidationError('Please enter a valid 10-digit phone number')
#         return phone_number

# class UserForm(forms.ModelForm):
#     date_of_birth = forms.DateField(
#         required=False,
#         input_formats=['%m/%d/%Y']
#     )
#     password = forms.CharField(max_length=100, required=False)

#     class Meta:
#         model = User
#         fields = ["email", "first_name", "last_name", "gender", "branch",
#                   "user_roles", "username", "country", "state",
#                   "district", "city", "area", "mobile", "pincode"]

#     def __init__(self, *args, **kwargs):
#         super(UserForm, self).__init__(*args, **kwargs)

#         self.fields['gender'].widget.attrs.update({
#             'placeholder': 'Gender',
#             'class': 'text-box wid-form select-box-pad'
#         })

#         not_required_fields = ['country', 'state', 'district', 'city', 'area', 'mobile', 'pincode', 'last_name']
#         for field in not_required_fields:
#             self.fields[field].required = False

#         if not self.instance.pk:
#             self.fields['password'].required = True

#     def clean_password(self):
#         password = self.cleaned_data.get('password')
#         if password and len(password) < 5:
#             raise forms.ValidationError('Password must be at least 5 characters long!')
#         return password

#     def clean_pincode(self):
#         pincode = self.cleaned_data.get('pincode')
#         if pincode:
#             if not (len(pincode) == 6 and pincode.isdigit()):
#                 raise forms.ValidationError('Please enter a valid 6-digit pincode')
#         return pincode

#     def clean_mobile(self):
#         phone_number = self.cleaned_data.get('mobile')
#         if phone_number:
#             if not (len(phone_number) == 10 and phone_number.isdigit()):
#                 raise forms.ValidationError('Please enter a valid 10-digit phone number')
#         return phone_number

#     def save(self, commit=True, *args, **kwargs):
#         instance = super(UserForm, self).save(commit=False, *args, **kwargs)
#         if not instance.pk:
#             instance.pincode = self.cleaned_data.get('pincode')
#             if self.cleaned_data.get('password'):
#                 instance.set_password(self.cleaned_data.get('password'))
#         if commit:
#             instance.save()
#         return instance

# class GroupForm(forms.ModelForm):
#     class Meta:
#         model = Group
#         fields = ["name", "code", "center"]

# class ClientForm(forms.ModelForm):
#     class Meta:
#         model = Client
#         fields = ["first_name", "last_name", "gender", "date_of_birth",
#                   "photo", "signature", "address", "phone_number"]

# class SavingsAccountForm(forms.ModelForm):
#     class Meta:
#         model = SavingsAccount
#         fields = ["client", "opening_date", "savings_balance", "annual_interest_rate"]

# class LoanAccountForm(forms.ModelForm):
#     class Meta:
#         model = LoanAccount
#         fields = ["client", "loan_amount", "loan_repayment_period", "loan_repayment_every",
#                   "loan_repayment_amount", "total_loan_amount_repaid", "interest_charged",
#                   "total_interest_repaid", "total_loan_paid", "total_loan_balance",
#                   "loanprocessingfee_amount", "no_of_repayments_completed", "principle_repayment",
#                   "status", "loan_issued_date", "interest_type", "annual_interest_rate"]

# class FixedDepositsForm(forms.ModelForm):
#     class Meta:
#         model = FixedDeposits
#         fields = ["client", "deposited_date", "status", "fixed_deposit_number",
#                   "fixed_deposit_amount", "fixed_deposit_period", "fixed_deposit_interest_rate",
#                   "nominee_firstname", "nominee_lastname", "nominee_gender",
#                   "relationship_with_nominee", "nominee_date_of_birth",
#                   "nominee_occupation", "nominee_photo", "nominee_signature",
#                   "fixed_deposit_interest", "maturity_amount",
#                   "total_withdrawal_amount_principle", "total_withdrawal_amount_interest"]

# class RecurringDepositsForm(forms.ModelForm):
#     class Meta:
#         model = RecurringDeposits
#         fields = ["client", "deposited_date", "reccuring_deposit_number", "status",
#                   "recurring_deposit_amount", "recurring_deposit_period", "recurring_deposit_interest_rate",
#                   "nominee_firstname", "nominee_lastname", "nominee_gender",
#                   "relationship_with_nominee", "nominee_date_of_birth",
#                   "nominee_occupation", "nominee_photo", "nominee_signature",
#                   "recurring_deposit_interest", "maturity_amount",
#                   "total_withdrawal_amount_principle", "total_withdrawal_amount_interest", "number_of_payments"]

# class ReceiptsForm(forms.ModelForm):
#     class Meta:
#         model = Receipts
#         fields = ["date", "branch", "receipt_number", "client", "group", "member_loan_account",
#                   "group_loan_account", "sharecapital_amount", "entrancefee_amount",
#                   "membershipfee_amount", "bookfee_amount", "loanprocessingfee_amount",
#                   "savingsdeposit_thrift_amount", "fixed_deposit_account", "fixeddeposit_amount",
#                   "recurring_deposit_account", "recurringdeposit_amount",
#                   "loanprinciple_amount", "loaninterest_amount", "insurance_amount",
#                   "staff", "savings_balance_atinstant",
#                   "demand_loanprinciple_amount_atinstant", "demand_loaninterest_amount_atinstant",
#                   "principle_loan_balance_atinstant"]

# class PaymentsForm(forms.ModelForm):
#     class Meta:
#         model = Payments
#         fields = ["date", "branch", "voucher_number", "client", "group", "staff",
#                   "payment_type", "amount", "interest", "total_amount",
#                   "totalamount_in_words", "loan_account", "fixed_deposit_account",
#                   "recurring_deposit_account"]
