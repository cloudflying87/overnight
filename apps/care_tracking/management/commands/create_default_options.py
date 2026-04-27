from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.care_tracking.utils import create_default_event_options
from apps.care_tracking.models import EventOption

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates default event options for users who have none'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Create default options for ALL users (even those with existing options)',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Create default options for a specific user',
        )

    def handle(self, *args, **options):
        if options['username']:
            # Create for specific user
            try:
                user = User.objects.get(username=options['username'])
                created = create_default_event_options(user)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created {len(created)} default options for user '{user.username}'"
                    )
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User '{options['username']}' not found")
                )
            return

        # Get users
        if options['all']:
            users = User.objects.all()
        else:
            # Only users with no event options
            users = User.objects.filter(event_options__isnull=True).distinct()

        total_created = 0
        total_users = 0

        for user in users:
            # Skip if user already has options (unless --all flag is used)
            if not options['all'] and EventOption.objects.filter(user=user).exists():
                continue

            created = create_default_event_options(user)
            if created:
                total_created += len(created)
                total_users += 1
                self.stdout.write(
                    f"Created {len(created)} options for {user.username}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTotal: Created {total_created} event options for {total_users} users"
            )
        )
