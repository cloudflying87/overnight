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
    success_url = reverse_lazy('care_tracking:daynote_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Day note created successfully!')
        return super().form_valid(form)


class DayNoteUpdateView(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
    """Update an existing day note"""
    model = DayNote
    form_class = DayNoteForm
    template_name = 'care_tracking/daynote_form.html'
    success_url = reverse_lazy('care_tracking:daynote_list')

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

    # Get dates with night events
    event_dates = set(
        NightEvent.objects.filter(
            user=request.user,
            event_datetime__date__gte=month_start,
            event_datetime__date__lt=month_end
        ).values_list('event_datetime__date', flat=True)
    )

    # Get dates with day notes
    note_dates = set(
        DayNote.objects.filter(
            user=request.user,
            date__gte=month_start,
            date__lt=month_end
        ).values_list('date', flat=True)
    )

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
        'event_dates': event_dates,
        'note_dates': note_dates,
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
