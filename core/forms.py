from micro_admin.models import (
    User, Client, Receipts, Payments, LoanAccount, Group,
    SavingsAccount, FixedDeposits, RecurringDeposits, GroupMemberLoanAccount
)
from django import forms
from django.core.validators import MinValueValidator
from django.forms.utils import ErrorList
from datetime import datetime
import decimal

d = decimal.Decimal


class ClientLoanAccountsForm(forms.Form):
    # fee
    loanprocessingfee_amount = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    loanprinciple_amount = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    loaninterest_amount = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    # a/c
    name = forms.CharField(max_length=100, required=False)
    account_number = forms.CharField(max_length=100, required=False)

    def clean(self):
        self.client = None
        if not (self.cleaned_data.get("name") and self.cleaned_data.get("account_number")):
            errors = self._errors.setdefault("message1", ErrorList())
            errors.append("Please provide both member first name and account number")
            raise forms.ValidationError(errors)
        
        self.client = Client.objects.filter(
            first_name__iexact=self.cleaned_data.get("name"),
            account_number=self.cleaned_data.get("account_number")
        ).last()
        
        if not self.client:
            errors = self._errors.setdefault("message1", ErrorList())
            errors.append("No Client exists with this First Name and Account number.")
            raise forms.ValidationError(errors)
        
        return self.cleaned_data


class GetLoanDemandsForm(forms.Form):
    loan_account_no = forms.CharField(max_length=100, required=False)
    group_loan_account_no = forms.CharField(max_length=100, required=False)
    name = forms.CharField(max_length=100, required=False)

    def clean(self):
        if not (self.cleaned_data.get("loan_account_no") or self.cleaned_data.get("group_loan_account_no")):
            errors = self._errors.setdefault("message1", ErrorList())
            errors.append("Please provide personal/group loan account number")
            raise forms.ValidationError(errors)
        
        if self.cleaned_data.get("loan_account_no") and self.cleaned_data.get("group_loan_account_no"):
            errors = self._errors.setdefault("message1", ErrorList())
            errors.append("Please choose only one a/c (personal/group)")
            raise forms.ValidationError(errors)
        
        if self.cleaned_data.get("loan_account_no"):
            self.loan_account = LoanAccount.objects.filter(account_no=self.cleaned_data.get("loan_account_no")).last()
        elif self.cleaned_data.get("group_loan_account_no"):
            self.group_loan_account = LoanAccount.objects.filter(account_no=self.cleaned_data.get("group_loan_account_no")).last()
            self.loan_account = GroupMemberLoanAccount.objects.filter(
                client__first_name=self.cleaned_data.get("name"), group_loan_account=self.group_loan_account
            ).last()
        
        if not self.loan_account:
            errors = self._errors.setdefault("message1", ErrorList())
            errors.append("Account not found with given a/c number")
            raise forms.ValidationError(errors)
        
        if self.loan_account.status == "Approved":
            if not (
                self.loan_account.total_loan_balance or
                self.loan_account.interest_charged or
                self.loan_account.loan_repayment_amount or
                self.loan_account.principle_repayment
            ):
                errors = self._errors.setdefault("message1", ErrorList())
                errors.append("Loan has been cleared successfully.")
                raise forms.ValidationError(errors)
        else:
            errors = self._errors.setdefault("message1", ErrorList())
            errors.append("Member Loan is under pending for approval.")
            raise forms.ValidationError(errors)
        
        return self.cleaned_data


class GetFixedDepositsForm(forms.Form):
    fixed_deposit_account_no = forms.CharField(max_length=100, required=False)

    def clean(self):
        if self.cleaned_data.get("fixed_deposit_account_no"):
            self.fixed_deposit_account = FixedDeposits.objects.filter(
                fixed_deposit_number=self.cleaned_data.get("fixed_deposit_account_no")
            ).last()
        
        if not self.fixed_deposit_account:
            errors = self._errors.setdefault("message1", ErrorList())
            errors.append("No Fixed Deposit Accounts found with given a/c number")
            raise forms.ValidationError(errors)
        
        if self.fixed_deposit_account.status == "Paid":
            errors = self.errors.setdefault("message1", ErrorList())
            errors.append("Member Fixed Deposit already paid")
            raise forms.ValidationError(errors)
        elif self.fixed_deposit_account.status == "Closed":
            errors = self._errors.setdefault("message1", ErrorList())
            errors.append("Member Fixed Deposit is Closed.")
            raise forms.ValidationError(errors)
        
        return self.cleaned_data


