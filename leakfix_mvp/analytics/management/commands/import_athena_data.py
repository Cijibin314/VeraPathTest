import random
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.core.paginator import Paginator
from django.utils import timezone
from analytics.models import Provider, Patient, Referral, Payer

class Command(BaseCommand):
    help = "Enriches existing referral data with mock statuses, costs, and timestamps."

    def add_arguments(self, parser):
        parser.add_argument("--page_size", type=int, default=100, help="Number of referrals to process per page.")

    def handle(self, *args, **options):
        page_size = options["page_size"]
        self.stdout.write("Enriching existing referrals with mock data...")

        all_referrals = Referral.objects.filter(status=Referral.Status.PENDING).order_by('id')
        if not all_referrals.exists():
            self.stdout.write(self.style.WARNING("No pending referrals to process. Run import_athena first."))
            return

        paginator = Paginator(all_referrals, page_size)
        updated_count = 0

        for page_num in paginator.page_range:
            self.stdout.write(f"-- Processing page {page_num} of {paginator.num_pages} --")
            for referral in paginator.page(page_num).object_list:
                # Decide on a final status for the mock referral
                final_status = random.choice(["scheduled", "completed", "cancelled"])
                is_eligible = random.choice([True, True, True, False])
                payer_code = f"MOCK-PAYER-{random.randint(1, 5)}"
                payer, _ = Payer.objects.get_or_create(code=payer_code, defaults={"name": f"Mock Payer {payer_code}"})

                # Generate chronological timestamps based on the existing referral date
                referral.ack_at = referral.referral_date + timedelta(days=random.randint(1, 5))
                if final_status in ["scheduled", "completed"]:
                    referral.scheduled_at = referral.ack_at + timedelta(days=random.randint(1, 10))
                if final_status == "completed":
                    referral.completed_at = referral.scheduled_at + timedelta(days=random.randint(5, 20))
                if final_status == "cancelled":
                    referral.cancelled_at = referral.ack_at + timedelta(days=random.randint(1, 15))

                referral.status = final_status
                referral.in_network = is_eligible
                referral.payer = payer
                referral.cost_value = Decimal(random.randint(50, 1200))
                
                referral.save()
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Enrichment complete. Updated {updated_count} referral records."))
