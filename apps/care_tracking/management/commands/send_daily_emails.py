"""
Management command to send daily email summaries to users.
Run this command daily (via cron) to send email summaries.
"""

from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from apps.users.models import User
from apps.care_tracking.models import NightEvent, DayNote
import pytz
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Send daily email summaries to users who have enabled them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force send emails regardless of time (for testing)',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Send email only to specific username (for testing)',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        specific_user = options.get('user', None)

        # Get current time
        now_utc = timezone.now()

        # Query users with daily email enabled
        users_query = User.objects.filter(daily_email_enabled=True)

        if specific_user:
            users_query = users_query.filter(username=specific_user)

        users = users_query.select_related()

        sent_count = 0
        skipped_count = 0
        error_count = 0

        for user in users:
            try:
                # Convert current time to user's timezone
                user_tz = pytz.timezone(user.timezone)
                now_local = now_utc.astimezone(user_tz)

                # Get user's preferred email time
                email_time = user.daily_email_time

                # Check if current time matches email time (within a 15-minute window)
                # This allows for some flexibility in cron scheduling
                current_time = now_local.time()
                time_diff = abs(
                    (current_time.hour * 60 + current_time.minute) -
                    (email_time.hour * 60 + email_time.minute)
                )

                if not force and time_diff > 15:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping {user.username}: Not time yet (current: {current_time}, scheduled: {email_time})'
                        )
                    )
                    skipped_count += 1
                    continue

                # Get events from the last 24 hours
                yesterday = now_utc - timedelta(hours=24)
                events = list(NightEvent.objects.filter(
                    user=user,
                    event_datetime__gte=yesterday,
                    event_datetime__lte=now_utc
                ).prefetch_related('event_options').order_by('-event_datetime'))

                # Convert event times to user's timezone
                for event in events:
                    if event.event_datetime:
                        event.event_datetime_local = event.event_datetime.astimezone(user_tz)
                    else:
                        event.event_datetime_local = None

                # Get day note from yesterday (in user's timezone)
                yesterday_date = (now_local - timedelta(days=1)).date()
                day_note = DayNote.objects.filter(
                    user=user,
                    date=yesterday_date
                ).first()

                # Parse recipients
                recipients_str = user.daily_email_recipients.strip()
                if not recipients_str:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping {user.username}: No recipients configured'
                        )
                    )
                    skipped_count += 1
                    continue

                recipients = [email.strip() for email in recipients_str.split(',') if email.strip()]

                if not recipients:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping {user.username}: No valid recipients'
                        )
                    )
                    skipped_count += 1
                    continue

                # Prepare context for email template
                context = {
                    'user': user,
                    'events': events,
                    'day_note': day_note,
                    'yesterday_date': yesterday_date,
                    'event_count': events.count(),
                    'user_tz': user_tz,
                }

                # Render email
                subject = f'Daily Night Summary - {yesterday_date.strftime("%B %d, %Y")}'
                html_content = render_to_string('care_tracking/emails/daily_summary.html', context)
                text_content = strip_tags(html_content)

                # Create email
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=None,  # Use DEFAULT_FROM_EMAIL from settings
                    to=recipients,
                )
                email.attach_alternative(html_content, "text/html")

                # Send email
                email.send()

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Sent email to {user.username} ({len(recipients)} recipient(s)): {", ".join(recipients)}'
                    )
                )
                sent_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error sending email to {user.username}: {str(e)}'
                    )
                )
                error_count += 1

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {sent_count} sent, {skipped_count} skipped, {error_count} errors'
            )
        )
