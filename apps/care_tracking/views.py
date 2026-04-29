from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, date
import calendar

from .models import EventOption, NightEvent, DayNote
from .forms import EventOptionForm, NightEventForm, DayNoteForm
from .utils import get_user_active_options


class UserOwnsObjectMixin(UserPassesTestMixin):
    """Mixin to ensure user owns the object they're accessing"""

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user


# ============================================================================
# DASHBOARD
# ============================================================================

@login_required
def dashboard_view(request):
    """Main dashboard showing recent activity and quick stats"""

    user = request.user

    # Get recent events (last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_events = NightEvent.objects.filter(
        user=user,
        event_datetime__gte=seven_days_ago
    ).prefetch_related('event_options').order_by('-event_datetime')[:10]

    # Get recent day notes
    recent_notes = DayNote.objects.filter(user=user).order_by('-date')[:5]

    # Quick stats
    total_events = NightEvent.objects.filter(user=user).count()
    total_notes = DayNote.objects.filter(user=user).count()
    active_options = EventOption.objects.filter(user=user, is_active=True).count()

    # Events this week
    week_ago = timezone.now() - timedelta(days=7)
    events_this_week = NightEvent.objects.filter(
        user=user,
        event_datetime__gte=week_ago
    ).count()

    context = {
        'recent_events': recent_events,
        'recent_notes': recent_notes,
        'total_events': total_events,
        'total_notes': total_notes,
        'active_options': active_options,
        'events_this_week': events_this_week,
    }

    return render(request, 'care_tracking/dashboard.html', context)


# ============================================================================
# EVENT OPTIONS VIEWS
# ============================================================================

class EventOptionListView(LoginRequiredMixin, ListView):
    """List all event options for the current user"""
    model = EventOption
    template_name = 'care_tracking/eventoption_list.html'
    context_object_name = 'options'
    paginate_by = 20

    def get_queryset(self):
        return EventOption.objects.filter(user=self.request.user).order_by('name')


