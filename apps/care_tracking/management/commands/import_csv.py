import csv
from datetime import datetime, time
from django.core.management.base import BaseCommand
from django.utils import timezone
import pytz
from apps.users.models import User
from apps.care_tracking.models import NightEvent, DayNote, EventOption


class Command(BaseCommand):
    help = 'Import night events from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument('username', type=str, help='Username to import data for')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        username = options['username']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} does not exist'))
            return

        # Get user's timezone
        user_tz = pytz.timezone(user.timezone)

        # Get event options for keyword mapping
        event_options = {
            'wet': EventOption.objects.filter(user=user, name__icontains='wet').first(),
            'pee': EventOption.objects.filter(user=user, name__icontains='pee').first(),
            'off': EventOption.objects.filter(user=user, name__icontains='off').first(),
            'sheets_changed': EventOption.objects.filter(user=user, name__icontains='sheets changed').first(),
            'sheets_rearranged': EventOption.objects.filter(user=user, name__icontains='sheets rearranged').first(),
            'moving': EventOption.objects.filter(user=user, name__icontains='moving').first(),
            'sleeping': EventOption.objects.filter(user=user, name__icontains='sleeping').first(),
            'underwear': EventOption.objects.filter(user=user, name__icontains='underwear change').first(),
        }

        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            # Get date columns (skip 'Time' column)
            date_columns = [col for col in reader.fieldnames if col != 'Time']

            self.stdout.write(f'Found {len(date_columns)} nights to import: {date_columns}')

            # Process Summary row (index 0) - this becomes DayNotes
            summary_row = rows[0]
            for date_str in date_columns:
                summary_text = summary_row.get(date_str, '').strip()
                if summary_text and summary_text.lower() != 'summary':
                    # Parse date
                    date_obj = datetime.strptime(date_str, '%m/%d/%y').date()

                    # Check if DayNote already exists
                    day_note, created = DayNote.objects.get_or_create(
                        user=user,
                        date=date_obj,
                        defaults={'content': summary_text}
                    )

                    if created:
                        self.stdout.write(self.style.SUCCESS(f'  Created DayNote for {date_obj}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'  DayNote for {date_obj} already exists, skipping'))

            # Process time rows (skip Summary row and Notes row)
            time_rows = [row for row in rows[1:] if row.get('Time', '').strip() and row['Time'].strip().lower() != 'notes']

            events_created = 0
            events_skipped = 0

            for row in time_rows:
                time_str = row['Time'].strip()

                # Parse time (format: "21:00", "00:00", etc.)
                try:
                    time_obj = datetime.strptime(time_str, '%H:%M').time()
                except ValueError:
                    continue

                # Process each date column
                for date_str in date_columns:
                    notes = row.get(date_str, '').strip()

                    if not notes:
                        continue

                    # Parse date
                    date_obj = datetime.strptime(date_str, '%m/%d/%y').date()

                    # Combine date and time
                    naive_datetime = datetime.combine(date_obj, time_obj)

                    # Make aware in user's timezone, then convert to UTC
                    local_datetime = user_tz.localize(naive_datetime)
                    utc_datetime = local_datetime.astimezone(pytz.UTC)

                    # Check if event already exists (avoid duplicates)
                    existing = NightEvent.objects.filter(
                        user=user,
                        event_datetime=utc_datetime,
                        notes=notes
                    ).exists()

                    if existing:
                        events_skipped += 1
                        continue

                    # Create the event
                    event = NightEvent.objects.create(
                        user=user,
                        event_datetime=utc_datetime,
                        notes=notes
                    )

                    # Map event options based on keywords in notes
                    notes_lower = notes.lower()

                    if any(word in notes_lower for word in ['wet', 'soaked', 'damp']):
                        if event_options['wet']:
                            event.event_options.add(event_options['wet'])

                    if any(word in notes_lower for word in ['pee', 'urinal', 'bathroom']):
                        if event_options['pee']:
                            event.event_options.add(event_options['pee'])

                    if any(word in notes_lower for word in ['stripped', 'taking off', 'took off', 'off']):
                        if event_options['off']:
                            event.event_options.add(event_options['off'])

                    if 'sheets changed' in notes_lower or 'changed the sheets' in notes_lower:
                        if event_options['sheets_changed']:
                            event.event_options.add(event_options['sheets_changed'])

                    if any(word in notes_lower for word in ['sheets off', 'remade the beds', 'sheets rearranged']):
                        if event_options['sheets_rearranged']:
                            event.event_options.add(event_options['sheets_rearranged'])

                    if any(word in notes_lower for word in ['crawling', 'climbing', 'moving', 'between beds']):
                        if event_options['moving']:
                            event.event_options.add(event_options['moving'])

                    if any(word in notes_lower for word in ['sleeping well', 'settled', 'asleep']):
                        if event_options['sleeping']:
                            event.event_options.add(event_options['sleeping'])

                    if any(word in notes_lower for word in ['underwear', 'diaper', 'depends']):
                        if event_options['underwear']:
                            event.event_options.add(event_options['underwear'])

                    events_created += 1

            self.stdout.write(self.style.SUCCESS(f'\nImport complete!'))
            self.stdout.write(f'  Events created: {events_created}')
            self.stdout.write(f'  Events skipped (duplicates): {events_skipped}')
