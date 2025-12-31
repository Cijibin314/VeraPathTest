"""
Generate invoices based on retained revenue over a date range.

This command computes total retained revenue for all referrals created
during a given period, multiplies it by a fee rate (e.g. 0.05),
and creates an Invoice object.  Use monthly periods to run this
command on the first of each month for the previous month.
"""
from datetime import date
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum
from leakfix_mvp.analytics.models import Referral, Invoice


class Command(BaseCommand):
    help = 'Generate invoices for a given period'

    def add_arguments(self, parser):
        parser.add_argument('--start', type=str, help='Period start date (YYYY-MM-DD)')
        parser.add_argument('--end', type=str, help='Period end date (YYYY-MM-DD)')
        parser.add_argument(
            '--fee_rate',
            type=str,
            default='0.05',
            help='Fee rate as decimal (e.g. 0.05 for 5%)'
        )

    def handle(self, *args, **opts):
        try:
            start_date = date.fromisoformat(opts['start']) if opts.get('start') else None
            end_date = date.fromisoformat(opts['end']) if opts.get('end') else None
        except ValueError:
            raise CommandError('Invalid date format. Use YYYY-MM-DD.')

        if not start_date or not end_date:
            raise CommandError('You must specify a start and end date.')

        if end_date < start_date:
            raise CommandError('End date must be on or after start date.')

        fee_rate = Decimal(opts['fee_rate'])
        retained = (
            Referral.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
                in_network=True
            )
            .aggregate(total=Sum('cost_value'))
            .get('total')
            or Decimal('0.00')
        )

        amount_due = retained * fee_rate
        invoice = Invoice.objects.create(
            period_start=start_date,
            period_end=end_date,
            retained_revenue=retained,
            fee_rate=fee_rate,
            amount_due=amount_due,
            is_paid=False,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Created invoice {invoice.id}: retained ${retained} fee_rate {fee_rate} amount due ${amount_due}'
            )
        )
