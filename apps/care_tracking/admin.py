from django.contrib import admin
from .models import EventOption, NightEvent, DayNote


@admin.register(EventOption)
class EventOptionAdmin(admin.ModelAdmin):
    """Admin for EventOption model"""

    list_display = ['name', 'user', 'is_active', 'color_code', 'created_at']
    list_filter = ['is_active', 'user', 'created_at']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['user', 'name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'description')
        }),
        ('Display', {
            'fields': ('color_code', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class NightEventAdmin(admin.ModelAdmin):
    """Admin for NightEvent model"""

    list_display = ['user', 'event_datetime', 'get_options_display', 'created_at']
    list_filter = ['user', 'event_datetime', 'created_at']
    search_fields = ['user__username', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'event_datetime'
    ordering = ['-event_datetime']
    filter_horizontal = ['event_options']

    fieldsets = (
        ('Event Information', {
            'fields': ('user', 'event_datetime', 'event_options')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with prefetch_related"""
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('event_options').select_related('user')
        return queryset


admin.register(NightEvent)(NightEventAdmin)


@admin.register(DayNote)
class DayNoteAdmin(admin.ModelAdmin):
    """Admin for DayNote model"""

    list_display = ['user', 'date', 'content_preview', 'created_at']
    list_filter = ['user', 'date', 'created_at']
    search_fields = ['user__username', 'content']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date']

    fieldsets = (
        ('Day Note Information', {
            'fields': ('user', 'date', 'content')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def content_preview(self, obj):
        """Show first 50 characters of content"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'Content Preview'
