"""
Management command to send daily email summaries to users.
Run this command daily (via cron) to send email summaries.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.users.models import User
from apps.care_tracking.email_utils import send_nightly_summary, parse_recipients
import pytz


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
                today_local = now_local.date()

                # Skip if we already sent today's summary (prevents duplicate
                # sends when the cron runs multiple times inside the time
                # window). --force overrides this for testing.
                if not force and user.daily_email_last_sent == today_local:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping {user.username}: Already sent today ({today_local})'
                        )
                    )
                    skipped_count += 1
                    continue

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

                # Must have recipients configured before we do anything else.
                recipients = parse_recipients(user)
                if not recipients:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping {user.username}: No recipients configured'
                        )
                    )
                    skipped_count += 1
                    continue

                # Build and send the night summary. Only send when the night
                # actually has something to report (--force overrides this so
                # you can test even on a quiet night).
                sent = send_nightly_summary(
                    user,
                    recipients=recipients,
                    skip_if_empty=not force,
                )

                if not sent:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping {user.username}: Nothing logged overnight'
                        )
                    )
                    skipped_count += 1
                    continue

                # Record that today's summary went out so we don't resend it
                # on the next cron run within the window.
                user.daily_email_last_sent = today_local
                user.save(update_fields=['daily_email_last_sent'])

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
