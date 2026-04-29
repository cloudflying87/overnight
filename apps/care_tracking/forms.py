from django import forms
from django.utils import timezone
import pytz
import datetime
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

    # Declared as CharField so Django never touches timezone conversion.
    # We handle display (local→string in __init__) and saving (string→UTC
    # in clean_event_datetime) entirely ourselves.
    event_datetime = forms.CharField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
        }),
        label='When did this happen?',
    )

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
        }
        labels = {
            'event_options': 'What happened? (Select all that apply)',
            'notes': 'Additional Notes',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['event_options'].queryset = EventOption.objects.filter(
                user=user,
                is_active=True
            ).order_by('name')

            user_tz = pytz.timezone(user.timezone)

            if not self.instance.pk:
                local_str = timezone.now().astimezone(user_tz).strftime('%Y-%m-%dT%H:%M')
            elif self.instance.event_datetime:
                local_str = self.instance.event_datetime.astimezone(user_tz).strftime('%Y-%m-%dT%H:%M')
            else:
                local_str = ''

            self.initial['event_datetime'] = local_str

        self.user = user

    def clean_event_datetime(self):
        """Parse the local datetime string and convert to UTC for storage."""
        value = self.cleaned_data.get('event_datetime')
        if value and self.user:
            user_tz = pytz.timezone(self.user.timezone)
            try:
                naive_dt = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M')
            except ValueError:
                raise forms.ValidationError('Enter a valid date and time.')
            return user_tz.localize(naive_dt).astimezone(pytz.UTC)
        return value


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
