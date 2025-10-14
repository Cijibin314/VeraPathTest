import random
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

def generate_mock_insurance_data():
    """Generates a single mock insurance package."""
    return {
        "insurancepackageid": f"MOCK-{random.randint(100, 200)}",
        "eligibilitystatus": random.choice(["eligible", "ineligible", "unknown"])
    }

def generate_mock_referral_auth(provider_npi, payer_code):
    """Generates a single mock referral authorization with timestamps."""
    status = random.choice(["pending", "scheduled", "completed", "cancelled"])
    created_at = timezone.now() - timedelta(days=random.randint(30, 90))
    acknowledged_at, scheduled_at, completed_at, cancelled_at = None, None, None, None

    if status in ["acknowledged", "scheduled", "completed"]:
        acknowledged_at = created_at + timedelta(days=random.randint(1, 5))
    if status in ["scheduled", "completed"]:
        scheduled_at = (acknowledged_at or created_at) + timedelta(days=random.randint(1, 10))
    if status == "completed":
        completed_at = (scheduled_at or created_at) + timedelta(days=random.randint(5, 20))
    if status == "cancelled":
        cancelled_at = created_at + timedelta(days=random.randint(1, 15))

    return {
        "referringprovidernpi": provider_npi,
        "payercode": payer_code,
        "referralstatus": status,
        "specialty": random.choice(["Cardiology", "Dermatology", "Orthopedics"]),
        "amount": str(random.randint(50, 500)),
        "created_at": created_at,
        "acknowledged_at": acknowledged_at,
        "scheduled_at": scheduled_at,
        "completed_at": completed_at,
        "cancelled_at": cancelled_at,
    }

def generate_mock_creation_date():
    """Generates a random creation date in the past for a referral."""
    return (timezone.now() - timedelta(days=random.randint(30, 90))).date()
