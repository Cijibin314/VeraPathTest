import hashlib
from decimal import Decimal
from django.db import models

class Payer(models.Model):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.name

class Provider(models.Model):
    npi = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    specialty = models.CharField(max_length=120)
    subspecialty = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.specialty})"

class Patient(models.Model):
    original_id = models.CharField(max_length=120, unique=True)
    pseudonym = models.CharField(max_length=64, unique=True, editable=False)

    def save(self, *args, **kwargs) -> None:
        if not self.pseudonym:
            self.pseudonym = hashlib.sha256(self.original_id.encode()).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Patient {self.pseudonym[:8]}"

class Referral(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        ACKNOWLEDGED = 'ack', 'Acknowledged'
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT)
    payer = models.ForeignKey(Payer, on_delete=models.SET_NULL, null=True, blank=True)
    specialty = models.CharField(max_length=120, blank=True)  # NEW: record referral specialty
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    in_network = models.BooleanField(default=True)
    cost_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    referral_date = models.DateField()
    suggested_provider_ids = models.CharField(max_length=200, blank=True)
    is_creation_date_mocked = models.BooleanField(default=False)
    created_at = models.DateTimeField()
    ack_at = models.DateTimeField(null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

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
