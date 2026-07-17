from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model"""

    list_display = [
        'username', 'email', 'display_name',
        'daily_email_enabled', 'daily_email_time', 'timezone',
        'recipient_count', 'daily_email_last_sent',
        'is_active', 'created_at',
    ]
    list_filter = ['daily_email_enabled', 'is_staff', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'display_name', 'daily_email_recipients']
    ordering = ['-created_at']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('display_name', 'timezone', 'group_night_events', 'created_at', 'updated_at')
        }),
        ('Daily Email Summary', {
            'fields': (
                'daily_email_enabled',
                'daily_email_time',
                'daily_email_recipients',
                'daily_email_last_sent',
            ),
            'description': (
                'Schedule for the automated nightly summary email. '
                '"Last sent" is managed automatically to avoid duplicate sends.'
            ),
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'daily_email_last_sent']

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'display_name')
        }),
    )

    @admin.display(description='Recipients')
    def recipient_count(self, obj):
        """Number of configured recipient addresses for the daily email."""
        from apps.care_tracking.email_utils import parse_recipients
        return len(parse_recipients(obj))
