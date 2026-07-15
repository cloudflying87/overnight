from django.conf import settings
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import timedelta
import pytz
from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    ProfileUpdateForm,
    CustomPasswordChangeForm,
    SettingsForm
)
from apps.care_tracking.models import NightEvent, DayNote


class CustomLoginView(LoginView):
    """Custom login view"""
    template_name = 'registration/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('care_tracking:dashboard')


class CustomLogoutView(LogoutView):
    """Custom logout view"""
    next_page = 'users:login'


class SignUpView(CreateView):
    """User registration view"""
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('users:login')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        """Auto-login user after successful registration and create default event options"""
        response = super().form_valid(form)
        user = form.save()

        # Create default event options for the new user
        from apps.care_tracking.utils import create_default_event_options
        create_default_event_options(user)

        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('care_tracking:dashboard')


@login_required
def profile_view(request):
    """User profile page - update display name, email, and password"""
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, instance=request.user)
            password_form = CustomPasswordChangeForm(request.user)

            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('users:profile')
        elif 'change_password' in request.POST:
            profile_form = ProfileUpdateForm(instance=request.user)
            password_form = CustomPasswordChangeForm(request.user, request.POST)

            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('users:profile')
        else:
            profile_form = ProfileUpdateForm(instance=request.user)
            password_form = CustomPasswordChangeForm(request.user)
    else:
        profile_form = ProfileUpdateForm(instance=request.user)
        password_form = CustomPasswordChangeForm(request.user)

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, 'users/profile.html', context)


@login_required
def settings_view(request):
    """User settings page - timezone and preferences"""
    if request.method == 'POST':
        # Handle settings form submission
        if 'save_settings' in request.POST:
            form = SettingsForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Settings updated successfully!')
                return redirect('users:settings')
        # Handle manual email sending
        elif 'send_email' in request.POST:
            time_range = request.POST.get('time_range', '24h')
            try:
                send_manual_email(request.user, time_range)
                range_text = "all events" if time_range == 'all' else "last 24 hours"
                messages.success(request, f'Email sent successfully with {range_text}!')
            except Exception as e:
                messages.error(request, f'Error sending email: {str(e)}')
            return redirect('users:settings')
    else:
        form = SettingsForm(instance=request.user)

    context = {
        'form': form,
    }
    return render(request, 'users/settings.html', context)


def send_manual_email(user, time_range='24h'):
    """
    Send a manual email summary to the user

    Args:
        user: User object
        time_range: '24h' for last 24 hours, 'all' for all events
    """
    # Check if user has email enabled and recipients configured
    if not user.daily_email_recipients.strip():
        raise ValueError('No email recipients configured. Please add recipients in settings.')

    # Get current time
    now_utc = timezone.now()
    user_tz = pytz.timezone(user.timezone)
    now_local = now_utc.astimezone(user_tz)

    # Get events based on time range
    if time_range == 'all':
        events = list(NightEvent.objects.filter(
            user=user
        ).prefetch_related('event_options').order_by('-event_datetime'))

        # Get the date range for subject
        if events:
            oldest_event = events[-1]
            newest_event = events[0]
            date_range = f"{oldest_event.event_datetime.astimezone(user_tz).strftime('%b %d')} - {newest_event.event_datetime.astimezone(user_tz).strftime('%b %d, %Y')}"
        else:
            date_range = "No Events"
    else:  # 24h
        yesterday = now_utc - timedelta(hours=24)
        events = list(NightEvent.objects.filter(
            user=user,
            event_datetime__gte=yesterday,
            event_datetime__lte=now_utc
        ).prefetch_related('event_options').order_by('-event_datetime'))

        yesterday_date = (now_local - timedelta(days=1)).date()
        date_range = yesterday_date.strftime('%B %d, %Y')

    # Convert event times to user's timezone
    for event in events:
        if event.event_datetime:
            event.event_datetime_local = event.event_datetime.astimezone(user_tz)
        else:
            event.event_datetime_local = None

    # Get day note from yesterday (only for 24h range)
    day_note = None
    if time_range == '24h':
        yesterday_date = (now_local - timedelta(days=1)).date()
        day_note = DayNote.objects.filter(
            user=user,
            date=yesterday_date
        ).first()

    # Parse recipients
    recipients = [email.strip() for email in user.daily_email_recipients.split(',') if email.strip()]

    if not recipients:
        raise ValueError('No valid email recipients found.')

    # Prepare context for email template
    context = {
        'user': user,
        'events': events,
        'day_note': day_note,
        'yesterday_date': (now_local - timedelta(days=1)).date() if time_range == '24h' else None,
        'event_count': len(events),
        'user_tz': user_tz,
        'time_range': time_range,
        'is_manual': True,
        'site_url': settings.SITE_URL,
    }

    # Render email
    if time_range == 'all':
        subject = f'Night Events Summary - All Events ({date_range})'
    else:
        subject = f'Daily Night Summary - {date_range}'

    html_content = render_to_string('care_tracking/emails/daily_summary.html', context)
    text_content = strip_tags(html_content)

    # Create and send email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=None,  # Use DEFAULT_FROM_EMAIL from settings
        to=recipients,
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
