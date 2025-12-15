import hashlib
from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Payer(models.Model):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.name

class Hospital(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.name

class Practice(models.Model):
    name = models.CharField(max_length=200)
    athena_practice_id = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    work_gpci = models.DecimalField(max_digits=5, decimal_places=3, default=1.0, null=True, blank=True)
    pe_gpci = models.DecimalField(max_digits=5, decimal_places=3, default=1.0, null=True, blank=True)
    mp_gpci = models.DecimalField(max_digits=5, decimal_places=3, default=1.0, null=True, blank=True)
    conversion_factor = models.DecimalField(max_digits=10, decimal_places=2, default=33.0, null=True, blank=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    practice = models.ForeignKey(Practice, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.user.username

class Provider(models.Model):
    practices = models.ManyToManyField(Practice, blank=True)
    npi = models.CharField(max_length=20, blank=True, null=True)
    full_name = models.CharField(max_length=200)
    specialty = models.CharField(max_length=120, blank=True, null=True)
    subspecialty = models.CharField(max_length=120, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    accepting_new_patients = models.BooleanField(default=True, blank=True, null=True)
    primary_department = models.CharField(max_length=200, blank=True, null=True)
    is_in_network = models.BooleanField(default=False)

    # New fields from JSON structure
    providerid = models.IntegerField(blank=True, null=True)
    firstname = models.CharField(max_length=100, blank=True, null=True)
    lastname = models.CharField(max_length=100, blank=True, null=True)
    middleinitial = models.CharField(max_length=1, blank=True, null=True)
    sex = models.CharField(max_length=1, blank=True, null=True)
    entitytype = models.CharField(max_length=50, blank=True, null=True)
    ansinamecode = models.CharField(max_length=255, blank=True, null=True)
    hideinportal = models.BooleanField(default=False, blank=True, null=True)
    schedulingname = models.CharField(max_length=200, blank=True, null=True)
    billable = models.BooleanField(default=False, blank=True, null=True)
    ansispecialtycode = models.CharField(max_length=50, blank=True, null=True)
    createencounteroncheckin = models.BooleanField(default=False, blank=True, null=True)

    class Meta:
        unique_together = (('providerid',),)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.specialty})"

class Patient(models.Model):
    original_id = models.CharField(max_length=120, unique=True)
    pseudonym = models.CharField(max_length=64, unique=True, editable=False)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs) -> None:
        if not self.pseudonym:
            self.pseudonym = hashlib.sha256(self.original_id.encode()).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} (ID: {self.original_id})"
        return f"Patient {self.pseudonym[:8]}"

class Referral(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        ACKNOWLEDGED = 'ack', 'Acknowledged'
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        NO_SHOW = 'no_show', 'No Show'
        RESCHEDULED = 'rescheduled', 'Rescheduled'
        CANCELLED = 'cancelled', 'Cancelled'
        REVIEW = 'review', 'Review'
        CLOSED = 'closed', 'Closed'

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, null=True)
    payer = models.ForeignKey(Payer, on_delete=models.SET_NULL, null=True, blank=True)
    practice = models.ForeignKey(Practice, on_delete=models.CASCADE, null=True, blank=True)
    specialty = models.CharField(max_length=120, blank=True)  # NEW: record referral specialty
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    in_network = models.BooleanField(default=True)
    is_urgent = models.BooleanField(default=False)
    documenttypeid = models.CharField(max_length=50, blank=True, null=True)
    rvu_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    referral_date = models.DateField()
    suggested_provider_ids = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    ack_at = models.DateTimeField(null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    athena_document_id = models.CharField(max_length=50, blank=True, null=True)
    athena_encounter_id = models.CharField(max_length=50, blank=True, null=True)
    athena_department_id = models.CharField(max_length=50, blank=True, null=True)
    provider_note = models.TextField(blank=True)
    note_to_patient = models.TextField(blank=True)
    visit_summary = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return f"Referral ({self.patient}) → {self.provider}"

class Metric(models.Model):
    name = models.CharField(max_length=100)
    value = models.FloatField()
    computed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name}: {self.value:.2f}"

class ReferralHistory(models.Model):
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='history')
    at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)

    class Meta:
        ordering = ["-at"]

    def __str__(self) -> str:
        return f"{self.referral.id} -> {self.status} at {self.at}"

class Invoice(models.Model):
    period_start = models.DateField()
    period_end = models.DateField()
    retained_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    fee_rate = models.DecimalField(max_digits=5, decimal_places=2)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-period_start", "-period_end"]

    def __str__(self) -> str:
        return f"Invoice {self.id} ({self.period_start} to {self.period_end})"


class ImportLog(models.Model):
    """Tracks the status and timestamp of data import tasks."""
    task_name = models.CharField(max_length=100, unique=True)
    last_run_at = models.DateTimeField()
    status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.task_name}: {self.status} at {self.last_run_at:%Y-%m-%d %H:%M}"


class CPTCodeMapping(models.Model):
    ordertypeid = models.CharField(max_length=50, help_text="The ID of the referral order type from Athena.", null=True)
    name = models.CharField(max_length=255, help_text="The human-readable name of the referral order type.")
    cpt_code = models.CharField(max_length=10, help_text="The CPT code to use for estimation.")
    work_rvu = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    non_fac_pe_rvu = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    fac_pe_rvu = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    mp_rvu = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"{self.name} -> {self.cpt_code}"
