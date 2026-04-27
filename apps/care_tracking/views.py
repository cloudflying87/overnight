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
from datetime import timedelta

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
