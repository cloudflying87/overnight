from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from .models import User
import pytz


class CustomUserCreationForm(UserCreationForm):
    """Custom form for user registration"""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )

    display_name = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Display Name (optional)'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'display_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form with Bootstrap styling"""

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""

    class Meta:
        model = User
        fields = ('display_name', 'email')
        widgets = {
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'How you want to be called'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com'
            }),
        }
        labels = {
            'display_name': 'Display Name',
            'email': 'Email Address',
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with Bootstrap styling"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Current Password'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'New Password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm New Password'
        })


class SettingsForm(forms.ModelForm):
    """Form for user settings"""

    class Meta:
        model = User
        fields = ('timezone', 'group_night_events', 'daily_email_enabled', 'daily_email_time', 'daily_email_recipients')
        widgets = {
            'timezone': forms.Select(
                choices=[(tz, tz) for tz in pytz.common_timezones],
                attrs={'class': 'form-select'}
            ),
            'group_night_events': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'daily_email_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'daily_email_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'daily_email_recipients': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'email1@example.com, email2@example.com'
            }),
        }
        labels = {
            'timezone': 'Your Timezone',
            'group_night_events': 'Group Events by Night',
            'daily_email_enabled': 'Enable Daily Summary Email',
            'daily_email_time': 'Email Time',
            'daily_email_recipients': 'Email Recipients',
        }
        help_texts = {
            'timezone': 'All times will be displayed in your timezone',
            'group_night_events': 'Show events from 8 PM to 8 AM grouped together on the starting day',
            'daily_email_time': 'Time to send daily summary (in your timezone)',
            'daily_email_recipients': 'Comma-separated list of email addresses to receive daily summaries',
        }
