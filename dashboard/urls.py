"""
URL configuration for dashboard app.
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_alt'),
    path('reports/', views.reports_view, name='reports'),
    path('alerts/', views.alerts_view, name='alerts'),
    path('ai-advice/', views.ai_advice_view, name='ai_advice'),
    path('competitors/', views.competitors_view, name='competitors'),
    path('competitors/add/', views.add_competitor_view, name='add_competitor'),
    path('competitors/delete/<int:competitor_id>/', views.delete_competitor_view, name='delete_competitor'),
    path('analysis/', views.analysis_view, name='analysis'),
    path('settings/', views.settings_view, name='settings'),
    path('refresh/', views.refresh_view, name='refresh'),
    path('api/refresh/', views.api_refresh_view, name='api_refresh'),
]

