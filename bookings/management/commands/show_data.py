from django.core.management.base import BaseCommand

from bookings.models import Booking
from reports.models import Report


class Command(BaseCommand):
    help = 'Show recent bookings and reports stored in the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Recent bookings (max 10):'))
        bookings = Booking.objects.select_related('customer', 'sample_name').order_by('-created_at')[:10]
        if not bookings:
            self.stdout.write('  No bookings found.')
        for b in bookings:
            self.stdout.write(
                f'  {b.sample_reg_no} | {b.booking_date} | {b.customer} | {b.sample_name} | {b.get_status_display()}'
            )

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Recent reports (max 10):'))
        reports = Report.objects.select_related('booking', 'manager', 'incharge').order_by('-created_at')[:10]
        if not reports:
            self.stdout.write('  No reports found.')
        for r in reports:
            self.stdout.write(
                f'  {r.certificate_no} | booking={r.booking.sample_reg_no} | {r.get_status_display()} | '
                f'manager={r.manager_name or "-"} | incharge={r.incharge_name or "-"}'
            )
