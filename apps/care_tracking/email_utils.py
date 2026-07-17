"""
Helpers for building and sending the nightly summary email.

A "night" runs from 5 PM on its date to 10 AM the next morning (matching the
group-by-night behaviour in the calendar/day views). The summary reports the
night that most recently ended relative to "now", so a morning send covers the
previous evening through this morning.
"""
from datetime import datetime, time, timedelta
import pytz

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from .models import NightEvent, DayNote

# Night window boundaries (local time, 24h clock).
NIGHT_START_HOUR = 17  # 5 PM
NIGHT_END_HOUR = 10    # 10 AM next day


def build_nightly_summary_context(user):
    """
    Gather the events and day note for the night that most recently ended for
    ``user`` and return the template context for the summary email.
    """
    user_tz = pytz.timezone(user.timezone)
    now_utc = timezone.now()
    now_local = now_utc.astimezone(user_tz)

    # The night that just ended started yesterday evening.
    night_date = now_local.date() - timedelta(days=1)
    night_start_local = user_tz.localize(
        datetime.combine(night_date, time(NIGHT_START_HOUR, 0))
    )
    night_end_local = user_tz.localize(
        datetime.combine(night_date + timedelta(days=1), time(NIGHT_END_HOUR, 0))
    )
    night_start_utc = night_start_local.astimezone(pytz.UTC)
    night_end_utc = night_end_local.astimezone(pytz.UTC)
    # Never look past "now" (the tail of the window may still be in the future
    # when the email is sent before 10 AM).
    upper_utc = min(now_utc, night_end_utc)

    events = list(NightEvent.objects.filter(
        user=user,
        event_datetime__gte=night_start_utc,
        event_datetime__lte=upper_utc,
    ).prefetch_related('event_options').order_by('-event_datetime'))

    for event in events:
        if event.event_datetime:
            event.event_datetime_local = event.event_datetime.astimezone(user_tz)
        else:
            event.event_datetime_local = None

    day_note = DayNote.objects.filter(user=user, date=night_date).first()

    return {
        'user': user,
        'events': events,
        'day_note': day_note,
        'yesterday_date': night_date,
        'event_count': len(events),
        'user_tz': user_tz,
        'site_url': settings.SITE_URL,
        'night_start_local': night_start_local,
        'night_end_local': night_end_local,
    }


def has_night_content(context):
    """True if the night has any events or a day note worth emailing."""
    return bool(context['events']) or bool(context['day_note'])


def parse_recipients(user):
    """Return the user's configured recipient list (may be empty)."""
    return [email.strip() for email in user.daily_email_recipients.split(',') if email.strip()]


def send_nightly_summary(user, recipients=None, skip_if_empty=True):
    """
    Build and send the nightly summary email for ``user``.

    Args:
        user: the User whose night is summarised.
        recipients: explicit recipient list; defaults to the user's configured
            recipients. (The test button passes ``[user.email]`` to send only
            to the caller.)
        skip_if_empty: when True, don't send if the night has no events or note.

    Returns:
        True if an email was sent, False if it was skipped because the night
        was empty. Raises ValueError if there are no recipients.
    """
    context = build_nightly_summary_context(user)

    if skip_if_empty and not has_night_content(context):
        return False

    if recipients is None:
        recipients = parse_recipients(user)
    if not recipients:
        raise ValueError('No email recipients configured. Please add recipients in settings.')

    night_date = context['yesterday_date']
    subject = f'Nightly Summary - {night_date.strftime("%B %d, %Y")}'
    html_content = render_to_string('care_tracking/emails/daily_summary.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=None,  # Use DEFAULT_FROM_EMAIL from settings
        to=recipients,
    )
    email.attach_alternative(html_content, 'text/html')
    email.send()
    return True
