from django.urls import path
from . import views

app_name = 'care_tracking'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),

    # Event Options URLs
    path('options/', views.EventOptionListView.as_view(), name='eventoption_list'),
    path('options/create/', views.EventOptionCreateView.as_view(), name='eventoption_create'),
    path('options/<int:pk>/edit/', views.EventOptionUpdateView.as_view(), name='eventoption_update'),
    path('options/<int:pk>/delete/', views.EventOptionDeleteView.as_view(), name='eventoption_delete'),

    # Night Events URLs
    path('events/', views.NightEventListView.as_view(), name='nightevent_list'),
    path('events/log/', views.NightEventCreateView.as_view(), name='nightevent_create'),
    path('events/<int:pk>/edit/', views.NightEventUpdateView.as_view(), name='nightevent_update'),
    path('events/<int:pk>/delete/', views.NightEventDeleteView.as_view(), name='nightevent_delete'),

    # Day Notes URLs
    path('notes/', views.DayNoteListView.as_view(), name='daynote_list'),
    path('notes/create/', views.DayNoteCreateView.as_view(), name='daynote_create'),
    path('notes/<int:pk>/edit/', views.DayNoteUpdateView.as_view(), name='daynote_update'),
    path('notes/<int:pk>/delete/', views.DayNoteDeleteView.as_view(), name='daynote_delete'),

    # Calendar Views
    path('calendar/', views.calendar_view, name='calendar'),
    path('day/<int:year>/<int:month>/<int:day>/', views.day_view, name='day_view'),

    # Trends (will be added in Phase 6)
    # path('trends/', views.trends_view, name='trends'),
]