class EventOptionCreateView(LoginRequiredMixin, CreateView):
    """Create a new event option"""
    model = EventOption
    form_class = EventOptionForm
    template_name = 'care_tracking/eventoption_form.html'
    success_url = reverse_lazy('care_tracking:eventoption_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, f'Event option "{form.instance.name}" created successfully!')
        return super().form_valid(form)


class EventOptionUpdateView(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
    """Update an existing event option"""
    model = EventOption
    form_class = EventOptionForm
    template_name = 'care_tracking/eventoption_form.html'
    success_url = reverse_lazy('care_tracking:eventoption_list')

    def form_valid(self, form):
        messages.success(self.request, f'Event option "{form.instance.name}" updated successfully!')
        return super().form_valid(form)


class EventOptionDeleteView(LoginRequiredMixin, UserOwnsObjectMixin, DeleteView):
    """Delete an event option"""
    model = EventOption
    template_name = 'care_tracking/eventoption_confirm_delete.html'
    success_url = reverse_lazy('care_tracking:eventoption_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, f'Event option "{self.get_object().name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# NIGHT EVENT VIEWS
# ============================================================================

class NightEventListView(LoginRequiredMixin, ListView):
    """List all night events for the current user"""
    model = NightEvent
    template_name = 'care_tracking/nightevent_list.html'
    context_object_name = 'events'
    paginate_by = 20

    def get_queryset(self):
        queryset = NightEvent.objects.filter(
            user=self.request.user
        ).prefetch_related('event_options').order_by('-event_datetime')

        # Filter by date if provided
        date = self.request.GET.get('date')
        if date:
            queryset = queryset.filter(event_datetime__date=date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_date'] = self.request.GET.get('date', '')
        return context


class NightEventCreateView(LoginRequiredMixin, CreateView):
    """Create a new night event"""
    model = NightEvent
    form_class = NightEventForm
    template_name = 'care_tracking/nightevent_form.html'
    success_url = reverse_lazy('care_tracking:nightevent_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Night event logged successfully!')
        return super().form_valid(form)


class NightEventUpdateView(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
    """Update an existing night event"""
    model = NightEvent
    form_class = NightEventForm
    template_name = 'care_tracking/nightevent_form.html'
    success_url = reverse_lazy('care_tracking:nightevent_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object and self.object.event_datetime:
            user_tz = pytz.timezone(self.request.user.timezone)
            local_dt = self.object.event_datetime.astimezone(user_tz)
            context['local_event_datetime'] = local_dt.strftime('%Y-%m-%dT%H:%M')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Night event updated successfully!')
        return super().form_valid(form)


class NightEventDeleteView(LoginRequiredMixin, UserOwnsObjectMixin, DeleteView):
    """Delete a night event"""
    model = NightEvent
    template_name = 'care_tracking/nightevent_confirm_delete.html'
    success_url = reverse_lazy('care_tracking:nightevent_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Night event deleted successfully!')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# DAY NOTE VIEWS
# ============================================================================

class DayNoteListView(LoginRequiredMixin, ListView):
    """List all day notes for the current user"""
    model = DayNote
    template_name = 'care_tracking/daynote_list.html'
    context_object_name = 'notes'
    paginate_by = 20

    def get_queryset(self):
        return DayNote.objects.filter(user=self.request.user).order_by('-date')


class DayNoteCreateView(LoginRequiredMixin, CreateView):
    """Create a new day note"""
    model = DayNote
    form_class = DayNoteForm
    template_name = 'care_tracking/daynote_form.html'

    def get_initial(self):
        """Pre-fill date if provided in query params"""
        initial = super().get_initial()
        date_str = self.request.GET.get('date')
        if date_str:
            try:
                initial['date'] = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        return initial

    def get_success_url(self):
        """Redirect back to day view if date was provided"""
        date_str = self.request.GET.get('date')
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                return reverse_lazy('care_tracking:day_view', kwargs={
                    'year': date_obj.year,
                    'month': date_obj.month,
                    'day': date_obj.day
                })
            except ValueError:
                pass
        return reverse_lazy('care_tracking:daynote_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Day note created successfully!')
        return super().form_valid(form)


class DayNoteUpdateView(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
    """Update an existing day note"""
    model = DayNote
    form_class = DayNoteForm
    template_name = 'care_tracking/daynote_form.html'

    def get_success_url(self):
        """Redirect back to day view"""
        day_note = self.get_object()
        return reverse_lazy('care_tracking:day_view', kwargs={
            'year': day_note.date.year,
            'month': day_note.date.month,
            'day': day_note.date.day
        })

    def form_valid(self, form):
        messages.success(self.request, 'Day note updated successfully!')
        return super().form_valid(form)


class DayNoteDeleteView(LoginRequiredMixin, UserOwnsObjectMixin, DeleteView):
    """Delete a day note"""
    model = DayNote
    template_name = 'care_tracking/daynote_confirm_delete.html'
    success_url = reverse_lazy('care_tracking:daynote_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Day note deleted successfully!')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# CALENDAR VIEW
# ============================================================================

@login_required
def calendar_view(request):
    """Calendar view showing which days have events"""
    import pytz
    from datetime import datetime

    # Get year and month from query params, default to current
    user_tz = pytz.timezone(request.user.timezone)
    now_utc = timezone.now()
    now_local = now_utc.astimezone(user_tz)
    today = now_local.date()

    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    # Create calendar with Sunday as first day (6 = Sunday in Python's calendar)
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(year, month)

    # Get days with events for this month
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1)
    else:
        month_end = date(year, month + 1, 1)

    # Get dates with night events
    if request.user.group_night_events:
        # When grouping by night, map events to their night start date
        # A night starts at 5 PM and ends at 10 AM next day
        # Events before 10 AM belong to previous day's night
        events = NightEvent.objects.filter(
            user=request.user,
            event_datetime__date__gte=month_start - timedelta(days=1),  # Include previous day for early AM events
            event_datetime__date__lt=month_end
        ).select_related('user')

        event_days = set()
        for event in events:
            event_local = event.event_datetime.astimezone(user_tz)
            event_hour = event_local.hour
            event_date = event_local.date()

            # Determine which date to show this event on
            if event_hour < 10:
                # Before 10 AM - belongs to previous day's night
                display_date = event_date - timedelta(days=1)
            elif event_hour >= 17:
                # 5 PM or later - belongs to today's night
                display_date = event_date
            else:
                # 10 AM to 4:59 PM - daytime event, show on regular date
                display_date = event_date

            # Only show nights that have started
            # If it's today and we haven't reached 5 PM yet, don't show today's night
            # (but do show daytime events for today)
            if display_date == today:
                if event_hour >= 17 or event_hour < 10:
                    # This is a night event
                    if now_local.hour < 17:
                        # Night hasn't started yet
                        continue

            # Only include days in current month
            if month_start <= display_date < month_end:
                event_days.add(display_date.day)
    else:
        # Regular calendar view - show events by their date
        event_dates_raw = NightEvent.objects.filter(
            user=request.user,
            event_datetime__date__gte=month_start,
            event_datetime__date__lt=month_end
        ).values_list('event_datetime__date', flat=True)
        event_days = set(d.day for d in event_dates_raw)

    # Get dates with day notes (as day numbers)
    note_dates_raw = DayNote.objects.filter(
        user=request.user,
        date__gte=month_start,
        date__lt=month_end
    ).values_list('date', flat=True)
    note_days = set(d.day for d in note_dates_raw)

    # Calculate previous and next month
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    context = {
        'calendar': cal,
        'month': month,
        'year': year,
        'month_name': calendar.month_name[month],
        'event_days': event_days,
        'note_days': note_days,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'today': today,
    }

    return render(request, 'care_tracking/calendar.html', context)


@login_required
def day_view(request, year, month, day):
    """View all events and notes for a specific day"""
    import pytz
    from datetime import datetime

    selected_date = date(year, month, day)
    user_tz = pytz.timezone(request.user.timezone)

    # Check if user wants to group by night (5pm-10am)
    if request.user.group_night_events:
        # Night starts at 5pm on selected_date and ends at 10am next day
        night_start = user_tz.localize(datetime.combine(selected_date, datetime.min.time().replace(hour=17, minute=0, second=0)))
        night_end = night_start + timedelta(hours=17)  # 10am next day
        next_date = selected_date + timedelta(days=1)

        # Convert to UTC for database query
        night_start_utc = night_start.astimezone(pytz.UTC)
        night_end_utc = night_end.astimezone(pytz.UTC)

        events = NightEvent.objects.filter(
            user=request.user,
            event_datetime__gte=night_start_utc,
            event_datetime__lt=night_end_utc
        ).prefetch_related('event_options').order_by('event_datetime')

        # Show date range spanning both days
        if selected_date.month == next_date.month:
            date_range_label = f"Night of {selected_date.strftime('%b %d')}-{next_date.strftime('%d, %Y')} (5 PM - 10 AM)"
        else:
            date_range_label = f"Night of {selected_date.strftime('%b %d')} - {next_date.strftime('%b %d, %Y')} (5 PM - 10 AM)"
    else:
        # Regular calendar day view
        events = NightEvent.objects.filter(
            user=request.user,
            event_datetime__date=selected_date
        ).prefetch_related('event_options').order_by('event_datetime')

        date_range_label = selected_date.strftime('%B %d, %Y')

    # Get day note for this day
    try:
        day_note = DayNote.objects.get(user=request.user, date=selected_date)
    except DayNote.DoesNotExist:
        day_note = None

    context = {
        'selected_date': selected_date,
        'events': events,
        'day_note': day_note,
        'date_range_label': date_range_label,
        'is_night_view': request.user.group_night_events,
    }

    return render(request, 'care_tracking/day_view.html', context)

# ============================================================================
# TRENDS / ANALYTICS
# ============================================================================

def send_filtered_email(user, start_date_str, end_date_str, event_type_filter='', email_format='summary'):
    """
    Send filtered email with events from trends page

    Args:
        user: User object
        start_date_str: Start date in YYYY-MM-DD format
        end_date_str: End date in YYYY-MM-DD format
        event_type_filter: Optional event type filter
        email_format: 'summary' (count only), 'daily' (grouped by day), or 'detailed' (all events)
    """
    import pytz
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from datetime import datetime

    # Check if user has email recipients
    if not user.daily_email_recipients.strip():
        raise ValueError('No email recipients configured. Please add recipients in settings.')

    # Parse date strings
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Get user's timezone
    user_tz = pytz.timezone(user.timezone)

    # Query events
    events = list(NightEvent.objects.filter(
        user=user,
        event_datetime__date__gte=start_date,
        event_datetime__date__lte=end_date
    ).prefetch_related('event_options').order_by('-event_datetime'))

    # Apply event type filter if specified
    if event_type_filter:
        events = [e for e in events if any(opt.name == event_type_filter for opt in e.event_options.all())]

    # Convert event times to user's timezone
    for event in events:
        if event.event_datetime:
            event.event_datetime_local = event.event_datetime.astimezone(user_tz)
        else:
            event.event_datetime_local = None

    # Parse recipients
    recipients = [email.strip() for email in user.daily_email_recipients.split(',') if email.strip()]

    if not recipients:
        raise ValueError('No valid email recipients found.')

    # Prepare context
    date_range = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"

    # For daily format, group events by day
    daily_data = []
    if email_format == 'daily':
        from collections import defaultdict
        events_by_date = defaultdict(list)

        for event in events:
            event_date = event.event_datetime_local.date()
            events_by_date[event_date].append(event)

        # Build daily summary
        current_date = start_date
        while current_date <= end_date:
            date_events = events_by_date.get(current_date, [])

            # Count events by type
            event_type_counts = defaultdict(int)
            for event in date_events:
                for option in event.event_options.all():
                    event_type_counts[option.name] += 1

            daily_data.append({
                'date': current_date,
                'event_count': len(date_events),
                'event_types': dict(event_type_counts),
            })
            current_date += timedelta(days=1)

    context = {
        'user': user,
        'events': events,
        'event_count': len(events),
        'user_tz': user_tz,
        'start_date': start_date,
        'end_date': end_date,
        'date_range': date_range,
        'event_type_filter': event_type_filter,
        'email_format': email_format,
        'is_filtered': bool(event_type_filter),
        'daily_data': daily_data,  # For daily format
    }

    # Build subject based on format
    if email_format == 'daily':
        format_label = 'Daily Summary'
    elif email_format == 'detailed':
        format_label = 'Detailed Report'
    else:  # summary
        format_label = 'Summary'

    if event_type_filter:
        subject = f'Night Events {format_label}: {event_type_filter} ({date_range})'
    else:
        subject = f'Night Events {format_label} ({date_range})'

    # Render email
    html_content = render_to_string('care_tracking/emails/filtered_summary.html', context)
    text_content = strip_tags(html_content)

    # Create and send email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=None,
        to=recipients,
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


@login_required
def trends_view(request):
    """View trends and analytics for night events"""
    import pytz
    from collections import defaultdict
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from datetime import datetime

    # Handle email sending action
    if request.method == 'POST' and 'send_email' in request.POST:
        email_format = request.POST.get('email_format', 'summary')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        event_type_filter = request.POST.get('event_type', '')

        try:
            from apps.users.views import send_manual_email
            # Use a modified version that accepts date range and filter
            send_filtered_email(request.user, start_date_str, end_date_str, event_type_filter, email_format)
            messages.success(request, f'Email sent successfully with {email_format} format!')
        except Exception as e:
            messages.error(request, f'Error sending email: {str(e)}')

        # Redirect to same page with filters preserved
        return redirect(f"{request.path}?start_date={start_date_str}&end_date={end_date_str}&event_type={event_type_filter}")

    # Get filter params from query
    days = request.GET.get('days', '')
    event_type_filter = request.GET.get('event_type', '')
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')

    # Get user's timezone
    user_tz = pytz.timezone(request.user.timezone)
    now_utc = timezone.now()
    now_local = now_utc.astimezone(user_tz)

    # Calculate date range based on input
    if start_date_str and end_date_str:
        # Custom date range
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        days = (end_date - start_date).days + 1
    elif days:
        # Preset days
        days = int(days)
        end_date = now_local.date()
        start_date = end_date - timedelta(days=days - 1)
    else:
        # Default to 30 days
        days = 30
        end_date = now_local.date()
        start_date = end_date - timedelta(days=days - 1)

    # Get all events in date range
    events = NightEvent.objects.filter(
        user=request.user,
        event_datetime__date__gte=start_date,
        event_datetime__date__lte=end_date
    ).prefetch_related('event_options')

    # Apply event type filter if specified
    if event_type_filter:
        events = events.filter(event_options__name=event_type_filter).distinct()

    # Get all unique event types for filter dropdown
    all_event_types_for_filter = EventOption.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('name').values_list('name', flat=True)
    
    # Group events by night (night starts at 10 PM; events before 8 AM belong to previous evening)
    events_by_night = defaultdict(list)
    for event in events:
        event_local = event.event_datetime.astimezone(user_tz)
        hour = event_local.hour
        event_date = event_local.date()
        night_start = event_date - timedelta(days=1) if hour < 8 else event_date
        events_by_night[night_start].append(event)

    # Build nightly summary data
    daily_data = []
    for i in range(days):
        night_start = start_date + timedelta(days=i)
        night_end = night_start + timedelta(days=1)
        night_events = events_by_night.get(night_start, [])

        event_type_counts = defaultdict(int)
        for event in night_events:
            for option in event.event_options.all():
                event_type_counts[option.name] += 1

        daily_data.append({
            'date': night_start,
            'night_end': night_end,
            'event_count': len(night_events),
            'events': night_events,
            'event_types': dict(event_type_counts),
            'has_note': DayNote.objects.filter(user=request.user, date=night_start).exists(),
        })

    # Reverse so newest is first
    daily_data.reverse()
    
    # Calculate statistics
    event_counts = [d['event_count'] for d in daily_data]
    total_events = sum(event_counts)
    days_with_events = sum(1 for count in event_counts if count > 0)
    avg_events_per_night = total_events / days if days > 0 else 0
    avg_events_on_active_nights = total_events / days_with_events if days_with_events > 0 else 0
    max_events_in_night = max(event_counts) if event_counts else 0
    
    # Find most common event types
    all_event_types = defaultdict(int)
    for day_data in daily_data:
        for event_type, count in day_data['event_types'].items():
            all_event_types[event_type] += count
    
    # Sort by count descending
    top_event_types = sorted(all_event_types.items(), key=lambda x: x[1], reverse=True)[:5]

    # Analyze time of day patterns
    events_by_hour = defaultdict(list)  # Store actual events, not just counts
    event_types_by_hour = defaultdict(lambda: defaultdict(int))  # Track event types per hour

    for event in events:
        event_local = event.event_datetime.astimezone(user_tz)
        hour = event_local.hour
        event.event_datetime_local = event_local  # Store for template use
        events_by_hour[hour].append(event)

        # Count event types for this hour
        for option in event.event_options.all():
            event_types_by_hour[hour][option.name] += 1

    # Create time blocks data (hourly breakdown)
    time_blocks = []
    for hour in range(24):
        hour_events = events_by_hour.get(hour, [])
        count = len(hour_events)

        # Format hour for display
        if hour == 0:
            time_label = "12 AM"
        elif hour < 12:
            time_label = f"{hour} AM"
        elif hour == 12:
            time_label = "12 PM"
        else:
            time_label = f"{hour - 12} PM"

        # Get top event types for this hour (up to 3)
        hour_event_types = sorted(
            event_types_by_hour[hour].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        time_blocks.append({
            'hour': hour,
            'label': time_label,
            'count': count,
            'percentage': (count / total_events * 100) if total_events > 0 else 0,
            'events': hour_events,
            'event_types': hour_event_types,  # [(type_name, count), ...]
        })

    # Find peak hours (top 3)
    peak_hours = sorted(time_blocks, key=lambda x: x['count'], reverse=True)[:3]
    peak_hours = [h for h in peak_hours if h['count'] > 0]  # Only include hours with events

    # Analyze half-hour patterns for more granular view
    events_by_half_hour = defaultdict(list)
    event_types_by_half_hour = defaultdict(lambda: defaultdict(int))

    for event in events:
        event_local = event.event_datetime.astimezone(user_tz)
        hour = event_local.hour
        minute = event_local.minute

        # Determine which half hour: 0 = :00-:29, 1 = :30-:59
        half_hour_index = (hour * 2) + (1 if minute >= 30 else 0)

        events_by_half_hour[half_hour_index].append(event)

        # Count event types for this half hour
        for option in event.event_options.all():
            event_types_by_half_hour[half_hour_index][option.name] += 1

    # Create half-hour blocks data
    half_hour_blocks = []
    for i in range(48):  # 24 hours * 2 half-hours
        hour = i // 2
        is_second_half = i % 2 == 1

        # Format time label
        if hour == 0:
            hour_label = "12"
            period = "AM"
        elif hour < 12:
            hour_label = str(hour)
            period = "AM"
        elif hour == 12:
            hour_label = "12"
            period = "PM"
        else:
            hour_label = str(hour - 12)
            period = "PM"

        if is_second_half:
            time_label = f"{hour_label}:30 {period}"
        else:
            time_label = f"{hour_label}:00 {period}"

        half_hour_events = events_by_half_hour.get(i, [])
        count = len(half_hour_events)

        # Get top event types for this half hour (up to 3)
        half_hour_event_types = sorted(
            event_types_by_half_hour[i].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        half_hour_blocks.append({
            'index': i,
            'hour': hour,
            'is_second_half': is_second_half,
            'label': time_label,
            'count': count,
            'percentage': (count / total_events * 100) if total_events > 0 else 0,
            'events': half_hour_events,
            'event_types': half_hour_event_types,
        })

    context = {
        'daily_data': daily_data,
        'days': days if not (start_date_str and end_date_str) else '',
        'start_date': start_date,
        'end_date': end_date,
        'start_date_str': start_date.strftime('%Y-%m-%d'),
        'end_date_str': end_date.strftime('%Y-%m-%d'),
        'stats': {
            'total_events': total_events,
            'days_with_events': days_with_events,
            'avg_events_per_night': round(avg_events_per_night, 1),
            'avg_events_on_active_nights': round(avg_events_on_active_nights, 1),
            'max_events_in_night': max_events_in_night,
        },
        'top_event_types': top_event_types,
        'time_blocks': time_blocks,
        'half_hour_blocks': half_hour_blocks,
        'peak_hours': peak_hours,
        'event_type_filter': event_type_filter,
        'all_event_types_for_filter': all_event_types_for_filter,
        'is_custom_range': bool(start_date_str and end_date_str),
    }
    
    return render(request, 'care_tracking/trends.html', context)


@login_required
def export_events_csv(request):
    """Export events to CSV format"""
    import csv
    from django.http import HttpResponse
    import pytz
    from datetime import datetime

    # Get filters from query params
    event_type_filter = request.GET.get('event_type', '')
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')

    # Get user's timezone
    user_tz = pytz.timezone(request.user.timezone)
    now_utc = timezone.now()
    now_local = now_utc.astimezone(user_tz)

    # Calculate date range based on input
    if start_date_str and end_date_str:
        # Custom date range
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        # Default to 30 days
        days = int(request.GET.get('days', 30))
        end_date = now_local.date()
        start_date = end_date - timedelta(days=days - 1)

    # Query events
    events = NightEvent.objects.filter(
        user=request.user,
        event_datetime__date__gte=start_date,
        event_datetime__date__lte=end_date
    ).prefetch_related('event_options').order_by('-event_datetime')

    # Filter by event type if specified
    if event_type_filter:
        events = events.filter(event_options__name=event_type_filter)

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="night_events_{start_date}_{end_date}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Time', 'Event Types', 'Notes'])

    for event in events:
        event_local = event.event_datetime.astimezone(user_tz)
        event_types = ', '.join([opt.name for opt in event.event_options.all()])

        writer.writerow([
            event_local.strftime('%Y-%m-%d'),
            event_local.strftime('%I:%M %p'),
            event_types,
            event.notes or ''
        ])

    return response
