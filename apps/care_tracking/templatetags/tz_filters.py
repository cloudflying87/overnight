from django import template
from django.utils import timezone
import pytz

register = template.Library()


@register.filter
def user_timezone(value, user):
    """
    Convert a datetime to the user's timezone.
    Usage: {{ event.event_datetime|user_timezone:user }}
    """
    if not value:
        return value

    if not user or not hasattr(user, 'timezone'):
        return value

    try:
        # Get user's timezone
        user_tz = pytz.timezone(user.timezone)

        # If the datetime is naive, make it aware in UTC
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.utc)

        # Convert to user's timezone
        return value.astimezone(user_tz)
    except Exception:
        # If anything goes wrong, return the original value
        return value
