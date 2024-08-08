
# Create your tests here.
from django.test import TestCase
from django.urls import reverse
from micro_admin.forms import *
from micro_admin.models import *
from tempfile import NamedTemporaryFile
from micro_admin.templatetags import ledgertemplatetags, loans_tags


class ModelformTest(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name='sbh', opening_date='2014-10-10', country='ind', state='AP',
            district='Nellore', city='Nellore', area='circle', pincode=502286,
            phone_number=944454651165)
        self.user = User.objects.create_superuser(
            'jag123', 'jagadeesh123@gmail.com')
        self.temp_file = NamedTemporaryFile(delete=False, suffix='.jpg',)

    def test_BranchForm(self):
        form = BranchForm(data={
            'name': 'andhra', 'opening_date': '12/10/2014', 'country': 'ind',
            'state': 'AP', 'district': 'Nellore', 'city': 'Nellore',
            'area': 'circle', 'phone_number': '9444546511', 'pincode': 502286})
        self.assertTrue(form.is_valid())

    def test_BranchForm_invalid(self):
        form = BranchForm(data={
            'name': '', 'opening_date': '', 'country': '', 'state': '',
            'district': '', 'city': '', 'area': '', 'phone_number': '',
            'pincode': ''})
        self.assertFalse(form.is_valid())

    def test_UserForm(self):
        form = UserForm(data={
            'email': 'jag@gmail.com', 'first_name': 'jagadeesh', 'gender': 'M',
            'branch': self.branch.id, 'user_roles': 'BranchManager',
            'username': 'jagadeesh', 'password': 'jag123', "country": 'Ind',
            "state": 'AP', "district": 'Nellore', "city": 'Nellore',
            "area": 'rfc', "mobile": 9444546511, "pincode": 502286})
        self.assertTrue(form.is_valid())

    def test_UserForm_invalid(self):
        form = UserForm(data={
            'email': '', 'first_name': '', 'gender': '',
            'branch': self.branch.id, 'user_roles': '', 'username': '',
            'password': '', 'country': '', 'state': '', 'district': '',
            'city': '', 'area': '', 'mobile': '', 'pincode': ''})
        self.assertFalse(form.is_valid())

    def test_GroupForm(self):
        form = GroupForm(data={
            "name": 'Star', "account_number": 123456,
            "activation_date": '10/10/2014', "branch": self.branch.id})
        self.assertTrue(form.is_valid())

    def test_GroupForm_invalid(self):
        form = GroupForm(data={
            "name": "", "account_number": "", "activation_date": "",
            "branch": self.branch.id})
        self.assertFalse(form.is_valid())

    def test_ClientForm(self):
        form = ClientForm(data={
            "first_name": "Micro", "last_name": "Pyramid",
            "date_of_birth": '10/10/2014', "joined_date": "10/10/2014",
            "branch": self.branch.id, "account_number": 123, "gender": "M",
            "client_role": "FirstLeader", "occupation": "Teacher",
            "annual_income": 2000, "country": 'Ind', "state": 'AP',
            "district": 'Nellore', "city": 'Nellore', "area": 'rfc',
            "mobile": 9444546511, "pincode": 502286})
        self.assertTrue(form.is_valid())

    def test_ClientForm_invalid(self):
        form = ClientForm(data={
            "first_name": "", "last_name": "", "date_of_birth": '',
            "joined_date": "", "branch": self.branch.id, "account_number": "",
            "gender": "", "client_role": "", "occupation": "",
            "annual_income": '', "country": '', "state": '', "district": '',
            "city": '', "area": '', "mobile": '', "pincode": ''})
        self.assertFalse(form.is_valid())

    def test_SavingsAccountForm(self):
        form = SavingsAccountForm(data={
            "account_no": 12345, "opening_date": '10/10/2014',
            "min_required_balance": 0, "annual_interest_rate": 0})
        self.assertTrue(form.is_valid())

    def test_LoanAccountForm(self):
        form = LoanAccountForm(data={
            "account_no": 12, 'created_by': self.user.id, "loan_amount": 10000,
            "interest_type": 'Flat', "loan_repayment_period": 123,
            "loan_repayment_every": 12, "annual_interest_rate": 12,
            "loanpurpose_description": 'Hospitality'})
        self.assertTrue(form.is_valid())

    def test_LoanAccountForm_invalid(self):
        form = LoanAccountForm(data={
            "account_no": '', 'created_by': self.user.id, "loan_amount": '',
            "interest_type": '', "loan_repayment_period": '',
            "loan_repayment_every": '', "annual_interest_rate": '',
            "loanpurpose_description": ''})
        self.assertFalse(form.is_valid())

    def test_SavingsAccountForm_invalid(self):
        form = SavingsAccountForm(data={
            "account_no": 123, "opening_date": '10/10/2014',
            "min_required_balance": 0,
            "annual_interest_rate": 3})
        self.assertTrue(form.is_valid())

    def test_ReceiptForm(self):
        form = ReceiptForm(data={
            "date": '10/10/2014', "branch": self.branch.id,
            "receipt_number": 12345})
        self.assertTrue(form.is_valid())

    def test_PaymentForm(self):
        form = PaymentForm(data={
            "date": '10/10/2014', "branch": self.branch.id,
            "voucher_number": 1231, "payment_type": 'Loans', "amount": 500,
            "interest": 3, "total_amount": 5000,
            "totalamount_in_words": '1 rupee'})
        self.assertTrue(form.is_valid())

    def test_PaymentForm_invalid(self):
        form = PaymentForm(data={
            "date": "", "branch": "", "voucher_number": "", "payment_type": "",
            "amount": "", "interest": "", "total_amount": "",
            "totalamount_in_words": ""})
        self.assertFalse(form.is_valid())


