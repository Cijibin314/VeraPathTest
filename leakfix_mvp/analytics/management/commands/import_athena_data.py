from decimal import Decimal
from django.core.management.base import BaseCommand
from analytics.models import Provider, Patient, Referral, Payer, ReferralHistory
from analytics.athena_client import get_token, get

class Command(BaseCommand):
    help = "Import referring providers and referral authorizations from Athenahealth"

    def add_arguments(self, parser):
        parser.add_argument("practice_id", type=str, help="Athenahealth practice ID")

    def handle(self, *args, **options):
        practice_id = options["practice_id"]
        token = get_token()

        # 1. Import referring providers
        providers_data = get("referringproviders", practice_id, token)
        count_providers = 0
        for item in providers_data.get("referringproviders", providers_data):
            npi = item.get("npinumber") or item.get("npi")
            first = item.get("firstname", "")
            last = item.get("lastname", "")
            full_name = f"{first} {last}".strip()
            specialty = item.get("specialty", "")
            subspecialty = item.get("subspecialty", "")
            city = item.get("city", "")
            state = item.get("state", "")

            Provider.objects.update_or_create(
                npi=npi,
                defaults={
                    "full_name": full_name,
                    "specialty": specialty,
                    "subspecialty": subspecialty,
                    "city": city,
                    "state": state,
                },
            )
            count_providers += 1
        self.stdout.write(self.style.SUCCESS(f"Imported/updated {count_providers} referring providers."))

        # 2. Import referral authorizations for each patient in the local DB
        count_referrals = 0
        for patient in Patient.objects.all():
            # The patient.original_id must match the Athena patient ID
            patient_id = patient.original_id
            try:
                refauths = get(f"patients/{patient_id}/referralauths", practice_id, token)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to fetch referralauths for patient {patient_id}: {e}"))
                continue

            # Adjust the key based on actual response structure
            for auth in refauths.get("referralauths", refauths):
                # Extract or map fields — adjust these to match the real JSON fields
                provider_npi = auth.get("referringprovidernpi") or auth.get("referringProviderNPI")
                order_status = auth.get("referralstatus") or "pending"
                in_network = (auth.get("innetwork") == "true") if auth.get("innetwork") is not None else True
                cost_val = Decimal(auth.get("amount", "0") or "0")
                specialty = auth.get("specialty") or ""

                # Look up or create the provider by NPI
                if provider_npi:
                    provider, _ = Provider.objects.get_or_create(npi=provider_npi, defaults={"full_name": provider_npi})
                else:
                    provider = None

                # Look up payer if available (by code)
                payer_code = auth.get("payercode") or None
                payer = None
                if payer_code:
                    payer, _ = Payer.objects.get_or_create(code=payer_code, defaults={"name": payer_code})

                # Map status string to Referral.Status value
                status_map = {
                    "pending": Referral.Status.PENDING,
                    "scheduled": Referral.Status.SCHEDULED,
                    "completed": Referral.Status.COMPLETED,
                    "cancelled": Referral.Status.CANCELLED,
                    "acknowledged": Referral.Status.ACKNOWLEDGED,
                    "sent": Referral.Status.SENT,
                }
                status = status_map.get(order_status.lower(), Referral.Status.PENDING)

                referral, created = Referral.objects.update_or_create(
                    patient=patient,
                    provider=provider,
                    specialty=specialty or (provider.specialty if provider else ""),
                    defaults={
                        "payer": payer,
                        "status": status,
                        "in_network": in_network,
                        "cost_value": cost_val,
                    },
                )
                if created:
                    ReferralHistory.objects.create(referral=referral, status=referral.status)
                    count_referrals += 1

        self.stdout.write(self.style.SUCCESS(f"Imported/updated {count_referrals} referrals."))
        self.stdout.write(self.style.ERROR(...))
