from datetime import date
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class LawFirm(models.Model):
    """Multi-tenant organization representing an independent law practice."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True, help_text="Unique firm identifier (e.g. morgan-legal)")
    logo = models.FileField(upload_to='firm_logos/', blank=True, null=True, help_text="Upload firm logo (PNG, JPG, SVG)")
    phone = models.CharField(max_length=25, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#1D4ED8', help_text="Hex brand color (e.g. #1D4ED8)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class MedicalProviderFacility(models.Model):
    """Medical practice, imaging clinic, or hospital facility using the provider network."""
    FACILITY_TYPES = (
        ('ER', 'Emergency Room / Hospital'),
        ('URGENT_CARE', 'Urgent Care / Walk-in Clinic'),
        ('CHIROPRACTIC', 'Chiropractic Clinic'),
        ('PHYSICAL_THERAPY', 'Physical Therapy'),
        ('ORTHOPEDIC', 'Orthopedic Surgery / Specialist'),
        ('IMAGING', 'MRI / CT / Diagnostic Imaging'),
        ('PAIN_MANAGEMENT', 'Interventional Pain Management'),
        ('NEUROLOGY', 'Neurology / Specialist'),
        ('OTHER', 'General / Other Facility'),
    )
    name = models.CharField(max_length=200)
    facility_type = models.CharField(max_length=30, choices=FACILITY_TYPES, default='CHIROPRACTIC')
    phone = models.CharField(max_length=25, blank=True, null=True)
    fax = models.CharField(max_length=25, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    records_email = models.EmailField(blank=True, null=True, help_text="Direct email for medical records/liens")
    address = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Medical Provider Facilities"

    def __str__(self):
        return f"{self.name} ({self.get_facility_type_display()})"


class User(AbstractUser):
    SUPERADMIN = 'SUPERADMIN'
    FIRM_ADMIN = 'FIRM_ADMIN'
    ATTORNEY = 'ATTORNEY'
    CASE_MANAGER = 'CASE_MANAGER'
    MEDICAL_PROVIDER = 'MEDICAL_PROVIDER'
    CLIENT = 'CLIENT'

    ROLE_CHOICES = (
        (SUPERADMIN, 'Platform SuperAdmin'),
        (FIRM_ADMIN, 'Law Firm Administrator'),
        (ATTORNEY, 'Attorney'),
        (CASE_MANAGER, 'Case Manager'),
        (MEDICAL_PROVIDER, 'Medical Provider Staff'),
        (CLIENT, 'Client'),
    )
    role = models.CharField(max_length=25, choices=ROLE_CHOICES, default=CLIENT)
    phone = models.CharField(max_length=25, blank=True, null=True)
    must_change_password = models.BooleanField(default=False, verbose_name="Must Change Password on Next Login")

    firm = models.ForeignKey(LawFirm, on_delete=models.CASCADE, null=True, blank=True, related_name='staff_members')
    medical_facility = models.ForeignKey(MedicalProviderFacility, on_delete=models.CASCADE, null=True, blank=True, related_name='facility_staff')

    def __str__(self):
        org = f" - {self.firm.name}" if self.firm else (f" - {self.medical_facility.name}" if self.medical_facility else "")
        return f"{self.get_full_name() or self.username} ({self.get_role_display()}{org})"


class Client(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='client_profile', null=True, blank=True,
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Date of Birth")
    drivers_license = models.CharField(max_length=50, blank=True, null=True, verbose_name="Client DL #")
    address = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Case(models.Model):
    STATUS_CHOICES = (
        ('INTAKE', 'Intake'),
        ('TREATMENT', 'Medical Treatment'),
        ('DEMAND', 'Demand Package'),
        ('NEGOTIATIONS', 'Negotiations'),
        ('LITIGATION', 'Litigation'),
        ('SETTLED', 'Settled / Closing'),
    )
    case_number = models.CharField(max_length=50, unique=True)
    firm = models.ForeignKey(LawFirm, on_delete=models.CASCADE, null=True, blank=True, related_name='cases')
    police_report_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Police Report #")
    police_precinct = models.CharField(max_length=100, blank=True, null=True, verbose_name="Police Precinct / Agency")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='cases')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INTAKE')

    incident_date = models.DateField(blank=True, null=True)
    accident_location = models.CharField(max_length=255, blank=True, null=True)
    accident_description = models.TextField(blank=True, null=True)

    ems_dispatched = models.BooleanField(default=False, verbose_name="EMS / Ambulance")
    initial_hospital = models.CharField(max_length=255, blank=True, null=True, verbose_name="Initial Hospital / ER")

    er_facility = models.CharField(max_length=255, blank=True, null=True, verbose_name="Emergency Room / ER")
    ambulance_provider = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ambulance / EMS Provider")
    initial_clinic = models.CharField(max_length=255, blank=True, null=True, verbose_name="Initial Clinic / Hospital")

    at_fault_driver_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="At-Fault Driver Name")
    insurance_carrier = models.CharField(max_length=150, blank=True, null=True, verbose_name="AFD Insurance")
    policy_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Policy #")
    claim_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Insurance Claim #")
    at_fault_drivers_license = models.CharField(max_length=50, blank=True, null=True, verbose_name="At-Fault DL #")
    policy_limits = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    assigned_attorney = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='attorney_cases')
    assigned_case_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_cases')

    # Lifecycle & 15-Day Auto-Archiving Fields
    settled_date = models.DateField(blank=True, null=True, help_text="Date when case was moved to Settled")
    is_archived = models.BooleanField(default=False, db_index=True, help_text="True if archived (hidden from active workspace)")
    archived_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def days_since_settled(self):
        if self.settled_date:
            return (date.today() - self.settled_date).days
        return None

    def check_auto_archive(self):
        """Archives case if it has been settled for 15 or more days."""
        if self.status == 'SETTLED' and self.settled_date and not self.is_archived:
            if (date.today() - self.settled_date).days >= 15:
                self.is_archived = True
                self.save(update_fields=['is_archived'])
                return True
        return False

    def __str__(self):
        return f"{self.case_number} - {self.client}"


class CaseNote(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class MedicalBill(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='medical_bills')
    provider = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Original Billed Amount")
    reduced_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Negotiated Lien Amount")
    received = models.BooleanField(default=False)
    bill_document = models.FileField(upload_to='medical_bills/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def effective_amount(self):
        if self.reduced_amount is not None:
            return self.reduced_amount
        return self.amount


class MedicalTreatmentRecord(models.Model):
    """Two-way care progression link between a Case and an in-network Medical Provider Facility."""
    TREATMENT_STATUS = (
        ('REFERRED', 'Referred / Awaiting Intake'),
        ('APPOINTMENT_SET', 'First Appointment Scheduled'),
        ('IN_TREATMENT', 'Active Treatment / Therapy'),
        ('DISCHARGED', 'Completed Care / Discharged'),
        ('NO_SHOW', 'Patient Failed to Attend / Non-Compliant'),
    )
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='treatment_records')
    facility = models.ForeignKey(MedicalProviderFacility, on_delete=models.CASCADE, related_name='referred_cases')
    status = models.CharField(max_length=25, choices=TREATMENT_STATUS, default='REFERRED')
    first_visit_date = models.DateField(blank=True, null=True)
    discharge_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, help_text="Clinical notes or referral instructions")
    records_received = models.BooleanField(default=False)
    lien_received = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.case.case_number} @ {self.facility.name} ({self.get_status_display()})"


class Settlement(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name='settlement')
    gross_settlement = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    attorney_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=33.33)
    litigation_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    final_client_net = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)


class CaseDocument(models.Model):
    DOC_TYPES = (
        ('CRASH_PHOTO', 'Accident Scene / Damage Photo'),
        ('POLICE_REPORT', 'Police Accident Report'),
        ('MEDICAL_BILL', 'Medical Bill / Lien'),
        ('MEDICAL_RECORD', 'Medical Record'),
        ('INSURANCE_LETTER', 'Insurance Letter'),
        ('OTHER', 'Other Evidence'),
    )
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    document_type = models.CharField(max_length=50, choices=DOC_TYPES, default='OTHER')
    file = models.FileField(upload_to='case_vault/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Passenger(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='passengers')
    name = models.CharField(max_length=150)
    date_of_birth = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=25, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    is_injured = models.BooleanField(default=False)
    is_minor = models.BooleanField(default=False)
    linked_case = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True, blank=True, related_name='originating_passenger_records')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        category = "Minor" if self.is_minor else "Adult"
        return f"{self.name} ({category} Passenger - Case #{self.case.case_number})"


class CaseMessage(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.sender.username} on Case #{self.case.case_number} at {self.created_at:%Y-%m-%d %H:%M}"


class DeletedCaseLog(models.Model):
    case_number = models.CharField(max_length=50)
    client_name = models.CharField(max_length=150)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(help_text="Mandatory business reason for case deletion")
    summary = models.TextField(blank=True, help_text="Snapshot summary of the case before destruction")
    deleted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-deleted_at']

    def __str__(self):
        return f"Deleted Case #{self.case_number} ({self.client_name}) on {self.deleted_at:%Y-%m-%d %H:%M}"


class EmailTemplate(models.Model):
    """Customizable automated email dispatch templates per law firm."""
    TEMPLATE_KEYS = (
        ('CLIENT_ONBOARDING', 'Client Onboarding & Portal Invitation'),
        ('STAGE_PROGRESSION', 'Case Stage Advancement Notice'),
        ('MEDICAL_REFERRAL', 'New Patient Referral to Medical Provider'),
        ('TREATMENT_COMPLETE', 'Medical Discharge / Treatment Completed Notice'),
    )
    firm = models.ForeignKey(LawFirm, on_delete=models.CASCADE, related_name='email_templates')
    template_key = models.CharField(max_length=50, choices=TEMPLATE_KEYS)
    subject = models.CharField(max_length=255)
    body = models.TextField(help_text="Supports merge tags: {{ client_name }}, {{ case_number }}, {{ firm_name }}, {{ portal_url }}")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('firm', 'template_key')

    def __str__(self):
        return f"{self.firm.name} - {self.get_template_key_display()}"