class TemplateTagsTest(TestCase):
    def test_demand_collections_difference(self):
        res = ledgertemplatetags.demand_collections_difference(20, 10)
        self.assertEqual(res, 10)





class AdminViewsTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('jagadeesh', 'jagadeesh@gmail.com', 'jag123')
        self.branch = Branch.objects.create(
            name='sbh', opening_date='2014-10-10', country='ind', state='AP',
            district='Nellore', city='Nellore', area='circle', pincode=502286,
            phone_number='944454651165'
        )
        self.branch1 = Branch.objects.create(
            name='sbi', opening_date='2014-10-10', country='ind', state='AP',
            district='Nellore', city='Nellore', area='circle', pincode=502286,
            phone_number='944454651165'
        )
        self.branch2 = Branch.objects.create(
            name='andra', opening_date='2014-10-10', country='ind', state='AP',
            district='Nellore', city='Nellore', area='circle', pincode=502286,
            phone_number='944454651165'
        )

        self.staff = User.objects.create_user(
            username='jag', email='jagadeesh@gmail.com', password='jag'
        )
        self.staff1 = User.objects.create_user(
            username='ravi', email='ravi@gmail.com', password='ravi'
        )

        self.member1 = Client.objects.create(
            first_name="Micro", last_name="Pyramid", created_by=self.staff,
            date_of_birth='2014-10-10', joined_date="2014-10-10",
            branch=self.branch, account_number=123, gender="M",
            client_role="FirstLeader", occupation="Teacher",
            annual_income=2000, country='Ind', state='AP', district='Nellore',
            city='Nellore', area='rfc'
        )
        self.member2 = Client.objects.create(
            first_name="Micro1", last_name="Pyramid", created_by=self.staff,
            date_of_birth='2014-10-10', joined_date="2014-10-10",
            branch=self.branch, account_number=1234, gender="M",
            client_role="FirstLeader", occupation="Teacher",
            annual_income=2000, country='Ind', state='AP',
            district='Nellore', city='Nellore', area='rfc'
        )

        self.member1_savings_account = SavingsAccount.objects.create(
            account_no='CS1', client=self.member1, opening_date='2014-01-01',
            min_required_balance=0, savings_balance=100,
            annual_interest_rate=1, created_by=self.staff, status='Approved'
        )
        self.member2_savings_account = SavingsAccount.objects.create(
            account_no='CS2', client=self.member2, opening_date='2014-01-01',
            min_required_balance=0, savings_balance=100,
            annual_interest_rate=1, created_by=self.staff,
            status='Approved'
        )

        self.group1 = Group.objects.create(
            name='group1', created_by=self.staff, account_number='1',
            activation_date='2014-01-01', branch=self.branch
        )
        self.group1.clients.add(self.member1)
        self.group1.save()

        self.member1.status = 'Assigned'
        self.member1.save()

        self.group_client = Client.objects.create(
            first_name="Micro2", last_name="Pyramid", created_by=self.staff,
            date_of_birth='2014-10-10', joined_date="2014-10-10",
            branch=self.branch, account_number=1, gender="M",
            client_role="FirstLeader", occupation="Teacher",
            annual_income=2000, country='Ind', state='AP',
            district='Nellore', city='Nellore', area='rfc'
        )
        self.group_client.status = 'Assigned'
        self.group_client.save()

        self.group2 = Group.objects.create(
            name='group2', created_by=self.staff, account_number='2',
            activation_date='2014-01-01', branch=self.branch
        )
        self.group2.clients.add(self.group_client)
        self.group2.clients.add(self.member2)
        self.group2.save()

        self.group1_savings_account = SavingsAccount.objects.create(
            account_no='GS1', group=self.group1, opening_date='2014-01-01',
            min_required_balance=0, savings_balance=100,
            annual_interest_rate=1, created_by=self.staff1, status='Approved'
        )
        self.group2_savings_account = SavingsAccount.objects.create(
            account_no='GS2', group=self.group2, opening_date='2014-01-01',
            min_required_balance=0, savings_balance=100,
            annual_interest_rate=1, created_by=self.staff, status='Approved'
        )

        self.grouploan = LoanAccount.objects.create(
            account_no='GL1', interest_type='Flat', group=self.group1,
            created_by=self.staff, status="Approved", loan_amount=12000,
            loan_repayment_period=12, loan_repayment_every=1,
            annual_interest_rate=2, loanpurpose_description='Home Loan',
            interest_charged=20, total_loan_balance=12000,
            principle_repayment=1000
        )
        self.clientloan = LoanAccount.objects.create(
            account_no='CL1', interest_type='Flat', client=self.member1,
            created_by=self.staff, status="Approved", loan_amount=12000,
            loan_repayment_period=12, loan_repayment_every=1,
            annual_interest_rate=2, loanpurpose_description='Home Loan',
            interest_charged=20, total_loan_balance=12000,
            principle_repayment=1000
        )

        self.loanaccount_group2 = LoanAccount.objects.create(
            account_no='GL2', interest_type='Flat', group=self.group2,
            created_by=self.staff, status="Approved", loan_amount=12000,
            loan_repayment_period=12, loan_repayment_every=1,
            annual_interest_rate=2, loanpurpose_description='Home Loan',
            interest_charged=20, total_loan_balance=12000,
            principle_repayment=1000
        )

        self.fixed_deposit = FixedDeposits.objects.create(
            client=self.member1, deposited_date='2014-01-01', status='Opened',
            fixed_deposit_number='f1', fixed_deposit_amount=1200,
            fixed_deposit_period=12, fixed_deposit_interest_rate=3,
            nominee_firstname='r', nominee_lastname='k', nominee_gender='M',
            relationship_with_nominee='friend',
            nominee_date_of_birth='2014-10-10', nominee_occupation='teacher'
        )
        self.recurring_deposit = RecurringDeposits.objects.create(
            client=self.member1, deposited_date='2014-01-01',
            reccuring_deposit_number='r1', status='Opened',
            recurring_deposit_amount=1200, recurring_deposit_period=200,
            recurring_deposit_interest_rate=3, nominee_firstname='ra',
            nominee_lastname='ku', nominee_gender='M',
            relationship_with_nominee='friend',
            nominee_date_of_birth='2014-01-01', nominee_occupation='Teacher'
        )

        self.temp_file = NamedTemporaryFile(delete=False, suffix='.jpg')

        self.receipt = Receipts.objects.create(
            receipt_number=1, date="2015-02-20", staff=self.staff,
            branch=self.branch, client=self.member1,
            entrancefee_amount="100"
        )
        self.payments = Payments.objects.create(
            date="2015-02-20", staff=self.staff, branch=self.branch,
            client=self.member1, payment_type="OtherCharges", voucher_number=1,
            amount=100, total_amount=101, interest=1,
            totalamount_in_words="hundred"
        )

    def test_views(self):
        user_login = self.client.login(username='jagadeesh', password='jag123')
        self.assertTrue(user_login)

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

        response = self.client.get(reverse('micro_admin:createbranch'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'branch/create.html')

        response = self.client.get(reverse('micro_admin:createclient'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'client/create.html')

        response = self.client.get(reverse('micro_admin:createuser'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/create.html')

        response = self.client.get(reverse('micro_admin:creategroup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'group/create.html')

        response = self.client.get(reverse("micro_admin:editbranch", kwargs={"pk": self.branch.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'branch/edit.html')

        response = self.client.get(reverse("micro_admin:edituser", kwargs={"pk": self.user.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/edit.html')

        response = self.client.get(reverse("micro_admin:branchprofile", kwargs={"pk": self.branch.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'branch/view.html')

        response = self.client.get(reverse("micro_admin:userprofile", kwargs={"pk": self.user.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/profile.html')

        response = self.client.get(reverse("micro_admin:userslist"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/list.html')

        response = self.client.get(reverse("micro_admin:viewbranch"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'branch/list.html')

        response = self.client.get(reverse('micro_admin:groupslist'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'group/list.html')

        response = self.client.get(reverse('micro_admin:viewclient'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'client/list.html')

        response = self.client.get(reverse("micro_admin:deletebranch", kwargs={"pk": self.branch2.id}))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('micro_admin:userchangepassword'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_change_password.html')

        response = self.client.get(reverse("micro_admin:daybookpdfdownload", kwargs={"date": "2014-10-10"}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pdf_daybook.html')

        response = self.client.get(reverse('micro_admin:generalledgerpdfdownload'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pdfgeneral_ledger.html')

        response = self.client.get(reverse('micro_admin:paymentslist'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'list_of_payments.html')

        response = self.client.get(reverse('micro_admin:recurringdeposits'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'client/recurring-deposits/application.html')

        response = self.client.post(reverse('micro_admin:recurringdeposits'), {
            "client_name": "Micro", "client_account_no": 123,
            "nominee_date_of_birth": "", "nominee_gender": "",
            "nominee_firstname": '', "nominee_lastname": '',
            "nominee_occupation": '', "reccuring_deposit_number": "",
            "deposited_date": '', "recurring_deposit_amount": "",
            "recurring_deposit_period": "",
            "recurring_deposit_interest_rate": "",
            "relationship_with_nominee": '',
            "nominee_signature": "", "nominee_photo": "",
            "client": self.member1.id
        })
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('micro_admin:fixeddeposits'), {
            "client_name": "Micro", "client_account_no": 123,
            "nominee_firstname": '', "nominee_lastname": '',
            "nominee_gender": "", "nominee_date_of_birth": "",
            "nominee_occupation": '', "fixed_deposit_number": "",
            "deposited_date": '', "fixed_deposit_amount": "",
            "fixed_deposit_period": "", "fixed_deposit_interest_rate": "",
            "relationship_with_nominee": '', "nominee_photo": "",
            "nominee_signature": ""
        })
        self.assertEqual(response.status_code, 200)

    def test_user_logout(self):
        user_login = self.client.login(username='jagadeesh', password='jag123')
        self.assertTrue(user_login)
        response = self.client.get(reverse('micro_admin:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('micro_admin:login'), status_code=302, target_status_code=200)

    def test_user_login_view(self):
        response = self.client.post(reverse('micro_admin:login'), {
            'username': 'jagadeesh', 'password': 'jag123'
        })
        self.assertEqual(response.status_code, 200)

    def test_create_branch_invalid_post_data(self):
        user_login = self.client.login(username='jagadeesh', password='jag123')
        self.assertTrue(user_login)
        response = self.client.post(reverse("micro_admin:createbranch"), {
            'name': '', 'opening_date': '', 'country': '', 'state': '',
            'district': '', 'city': '', 'area': '', 'phone_number': '',
            'pincode': ''
        })
        self.assertEqual(response.status_code, 200)

    def test_create_client_invalid_post_data(self):
        user_login = self.client.login(username='jagadeesh', password='jag123')
        self.assertTrue(user_login)
        response = self.client.post(reverse("micro_admin:createclient"), {
            "first_name": "", "last_name": "", "date_of_birth": '',
            "joined_date": "", "branch": "", "account_number": "",
            "gender": "", "client_role": "", "occupation": "",
            "annual_income": '', "country": '', "state": '', "district": '',
            "city": '', "area": '', "mobile": '', "pincode": ''
        })
        self.assertEqual(response.status_code, 200)

    def test_addmembers_to_group_post_data(self):
        user_login = self.client.login(username='jagadeesh', password='jag123')
        self.assertTrue(user_login)
        response = self.client.post(
            reverse('micro_admin:addmember', kwargs={'group_id': self.group1.id}),
            {"clients": [self.member1.id]}
        )
        self.assertEqual(response.status_code, 200)

    def test_add_group_meeting_post_invalid_data(self):
        user_login = self.client.login(username='jagadeesh', password='jag123')
        self.assertTrue(user_login)
        response = self.client.post(
            reverse('micro_admin:addgroupmeeting', kwargs={'group_id': self.group1.id}),
            {
                "meeting_date": "",
                "meeting_time": "10-10-10",
            }
        )
        self.assertEqual(response.status_code, 200)

    def test_group_delete(self):
        user_login = self.client.login(username='jagadeesh', password='jag123')
        self.assertTrue(user_login)
        response = self.client.get(reverse('micro_admin:deletegroup', kwargs={'group_id': self.group1.id}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('micro_admin:groupslist'), status_code=302, target_status_code=200)
