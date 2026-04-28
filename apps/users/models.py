from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Allows for future extensions like profile fields, preferences, etc.
    """
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, default='America/Chicago')

    # Daily email settings
    daily_email_enabled = models.BooleanField(default=False)
    daily_email_time = models.TimeField(default='07:00:00', help_text='Time to send daily summary email')
    daily_email_recipients = models.TextField(blank=True, help_text='Comma-separated email addresses')

    # Display preferences
    group_night_events = models.BooleanField(
        default=False,
        help_text='Group events by night (5 PM - 10 AM) instead of calendar day'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username

    def get_display_name(self):
        """Return display name if set, otherwise username"""
        return self.display_name if self.display_name else self.username
