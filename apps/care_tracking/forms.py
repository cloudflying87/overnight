from django import forms
from django.utils import timezone
import pytz
from .models import EventOption, NightEvent, DayNote


class EventOptionForm(forms.ModelForm):
    """Form for creating/editing event options"""

    class Meta:
        model = EventOption
        fields = ['name', 'description', 'color_code', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Event name (e.g., "Underwear change")'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Optional description',
                'rows': 3
            }),
            'color_code': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#3B82F6'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Event Name',
            'description': 'Description',
            'color_code': 'Color (for charts)',
            'is_active': 'Active'
        }


class NightEventForm(forms.ModelForm):
    """Form for logging night events"""

    class Meta:
        model = NightEvent
        fields = ['event_options', 'notes', 'event_datetime']
        widgets = {
            'event_options': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Optional notes about this event...',
                'rows': 4
            }),
            'event_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }
        labels = {
            'event_options': 'What happened? (Select all that apply)',
            'notes': 'Additional Notes',
            'event_datetime': 'When did this happen?'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Only show active event options for the current user
        if user:
            self.fields['event_options'].queryset = EventOption.objects.filter(
                user=user,
                is_active=True
            ).order_by('name')

            # Convert datetime to user's timezone for display
            user_tz = pytz.timezone(user.timezone)

            # Set default datetime to now in user's timezone if creating new
            if not self.instance.pk:
                now_utc = timezone.now()
                now_local = now_utc.astimezone(user_tz)
                self.initial['event_datetime'] = now_local.strftime('%Y-%m-%dT%H:%M')
            # If editing existing event, convert stored UTC time to user's timezone
            elif self.instance.event_datetime:
                event_local = self.instance.event_datetime.astimezone(user_tz)
                self.initial['event_datetime'] = event_local.strftime('%Y-%m-%dT%H:%M')

        # Store user for later use in clean
        self.user = user

    def clean_event_datetime(self):
        """Convert naive datetime from user's timezone to UTC"""
        event_datetime = self.cleaned_data.get('event_datetime')

        if event_datetime and self.user:
            # The datetime from the form is naive (no timezone)
            # It represents the user's local time
            user_tz = pytz.timezone(self.user.timezone)

            # Make it aware in the user's timezone
            if timezone.is_naive(event_datetime):
                local_dt = user_tz.localize(event_datetime)
                # Convert to UTC for storage
                utc_dt = local_dt.astimezone(pytz.UTC)
                return utc_dt

        return event_datetime


class DayNoteForm(forms.ModelForm):
    """Form for creating/editing day notes"""

    class Meta:
        model = DayNote
        fields = ['date', 'content']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Notes about today... (activities, diet, mood, etc.)',
                'rows': 5
            })
        }
        labels = {
            'date': 'Date',
            'content': 'Day Notes'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set default date to today if not provided
        if not self.instance.pk:
            self.initial['date'] = timezone.now().date()


class DateRangeForm(forms.Form):
    """Form for filtering by date range (for trends)"""

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='From'
    )

    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='To'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set default to last 30 days
        if not self.is_bound:
            end = timezone.now().date()
            start = end - timezone.timedelta(days=30)
            self.initial['start_date'] = start
            self.initial['end_date'] = end

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date must be before end date")

        return cleaned_data