class GetRecurringDepositsForm(forms.Form):
    recurring_deposit_account_no = forms.CharField(max_length=100, required=False)

    def clean(self):
        if self.cleaned_data.get("recurring_deposit_account_no"):
            self.recurring_deposit_account = RecurringDeposits.objects.filter(
                reccuring_deposit_number=self.cleaned_data.get("recurring_deposit_account_no")
            ).last()
        
        if not self.recurring_deposit_account:
            errors = self._errors.setdefault("message1", ErrorList())
            errors.append("No Recurring Deposit Accounts found with given a/c number")
            raise forms.ValidationError(errors)
        
        if self.recurring_deposit_account.status == "Paid":
            errors = self.errors.setdefault("message1", ErrorList())
            errors.append("Member Recurring Deposit already paid")
            raise forms.ValidationError(errors)
        elif self.recurring_deposit_account.status == "Closed":
            errors = self._errors.setdefault("message1", ErrorList())
            errors.append("Member Recurring Deposit is Closed.")
            raise forms.ValidationError(errors)
        
        return self.cleaned_data


class ReceiptForm(forms.ModelForm):
    date = forms.DateField(input_formats=["%Y-%m-%d"], required=True)
    name = forms.CharField(max_length=100, required=True)
    account_number = forms.CharField(max_length=100, required=True)
    savingsdeposit_thrift_amount = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    fixeddeposit_amount = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    recurringdeposit_amount = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    insurance_amount = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    # group
    group_name = forms.CharField(max_length=100, required=False)
    group_account_number = forms.CharField(max_length=100, required=False)
    # loan
    loan_account_no = forms.CharField(max_length=100, required=False)
    group_loan_account_no = forms.CharField(max_length=100, required=False)
    loanprocessingfee_amount = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    demand_loanprinciple = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    demand_loaninterest = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    loanprinciple_amount = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    loaninterest_amount = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    # fees
    sharecapital_amount = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    bookfee_amount = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    entrancefee_amount = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    membershipfee_amount = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    fixed_deposit_account_no = forms.CharField(max_length=100, required=False)
    recurring_deposit_account_no = forms.CharField(max_length=100, required=False)

    class Meta:
        model = Receipts
        fields = ("date", "branch", "receipt_number")

    def clean_receipt_number(self):
        receipt_number = self.cleaned_data.get("receipt_number")
        is_receipt_number_exist = Receipts.objects.filter(receipt_number=receipt_number).exists()
        if is_receipt_number_exist:
            raise forms.ValidationError("Receipt with this Receipt number already exists.")
        return receipt_number

    def verify_loan(self, loan_account):
        if loan_account.status == "Applied":
            errors = self._errors.setdefault("message1", ErrorList())
            errors.append("Loan is under pending for approval.")
            raise forms.ValidationError(errors)
        elif loan_account.status == "Approved":
            if not loan_account.loan_issued_date:
                errors = self._errors.setdefault("message1", ErrorList())
                errors.append("Loan Payment has not yet done.")
                raise forms.ValidationError(errors)
            else:
                if not (loan_account.total_loan_balance or
                        loan_account.interest_charged or
                        loan_account.loan_repayment_amount or
                        loan_account.principle_repayment):
                    errors = self._errors.setdefault("message1", ErrorList())
                    errors.append("Loan has been cleared successfully.")
                    raise forms.ValidationError(errors)
                else:
                    if not ((self.cleaned_data.get("loanprinciple_amount", 0) or d('0.00')) <= loan_account.total_loan_balance):
                        errors = self._errors.setdefault("message1", ErrorList())
                        errors.append("Amount is greater than loan balance.")
                        raise forms.ValidationError(errors)
                    else:
                        if (self.cleaned_data.get("loaninterest_amount", 0) or d('0.00')) > loan_account.interest_charged:
                            errors = self._errors.setdefault("message1", ErrorList())
                            errors.append("Amount is greater than loan interest.")
                            raise forms.ValidationError(errors)

    def clean(self):
        self.client = None
        self.loan_account = None
        self.group_loan_account = None
        self.fixed_deposit_account = None
        self.recurring_deposit_account = None
        self.savings_account = None

        if self.cleaned_data.get("loan_account_no") or self.cleaned_data.get("group_loan_account_no"):
            if not (self.cleaned_data.get("loan_account_no") or self.cleaned_data.get("group_loan_account_no")):
                errors = self._errors.setdefault("message1", ErrorList())
                errors.append("Please provide either loan a/c no. or group loan a/c no.")
                raise forms.ValidationError(errors)
            elif self.cleaned_data.get("loan_account_no") and self.cleaned_data.get("group_loan_account_no"):
                errors = self._errors.setdefault("message1", ErrorList())
                errors.append("Please provide only one a/c (loan/group)")
                raise forms.ValidationError(errors)

            if self.cleaned_data.get("loan_account_no"):
                self.loan_account = LoanAccount.objects.filter(account_no=self.cleaned_data.get("loan_account_no")).last()
                if not self.loan_account:
                    errors = self._errors.setdefault("message1", ErrorList())
                    errors.append("No Loan account found with given a/c no.")
                    raise forms.ValidationError(errors)
                self.verify_loan(self.loan_account)
            elif self.cleaned_data.get("group_loan_account_no"):
                self.group_loan_account = LoanAccount.objects.filter(account_no=self.cleaned_data.get("group_loan_account_no")).last()
                if not self.group_loan_account:
                    errors = self._errors.setdefault("message1", ErrorList())
                    errors.append("No group Loan account found with given a/c no.")
                    raise forms.ValidationError(errors)
                self.loan_account = GroupMemberLoanAccount.objects.filter(
                    client__first_name=self.cleaned_data.get("name"), group_loan_account=self.group_loan_account
                ).last()
                if not self.loan_account:
                    errors = self._errors.setdefault("message1", ErrorList())
                    errors.append("No group member Loan account found with given member name.")
                    raise forms.ValidationError(errors)
                self.verify_loan(self.loan_account)

        if self.cleaned_data.get("name") and self.cleaned_data.get("account_number"):
            self.client = Client.objects.filter(
                first_name__iexact=self.cleaned_data.get("name"),
                account_number=self.cleaned_data.get("account_number")
            ).last()
            if not self.client:
                errors = self._errors.setdefault("message1", ErrorList())
                errors.append("No Client exists with this First Name and Account number.")
                raise forms.ValidationError(errors)
            
            if self.cleaned_data.get("savingsdeposit_thrift_amount"):
                self.savings_account = SavingsAccount.objects.filter(client=self.client).last()
                if not self.savings_account:
                    errors = self._errors.setdefault("message1", ErrorList())
                    errors.append("No Savings Account for the Client exists.")
                    raise forms.ValidationError(errors)
            
            if self.cleaned_data.get("fixed_deposit_account_no"):
                self.fixed_deposit_account = FixedDeposits.objects.filter(
                    fixed_deposit_number=self.cleaned_data.get("fixed_deposit_account_no"), client=self.client
                ).last()
                if not self.fixed_deposit_account:
                    errors = self._errors.setdefault("message1", ErrorList())
                    errors.append("No Fixed Deposit Accounts found with given a/c number")
                    raise forms.ValidationError(errors)
                if self.fixed_deposit_account.status == "Paid":
                    errors = self._errors.setdefault("message1", ErrorList())
                    errors.append("Member Fixed Deposit already paid")
                    raise forms.ValidationError(errors)
                elif self.fixed_deposit_account.status == "Closed":
                    errors = self._errors.setdefault("message1", ErrorList())
                    errors.append("Member Fixed Deposit is Closed.")
                    raise forms.ValidationError(errors)

            if self.cleaned_data.get("recurring_deposit_account_no"):
                self.recurring_deposit_account = RecurringDeposits.objects.filter(
                    reccuring_deposit_number=self.cleaned_data.get("recurring_deposit_account_no"), client=self.client
                ).last()
                if not self.recurring_deposit_account:
                    errors = self._errors.setdefault("message1", ErrorList())
                    errors.append("No Recurring Deposit Accounts found with given a/c number")
                    raise forms.ValidationError(errors)
                if self.recurring_deposit_account.status == "Paid":
                    errors = self._errors.setdefault("message1", ErrorList())
                    errors.append("Member Recurring Deposit already paid")
                    raise forms.ValidationError(errors)
                elif self.recurring_deposit_account.status == "Closed":
                    errors = self._errors.setdefault("message1", ErrorList())
                    errors.append("Member Recurring Deposit is Closed.")
                    raise forms.ValidationError(errors)

        if self.cleaned_data.get("group_name") and self.cleaned_data.get("group_account_number"):
            self.group = Group.objects.filter(
                name=self.cleaned_data.get("group_name"),
                account_number=self.cleaned_data.get("group_account_number")
            ).last()
            if not self.group:
                errors = self._errors.setdefault("message1", ErrorList())
                errors.append("No Group exists with this name and Account number.")
                raise forms.ValidationError(errors)

        return self.cleaned_data




