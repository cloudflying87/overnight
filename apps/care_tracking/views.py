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
    # Get year and month from query params, default to current
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    # Create calendar
    cal = calendar.monthcalendar(year, month)

    # Get days with events for this month
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1)
    else:
        month_end = date(year, month + 1, 1)

    # Get dates with night events (as day numbers)
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
    selected_date = date(year, month, day)

    # Get all events for this day
    events = NightEvent.objects.filter(
        user=request.user,
        event_datetime__date=selected_date
    ).prefetch_related('event_options').order_by('event_datetime')

    # Get day note for this day
    try:
        day_note = DayNote.objects.get(user=request.user, date=selected_date)
    except DayNote.DoesNotExist:
        day_note = None

    context = {
        'selected_date': selected_date,
        'events': events,
        'day_note': day_note,
    }

    return render(request, 'care_tracking/day_view.html', context)

# ============================================================================
# TRENDS / ANALYTICS
# ============================================================================

@login_required
def trends_view(request):
    """View trends and analytics for night events"""
    import pytz
    from collections import defaultdict
    
    # Get date range from query params (default to last 30 days)
    days = int(request.GET.get('days', 30))
    
    # Get user's timezone
    user_tz = pytz.timezone(request.user.timezone)
    now_utc = timezone.now()
    now_local = now_utc.astimezone(user_tz)
    
    # Calculate date range
    end_date = now_local.date()
    start_date = end_date - timedelta(days=days - 1)
    
    # Get all events in date range
    events = NightEvent.objects.filter(
        user=request.user,
        event_datetime__date__gte=start_date,
        event_datetime__date__lte=end_date
    ).prefetch_related('event_options')
    
    # Group events by date (in user's timezone)
    events_by_date = defaultdict(list)
    for event in events:
        event_local = event.event_datetime.astimezone(user_tz)
        event_date = event_local.date()
        events_by_date[event_date].append(event)
    
    # Build daily summary data
    daily_data = []
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        date_events = events_by_date.get(current_date, [])
        
        # Count events by type
        event_type_counts = defaultdict(int)
        for event in date_events:
            for option in event.event_options.all():
                event_type_counts[option.name] += 1
        
        daily_data.append({
            'date': current_date,
            'event_count': len(date_events),
            'events': date_events,
            'event_types': dict(event_type_counts),
            'has_note': DayNote.objects.filter(user=request.user, date=current_date).exists(),
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
    
    context = {
        'daily_data': daily_data,
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
        'stats': {
            'total_events': total_events,
            'days_with_events': days_with_events,
            'avg_events_per_night': round(avg_events_per_night, 1),
            'avg_events_on_active_nights': round(avg_events_on_active_nights, 1),
            'max_events_in_night': max_events_in_night,
        },
        'top_event_types': top_event_types,
    }
    
    return render(request, 'care_tracking/trends.html', context)
