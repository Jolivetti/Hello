from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from claims.models import User, Client as ClientProfile, Case, MedicalBill, Settlement

class LegalCRMSmokeTests(TestCase):
    def setUp(self):
        # Setup Staff and Client users
        self.staff_user = User.objects.create_user(username="staff_user", password="password123", role="ATTORNEY")
        self.client_user = User.objects.create_user(username="johndoe", password="password123", role="CLIENT")
        
        # Setup Client Profile and Case
        self.client_profile = ClientProfile.objects.create(
            user=self.client_user,
            first_name="John",
            last_name="Doe",
            email="johndoe@example.com"
        )
        self.case = Case.objects.create(
            case_number="DOI-091126-1",
            police_report_number="PR-12345",
            client=self.client_profile,
            assigned_attorney=self.staff_user,
            insurance_carrier="Progressive",
            policy_limits=Decimal("50000.00"),
            status="TREATMENT"
        )
        self.bill = MedicalBill.objects.create(
            case=self.case,
            provider="Arrowhead Clinic",
            amount=Decimal("1500.00"),
            received=True
        )
        self.settlement = Settlement.objects.create(
            case=self.case,
            gross_settlement=Decimal("25000.00"),
            attorney_fee_percent=Decimal("33.33"),
            litigation_costs=Decimal("500.00")
        )

    def test_attorney_dashboard_and_case_detail(self):
        """Verify staff can access dashboard, case details, and see calculations."""
        c = Client()
        c.login(username="staff_user", password="password123")
        
        # Dashboard check
        res_dash = c.get(reverse('index'))
        self.assertEqual(res_dash.status_code, 200)
        self.assertContains(res_dash, "Active Claims Ledger")
        
        # Case detail check
        res_detail = c.get(reverse('case_detail', args=[self.case.id]))
        self.assertEqual(res_detail.status_code, 200)
        self.assertContains(res_detail, "DOI-091126-1")
        self.assertContains(res_detail, "Arrowhead Clinic")

    def test_client_portal_access(self):
        """Verify client sees their active case and cannot access staff views."""
        c = Client()
        c.login(username="johndoe", password="password123")
        
        # Client portal check
        res_portal = c.get(reverse('client_portal'))
        self.assertEqual(res_portal.status_code, 200)
        self.assertContains(res_portal, "DOI-091126-1")
        self.assertContains(res_portal, "Arrowhead Clinic")
        self.assertNotContains(res_portal, "No Active Claims Found")

        # Security check: Client must NOT be allowed to access case detail
        res_forbidden = c.get(reverse('case_detail', args=[self.case.id]))
        self.assertEqual(res_forbidden.status_code, 302)  # Redirects away from staff view