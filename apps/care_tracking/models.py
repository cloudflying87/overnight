from django.db import models
from django.conf import settings
from django.utils import timezone


class EventOption(models.Model):
    """
    User-customizable event options (e.g., "woke up", "restless").
    Each user manages their own set of options.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='event_options'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)  # Soft delete
    color_code = models.CharField(max_length=7, default='#3B82F6')  # For UI/charts
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'event_options'
        ordering = ['name']
        unique_together = [['user', 'name']]  # Prevent duplicate names per user
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
        verbose_name = 'Event Option'
        verbose_name_plural = 'Event Options'

    def __str__(self):
        return self.name


class NightEvent(models.Model):
    """
    Individual night event logged by a caregiver.
    Can have multiple event options selected.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='night_events'
    )
    event_options = models.ManyToManyField(
        EventOption,
        related_name='night_events',
        blank=True
    )
    notes = models.TextField(blank=True)
    event_datetime = models.DateTimeField(default=timezone.now)  # When event occurred
    created_at = models.DateTimeField(auto_now_add=True)  # When logged
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'night_events'
        ordering = ['-event_datetime']
        indexes = [
            models.Index(fields=['user', 'event_datetime']),
            models.Index(fields=['event_datetime']),
        ]
        verbose_name = 'Night Event'
        verbose_name_plural = 'Night Events'

    def __str__(self):
        return f"{self.user.username} - {self.event_datetime.strftime('%Y-%m-%d %H:%M')}"

    @property
    def event_date(self):
        """Returns just the date portion for grouping"""
        return self.event_datetime.date()

    def get_options_display(self):
        """Returns comma-separated list of event options"""
        return ", ".join([opt.name for opt in self.event_options.all()])


class DayNote(models.Model):
    """
    Notes for a specific day to correlate with nighttime events.
    One note per user per day.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='day_notes'
    )
    date = models.DateField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'day_notes'
        ordering = ['-date']
        unique_together = [['user', 'date']]  # One note per user per day
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
        verbose_name = 'Day Note'
        verbose_name_plural = 'Day Notes'

    def __str__(self):
        return f"{self.user.username} - {self.date}"