class PaymentForm(forms.ModelForm):
    date = forms.DateField(input_formats=["%m/%d/%Y"], required=True)
    group_name = forms.CharField(max_length=100, required=False)
    group_account_number = forms.CharField(max_length=100, required=False)
    client_name = forms.CharField(max_length=100, required=False)
    client_account_number = forms.CharField(max_length=100, required=False)
    staff_username = forms.CharField(max_length=100, required=False)
    group_loan_account_no = forms.CharField(max_length=100, required=False)
    member_loan_account_no = forms.CharField(max_length=100, required=False)
    interest = forms.DecimalField(required=False, validators=[MinValueValidator(0)])
    fixed_deposit_account_no = forms.CharField(max_length=100, required=False)
    recurring_deposit_account_no = forms.CharField(max_length=100, required=False)

    class Meta:
        model = Payments
        fields = ["date", "branch", "voucher_number", "payment_type", "amount", "interest", "total_amount", "totalamount_in_words"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_date(self):
        date_str = self.cleaned_data.get("date")
        if date_str:
            datestring_format = datetime.datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
            if self.cleaned_data.get("payment_type") == "Loans":
                loan = None
                if self.cleaned_data.get("member_loan_account_no"):
                    loan = LoanAccount.objects.filter(id=self.cleaned_data.get("member_loan_account_no")).first()
                elif self.cleaned_data.get("group_loan_account_no"):
                    loan = LoanAccount.objects.filter(id=self.cleaned_data.get("group_loan_account_no")).first()
                if loan and str(datestring_format) < str(loan.opening_date):
                    raise forms.ValidationError("Payment date should be greater than Loan Application date")
        return date_str

    def clean_voucher_number(self):
        voucher_number = self.cleaned_data.get("voucher_number")
        if Payments.objects.filter(voucher_number=voucher_number).exists():
            raise forms.ValidationError("Payslip with this Voucher number already exists.")
        return voucher_number

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        total_amount = cleaned_data.get("total_amount")

        if amount == 0 or total_amount == 0:
            raise forms.ValidationError("Voucher can't be generated with amount/total amount zero")

        payment_type = cleaned_data.get("payment_type")
        if payment_type in ["TravellingAllowance", "Paymentofsalary"]:
            if not cleaned_data.get("staff_username"):
                raise forms.ValidationError("Please enter Employee Username")
            staff = User.objects.filter(username__iexact=cleaned_data.get("staff_username")).first()
            if not staff:
                raise forms.ValidationError("Entered Employee Username is incorrect")
            if cleaned_data.get("interest"):
                raise forms.ValidationError("Interest must be empty for TA and Payment of salary Voucher.")
        elif payment_type in ["PrintingCharges", "StationaryCharges", "OtherCharges"]:
            if cleaned_data.get("interest"):
                raise forms.ValidationError("Interest must be empty for Charges Voucher.")
            if cleaned_data.get("total_amount") != cleaned_data.get("amount"):
                raise forms.ValidationError("Entered total amount is not equal to amount.")
        elif payment_type == "SavingsWithdrawal":
            total_amount = d(amount)
            if cleaned_data.get("interest"):
                total_amount += d(cleaned_data.get("interest"))
                if d(total_amount) != d(d(amount) + d(cleaned_data.get("interest"))):
                    raise forms.ValidationError("Entered total amount is incorrect.")
            else:
                if d(total_amount) != d(amount):
                    raise forms.ValidationError("Entered total amount is not equal to amount.")

            if not (cleaned_data.get("client_name") or cleaned_data.get('group_name')):
                raise forms.ValidationError("Please enter the Member First Name or Group Name")
            elif cleaned_data.get("client_name"):
                self.validate_client_withdrawal(cleaned_data, total_amount)

            elif cleaned_data.get("group_name") and not cleaned_data.get('client_name'):
                self.validate_group_withdrawal(cleaned_data, total_amount)

        elif payment_type == 'FixedWithdrawal':
            self.validate_fixed_withdrawal(cleaned_data)

        elif payment_type == 'RecurringWithdrawal':
            self.validate_recurring_withdrawal(cleaned_data)

        elif payment_type == "Loans":
            self.validate_loan_payment(cleaned_data)

        return cleaned_data

    def validate_client_withdrawal(self, cleaned_data, total_amount):
        client_name = cleaned_data.get("client_name")
        client_account_number = cleaned_data.get("client_account_number")

        client = Client.objects.filter(
            first_name__iexact=client_name,
            account_number=client_account_number
        ).first()

        if not client:
            raise forms.ValidationError("Member does not exist with this First Name and Account Number.")

        savings_account = SavingsAccount.objects.filter(client=client).first()
        if not savings_account:
            raise forms.ValidationError("Member does not have a Savings Account to withdraw amount.")

        if d(savings_account.savings_balance) < total_amount:
            raise forms.ValidationError("Member Savings Account does not have sufficient balance.")

    def validate_group_withdrawal(self, cleaned_data, total_amount):
        group_name = cleaned_data.get("group_name")
        group_account_number = cleaned_data.get("group_account_number")

        group = Group.objects.filter(
            name__iexact=group_name,
            account_number=group_account_number
        ).first()

        if not group:
            raise forms.ValidationError("Group does not exist with the given details.")

        group_savings_account = SavingsAccount.objects.filter(group=group).first()
        if not group_savings_account or d(group_savings_account.savings_balance) < total_amount:
            raise forms.ValidationError("Entered amount is higher than the savings amount.")

    def validate_fixed_withdrawal(self, cleaned_data):
        client_name = cleaned_data.get("client_name")
        client_account_number = cleaned_data.get("client_account_number")

        if not client_name:
            raise forms.ValidationError('Please enter the Member First Name')
        if cleaned_data.get("group_name") or cleaned_data.get("group_account_number"):
            raise forms.ValidationError("Don't include group details while processing Fixed Withdrawal.")

        client = Client.objects.filter(
            first_name__iexact=client_name,
            account_number=client_account_number
        ).first()

        if not client:
            raise forms.ValidationError("Member does not exist with this First Name and Account Number.")

        fixed_deposit_account = FixedDeposits.objects.filter(
            client=client,
            fixed_deposit_number=cleaned_data.get("fixed_deposit_account_no")
        ).exclude(status="Closed").first()

        if not fixed_deposit_account:
            raise forms.ValidationError("No Fixed Deposit Accounts found with the given account number.")

    def validate_recurring_withdrawal(self, cleaned_data):
        client_name = cleaned_data.get("client_name")
        client_account_number = cleaned_data.get("client_account_number")

        if not client_name:
            raise forms.ValidationError('Please enter the Member First Name')
        if cleaned_data.get("group_name") or cleaned_data.get("group_account_number"):
            raise forms.ValidationError("Don't include group details while processing Recurring Withdrawal.")

        client = Client.objects.filter(
            first_name__iexact=client_name,
            account_number=client_account_number
        ).first()

        if not client:
            raise forms.ValidationError("Member does not exist with this First Name and Account Number.")

        recurring_deposit_account = RecurringDeposits.objects.filter(
            client=client,
            reccuring_deposit_number=cleaned_data.get("recurring_deposit_account_no")
        ).exclude(status="Closed", number_of_payments=0).first()

        if not recurring_deposit_account:
            raise forms.ValidationError("No Recurring Deposit Accounts found with the given account number.")

    def validate_loan_payment(self, cleaned_data):
        if not (cleaned_data.get("group_name") or cleaned_data.get("client_name")):
            raise forms.ValidationError("Please enter Group Name or Client Name.")
        # Additional validation logic for loans...

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.id:
            # Logic to set the instance fields based on payment type...
            pass  # Implement the necessary logic to save the instance
        if commit:
            instance.save()
        return instance

###########################K################################################
class GetFixedDepositsPaidForm(forms.Form):
    fixed_deposit_account_no = forms.CharField(max_length=100, required=False)

    def __init__(self, *args, **kwargs):
        # Extract 'client' from initial kwargs and remove it from kwargs
        self.client = kwargs.pop('initial', {}).get('client', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        # Call the parent class's clean method
        cleaned_data = super().clean()
        
        # Retrieve the fixed deposit account number from cleaned data
        account_no = cleaned_data.get("fixed_deposit_account_no")
        if account_no:
            self.fixed_deposit_account = FixedDeposits.objects.filter(
                client=self.client,
                fixed_deposit_number=account_no
            ).last()
            
            if not self.fixed_deposit_account:
                self.add_error("fixed_deposit_account_no", "No Fixed Deposit Accounts found with the given account number.")
                raise forms.ValidationError("No Fixed Deposit Accounts found with the given account number.")
            
            if self.fixed_deposit_account.status == "Opened":
                self.add_error("fixed_deposit_account_no", "Member Fixed Deposit is opened.")
                raise forms.ValidationError("Member Fixed Deposit is opened.")
            
            elif self.fixed_deposit_account.status == "Closed":
                self.add_error("fixed_deposit_account_no", "Member Fixed Deposit is closed.")
                raise forms.ValidationError("Member Fixed Deposit is closed.")
        
        return cleaned_data
    
class ClientDepositsAccountsForm(forms.Form):
    payment_type = forms.CharField(max_length=100, required=False)
    client_name = forms.CharField(max_length=100, required=False)
    client_account_number = forms.CharField(max_length=100, required=False)

    def clean(self):
        # Call the parent class's clean method
        cleaned_data = super().clean()
        
        # Extract payment type and client details
        self.pay_type = cleaned_data.get('payment_type')
        client_name = cleaned_data.get('client_name')
        client_account_number = cleaned_data.get('client_account_number')
        
        # Ensure both client name and account number are provided
        if not client_name or not client_account_number:
            self.add_error(None, "Please provide both client name and account number.")
            raise forms.ValidationError("Please provide both client name and account number.")
        
        # Fetch the client based on the provided details
        self.client = Client.objects.filter(
            first_name__iexact=client_name,
            account_number=client_account_number
        ).last()
        
        if not self.client:
            self.add_error(None, "No client exists with the provided name and account number.")
            raise forms.ValidationError("No client exists with the provided name and account number.")
        
        return cleaned_data
    

class GetRecurringDepositsPaidForm(forms.Form):
    recurring_deposit_account_no = forms.CharField(max_length=100, required=False)

    def __init__(self, *args, **kwargs):
        # Initialize client from kwargs if provided
        self.client = kwargs.pop('initial', {}).get('client', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        # Call parent class clean method
        cleaned_data = super().clean()

        # Get the recurring deposit account number from cleaned data
        account_no = cleaned_data.get("recurring_deposit_account_no")
        
        # Check if account number is provided and fetch the recurring deposit
        if account_no:
            self.recurring_deposit_account = RecurringDeposits.objects.filter(
                client=self.client,
                reccuring_deposit_number=account_no
            ).last()
        
        if not getattr(self, 'recurring_deposit_account', None):
            self.add_error(None, "No Recurring Deposit Accounts found with the given account number.")
            raise forms.ValidationError("No Recurring Deposit Accounts found with the given account number.")
        
        if self.recurring_deposit_account.status == 'Closed':
            self.add_error(None, "Member Recurring Deposit is Closed.")
            raise forms.ValidationError("Member Recurring Deposit is Closed.")
        
        return cleaned_data