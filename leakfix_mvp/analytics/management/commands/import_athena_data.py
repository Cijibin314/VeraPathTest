from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.core.paginator import Paginator
from analytics.models import Provider, Patient, Referral, Payer, ReferralHistory
from analytics.athena_client import get_token, get

class Command(BaseCommand):
    help = "Import referring providers and referral authorizations from Athenahealth"

    def add_arguments(self, parser):
        parser.add_argument("practice_id", type=str, help="Athenahealth practice ID")
        parser.add_argument("--page_size", type=int, default=25, help="Number of patients to process per page.")

    def handle(self, *args, **options):
        practice_id = options["practice_id"]
        page_size = options["page_size"]
        token = get_token()

        # 1. Import referring providers
        self.stdout.write("Importing referring providers...")
        try:
            providers_data = get("referringproviders", practice_id, token)
            count_providers = 0
            for item in providers_data.get("referringproviders", providers_data):
                npi = item.get("npinumber") or item.get("npi")
                if not npi:
                    continue
                Provider.objects.update_or_create(
                    npi=npi,
                    defaults={
                        "full_name": f"{item.get('firstname', '')} {item.get('lastname', '')}".strip(),
                        "specialty": item.get("specialty", ""),
                        "subspecialty": item.get("subspecialty", ""),
                        "city": item.get("city", ""),
                        "state": item.get("state", ""),
                    },
                )
                count_providers += 1
            self.stdout.write(self.style.SUCCESS(f"Imported/updated {count_providers} referring providers."))
        except Exception as e:
            raise CommandError(f"Failed to import referring providers: {e}")

        # 2. Import referral authorizations using pagination
        self.stdout.write("Importing referral authorizations...")
        all_patients = Patient.objects.all().order_by('id')
        paginator = Paginator(all_patients, page_size)
        total_referrals_created = 0

        for page_num in paginator.page_range:
            self.stdout.write(f"-- Processing page {page_num} of {paginator.num_pages} --")
            page_of_patients = paginator.page(page_num)
            
            for patient in page_of_patients.object_list:
                patient_id = patient.original_id
                self.stdout.write(f"  -> Fetching for patient {patient_id}...", ending="")
                try:
                    refauths_data = get(f"patients/{patient_id}/referralauths", practice_id, token)
                    self.stdout.write(self.style.SUCCESS(" Found."))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f" Failed: {e}"))
                    continue

                for auth in refauths_data.get("referralauths", refauths_data):
                    provider_npi = auth.get("referringprovidernpi") or auth.get("referringProviderNPI")
                    if not provider_npi:
                        continue
                    
                    provider, _ = Provider.objects.get_or_create(npi=provider_npi, defaults={"full_name": f"Provider {provider_npi}"})

                    payer_code = auth.get("payercode") or None
                    payer = None
                    if payer_code:
                        payer, _ = Payer.objects.get_or_create(code=payer_code, defaults={"name": payer_code})

                    order_status = auth.get("referralstatus") or "pending"
                    status_map = {
                        "pending": Referral.Status.PENDING,
                        "scheduled": Referral.Status.SCHEDULED,
                        "completed": Referral.Status.COMPLETED,
                        "cancelled": Referral.Status.CANCELLED,
                        "acknowledged": Referral.Status.ACKNOWLEDGED,
                        "sent": Referral.Status.SENT,
                    }
                    status = status_map.get(order_status.lower(), Referral.Status.PENDING)

                    _, created = Referral.objects.update_or_create(
                        patient=patient,
                        provider=provider,
                        specialty=auth.get("specialty") or (provider.specialty if provider else ""),
                        defaults={
                            "payer": payer,
                            "status": status,
                            "in_network": (auth.get("innetwork") == "true") if auth.get("innetwork") is not None else True,
                            "cost_value": Decimal(auth.get("amount", "0") or "0"),
                        },
                    )
                    if created:
                        ReferralHistory.objects.create(referral=referral, status=referral.status)
                        total_referrals_created += 1

        self.stdout.write(self.style.SUCCESS(f"Import complete. Created {total_referrals_created} new referrals in total."))
