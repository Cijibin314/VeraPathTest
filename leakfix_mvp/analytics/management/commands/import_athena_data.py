from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.core.paginator import Paginator
from django.utils import timezone
from analytics.models import Provider, Patient, Referral, Payer
from analytics.athena_client import get_token, get

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

        self.stdout.write("Importing referral authorizations...")
        all_patients = Patient.objects.all().order_by('id')
        paginator = Paginator(all_patients, page_size)
        total_created = 0
        total_updated = 0

        for page_num in paginator.page_range:
            self.stdout.write(f"-- Processing page {page_num} of {paginator.num_pages} --")
            for patient in paginator.page(page_num).object_list:
                insurances_data = None
                try:
                    insurances_data = get(f"patients/{patient.original_id}/insurances", practice_id, token)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"\n  -> API error for patient {patient.original_id} insurances: {e}. Skipping insurance data."))

                eligibility_by_payer = {}
                if insurances_data and insurances_data.get("insurances"):
                    eligibility_by_payer = {
                        str(ins.get("insurancepackageid")): ins.get("eligibilitystatus", "").lower() == "eligible"
                        for ins in insurances_data.get("insurances", [])
                    }

                # Find the most recent pending referral for this patient
                try:
                    referral_to_update = Referral.objects.filter(
                        patient=patient,
                        status=Referral.Status.PENDING
                    ).latest('referral_date')
                except Referral.DoesNotExist:
                    continue

                refauths_data = None
                try:
                    refauths_data = get(f"patients/{patient.original_id}/referralauths", practice_id, token)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"\n  -> API error for patient {patient.original_id} referral auths: {e}. Skipping referral auth data."))

                auth = None
                if refauths_data and refauths_data.get("referralauths"):
                    # Try to find a matching auth for the provider
                    provider_npi = referral_to_update.provider.npi
                    for ra_auth in refauths_data.get("referralauths", []):
                        if str(ra_auth.get("referringproviderid")) == provider_npi:
                            auth = ra_auth
                            break

                if not auth:
                    self.stdout.write(self.style.WARNING(f"   -> No live referral auth data found for referral {referral_to_update.id}. Skipping update."))
                    continue # Skip if no auth data

                payer_code = list(eligibility_by_payer.keys())[0] if eligibility_by_payer else None
                payer = None
                if payer_code:
                    payer, _ = Payer.objects.get_or_create(code=payer_code, defaults={"name": f"Payer {payer_code}"})

                is_in_network = eligibility_by_payer.get(payer_code, False) if payer_code else False
                status = (auth.get("referralauthtype") or "pending").lower()
                if status not in Referral.Status.values: status = Referral.Status.PENDING

                referral_to_update.status = status
                referral_to_update.in_network = is_in_network
                referral_to_update.payer = payer
                referral_to_update.cost_value = Decimal(auth.get("amount", "0") or "0")
                
                # Parse and assign dates, handling potential errors
                ack_at_str = auth.get("acknowledged_at")
                referral_to_update.ack_at = datetime.strptime(ack_at_str, "%Y-%m-%dT%H:%M:%SZ") if ack_at_str else None

                scheduled_at_str = auth.get("scheduled_at")
                referral_to_update.scheduled_at = datetime.strptime(scheduled_at_str, "%Y-%m-%dT%H:%M:%SZ") if scheduled_at_str else None

                completed_at_str = auth.get("completed_at")
                referral_to_update.completed_at = datetime.strptime(completed_at_str, "%Y-%m-%dT%H:%M:%SZ") if completed_at_str else None

                cancelled_at_str = auth.get("cancelled_at")
                referral_to_update.cancelled_at = datetime.strptime(cancelled_at_str, "%Y-%m-%dT%H:%M:%SZ") if cancelled_at_str else None

                referral_to_update.save()
                total_updated += 1