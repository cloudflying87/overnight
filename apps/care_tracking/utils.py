"""
Utility functions for care tracking app
"""
from .models import EventOption, CareShare

# Session key holding the id of the user whose records are being viewed.
SUBJECT_SESSION_KEY = 'viewing_subject_id'


# Default event options to create for new users
DEFAULT_EVENT_OPTIONS = [
    {'name': 'Underwear change', 'color_code': '#FF6B6B'},
    {'name': 'Underwear/Clothes wet', 'color_code': '#4ECDC4'},
    {'name': 'Bed clothes wet', 'color_code': '#45B7D1'},
    {'name': 'Sheets rearranged', 'color_code': '#FFA07A'},
    {'name': 'Sheets changed', 'color_code': '#98D8C8'},
    {'name': 'Need to pee', 'color_code': '#F7DC6F'},
    {'name': 'Active Sleeping', 'color_code': '#BB8FCE'},
    {'name': 'Settled Sleeping', 'color_code': '#85C1E2'},
    {'name': 'Moving around the mattresses/room', 'color_code': '#F8B739'},
    {'name': "PJ's Top and/or Bottom off", 'color_code': '#52B788'},
]


def create_default_event_options(user):
    """
    Create default event options for a new user.

    Args:
        user: User instance

    Returns:
        list: Created EventOption instances
    """
    created_options = []

    for option_data in DEFAULT_EVENT_OPTIONS:
        option, created = EventOption.objects.get_or_create(
            user=user,
            name=option_data['name'],
            defaults={
                'color_code': option_data['color_code'],
                'is_active': True
            }
        )
        if created:
            created_options.append(option)

    return created_options


def get_user_active_options(user):
    """
    Get all active event options for a user.

    Args:
        user: User instance

    Returns:
        QuerySet: Active EventOption instances
    """
    return EventOption.objects.filter(user=user, is_active=True).order_by('name')


def get_shared_owners(user):
    """
    Users who have shared their records (read-only) with ``user``.

    Returns:
        QuerySet of User, ordered by display name then username.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.filter(
        shares_given__viewer=user
    ).distinct().order_by('display_name', 'username')


def resolve_subject(request):
    """
    Determine whose records the current request should display.

    Returns ``(subject_user, is_owner)``:
      - the logged-in user themselves (is_owner=True) by default, or
      - a shared owner the user has selected (is_owner=False), validated
        against the set of owners who have actually shared with them.

    An invalid or stale session selection silently falls back to self.
    """
    user = request.user
    subject_id = request.session.get(SUBJECT_SESSION_KEY)

    if subject_id and subject_id != user.id:
        owner = get_shared_owners(user).filter(id=subject_id).first()
        if owner is not None:
            return owner, False
        # Stale/invalid selection — clear it.
        request.session.pop(SUBJECT_SESSION_KEY, None)

    return user, True
