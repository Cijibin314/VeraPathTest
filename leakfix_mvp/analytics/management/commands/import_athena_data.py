import random
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.core.paginator import Paginator
from django.utils import timezone
from analytics.models import Provider, Patient, Referral, Payer
from analytics.athena_client import get_token, get
from analytics.mock_data import generate_mock_insurance_data, generate_mock_referral_auth

from datetime import datetime

from django.utils import timezone

class Command(BaseCommand):
    help = "Imports referral data, supplementing with mock data where APIs are empty."

    def add_arguments(self, parser):
        parser.add_argument("practice_id", type=str, help="Athenahealth practice ID")
        parser.add_argument("--page_size", type=int, default=25, help="Number of patients to process per page.")

    def handle(self, *args, **options):
        from datetime import datetime
        practice_id = options["practice_id"]
        page_size = options["page_size"]
        token = get_token()
        all_providers = list(Provider.objects.all())
        if not all_providers:
            raise CommandError("No providers found. Please run import_athena first.")

        self.stdout.write("Importing referral authorizations (with mock data fallback)...")
        all_patients = Patient.objects.all().order_by('id')
        paginator = Paginator(all_patients, page_size)
        total_created = 0
        total_updated = 0

        for page_num in paginator.page_range:
            self.stdout.write(f"-- Processing page {page_num} of {paginator.num_pages} --")
            for patient in paginator.page(page_num).object_list:
                try:
                    insurances_data = get(f"patients/{patient.original_id}/insurances", practice_id, token)
                    if not insurances_data.get("insurances"):
                        self.stdout.write(self.style.WARNING(f"\n  -> No live insurance data for patient {patient.original_id}. Using mock data."))
                        insurances_data = {"insurances": [generate_mock_insurance_data()]}
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"\n  -> API error for patient {patient.original_id} insurances: {e}. Using mock data."))
                    insurances_data = {"insurances": [generate_mock_insurance_data()]}

                eligibility_by_payer = {
                    str(ins.get("insurancepackageid")): ins.get("eligibilitystatus", "").lower() == "eligible"
                    for ins in insurances_data.get("insurances", [])
                }

                # Find all pending referrals for this patient
                pending_referrals = Referral.objects.filter(
                    patient=patient,
                    status=Referral.Status.PENDING
                ).order_by('-referral_date')

                if not pending_referrals:
                    continue

                try:
                    refauths_data = get(f"patients/{patient.original_id}/referralauths", practice_id, token)
                    auths = refauths_data.get("referralauths", [])
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"\n  -> API error for patient {patient.original_id} referral auths: {e}. Using mock data for all pending referrals."))
                    auths = []

                # Create a dictionary of auths by provider NPI for easier lookup
                auths_by_provider = {auth.get("referringproviderid"): auth for auth in auths}

                for referral_to_update in pending_referrals:
                    self.stdout.write(f"\n[DATA_LOG] Processing referral {referral_to_update.id} (ReferralDate: {referral_to_update.referral_date}, IsMocked: {referral_to_update.is_creation_date_mocked})")
                    auth = None
                    # If the creation date was mocked, we must generate mock auth data.
                    if referral_to_update.is_creation_date_mocked:
                        self.stdout.write(f"[DATA_LOG]   -> Flag is_creation_date_mocked is True. Skipping API call.")
                        provider_npi = referral_to_update.provider.npi
                        mock_payer_code = list(eligibility_by_payer.keys())[0] if eligibility_by_payer else "MOCK-101"
                        auth = generate_mock_referral_auth(provider_npi, mock_payer_code, base_date=timezone.make_aware(datetime.combine(referral_to_update.referral_date, datetime.min.time())))
                        self.stdout.write(f"[DATA_LOG]   -> Generated mock auth: {auth}")
                    else:
                        # Otherwise, try to find a real auth record.
                        self.stdout.write(f"[DATA_LOG]   -> Flag is_creation_date_mocked is False. Calling API.")
                        provider_npi = referral_to_update.provider.npi
                        auth = auths_by_provider.get(provider_npi)
                        if auth:
                            self.stdout.write(f"[DATA_LOG]   -> Found live auth data: {auth}")

                        # Validate the real auth data
                        if auth and auth.get("completed_at"):
                            try:
                                completed_at = datetime.strptime(auth.get("completed_at"), "%Y-%m-%dT%H:%M:%SZ").date()
                                if completed_at < referral_to_update.referral_date:
                                    self.stdout.write(self.style.WARNING(f"[DATA_LOG]   -> INVALID live data: completed_at ({completed_at}) is before referral_date ({referral_to_update.referral_date}). Discarding."))
                                    auth = None # Discard the invalid live data
                            except (ValueError, TypeError):
                                self.stdout.write(self.style.WARNING(f"[DATA_LOG]   -> Could not parse completed_at. Discarding."))
                                auth = None # Discard the invalid live data

                    # If still no auth, generate mock data as a final fallback.
                    if not auth:
                        self.stdout.write(self.style.WARNING(f"[DATA_LOG]   -> No valid auth found. Generating mock data as fallback."))
                        provider_npi = referral_to_update.provider.npi
                        mock_payer_code = list(eligibility_by_payer.keys())[0] if eligibility_by_payer else "MOCK-101"
                        auth = generate_mock_referral_auth(provider_npi, mock_payer_code, base_date=timezone.make_aware(datetime.combine(referral_to_update.referral_date, datetime.min.time())))
                        self.stdout.write(f"[DATA_LOG]   -> Generated mock auth: {auth}")

                    payer_code = list(eligibility_by_payer.keys())[0] if eligibility_by_payer else None
                    if not payer_code: continue
                    payer, _ = Payer.objects.get_or_create(code=payer_code, defaults={"name": f"Payer {payer_code}"})

                    is_in_network = eligibility_by_payer.get(payer_code, False)
                    status = (auth.get("referralstatus") or auth.get("referralauthtype") or "pending").lower()
                    if status not in Referral.Status.values: status = Referral.Status.PENDING

                    referral_to_update.status = status
                    referral_to_update.in_network = is_in_network
                    referral_to_update.payer = payer
                    referral_to_update.cost_value = Decimal(auth.get("amount", "0") or "0")
                    referral_to_update.ack_at = auth.get("acknowledged_at")
                    referral_to_update.scheduled_at = auth.get("scheduled_at")
                    referral_to_update.completed_at = auth.get("completed_at")
                    referral_to_update.cancelled_at = auth.get("cancelled_at")
                    referral_to_update.save()
                    total_updated += 1

                    self.stdout.write(f"  -> Updated referral {referral_to_update.id}:")
                    self.stdout.write(f"    referral_date: {referral_to_update.referral_date}")
                    self.stdout.write(f"    created_at: {referral_to_update.created_at}")
                    self.stdout.write(f"    ack_at: {referral_to_update.ack_at}")
                    self.stdout.write(f"    scheduled_at: {referral_to_update.scheduled_at}")
                    self.stdout.write(f"    completed_at: {referral_to_update.completed_at}")

        self.stdout.write(self.style.SUCCESS(f"Import complete. Updated {total_updated} referral records."))