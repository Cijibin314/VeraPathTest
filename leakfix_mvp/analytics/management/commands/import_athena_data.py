import random
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.core.paginator import Paginator
from django.utils import timezone
from analytics.models import Provider, Patient, Referral, Payer
from analytics.athena_client import get_token, get
from analytics.mock_data import generate_mock_insurance_data, generate_mock_referral_auth

class Command(BaseCommand):
    help = "Imports referral data, supplementing with mock data where APIs are empty."

    def add_arguments(self, parser):
        parser.add_argument("practice_id", type=str, help="Athenahealth practice ID")
        parser.add_argument("--page_size", type=int, default=25, help="Number of patients to process per page.")

    def handle(self, *args, **options):
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

                try:
                    refauths_data = get(f"patients/{patient.original_id}/referralauths", practice_id, token)
                    if not refauths_data.get("referralauths"):
                        self.stdout.write(self.style.WARNING(f"\n  -> No live referral auth data for patient {patient.original_id}. Using mock data."))
                        mock_provider = random.choice(all_providers)
                        mock_payer_code = list(eligibility_by_payer.keys())[0] if eligibility_by_payer else "MOCK-101"
                        refauths_data = {"referralauths": [generate_mock_referral_auth(mock_provider.npi, mock_payer_code)]}
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"\n  -> API error for patient {patient.original_id} referral auths: {e}. Using mock data."))
                    mock_provider = random.choice(all_providers)
                    mock_payer_code = list(eligibility_by_payer.keys())[0] if eligibility_by_payer else "MOCK-101"
                    refauths_data = {"referralauths": [generate_mock_referral_auth(mock_provider.npi, mock_payer_code)]}

                for auth in refauths_data.get("referralauths", []):
                    provider_id = auth.get("referringproviderid")
                    if not provider_id: continue
                    provider, _ = Provider.objects.get_or_create(npi=str(provider_id), defaults={"full_name": f"Provider {provider_id}"})

                    payer_code = list(eligibility_by_payer.keys())[0] if eligibility_by_payer else None
                    if not payer_code: continue
                    payer, _ = Payer.objects.get_or_create(code=payer_code, defaults={"name": f"Payer {payer_code}"})

                    is_in_network = eligibility_by_payer.get(payer_code, False)
                    status = (auth.get("referralauthtype") or "pending").lower()
                    if status not in Referral.Status.values: status = Referral.Status.PENDING

                    # Find the most recent pending referral for this patient/provider and update it
                    try:
                        referral_to_update = Referral.objects.filter(
                            patient=patient, 
                            provider=provider,
                            status=Referral.Status.PENDING
                        ).latest('referral_date')

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
                    except Referral.DoesNotExist:
                        # If no pending referral exists, we can't update anything.
                        # This can happen if import_athena hasn't been run recently.
                        pass

        self.stdout.write(self.style.SUCCESS(f"Import complete. Updated {total_updated} referral records."))