"""
Admin configuration for dashboard models.
"""
from django.contrib import admin
from .models import WBToken, Competitor, Settings, SampleProduct


@admin.register(WBToken)
class WBTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_token', 'stats_token', 'prices_token', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Competitor)
class CompetitorAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'url', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['name', 'url']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'low_stock_threshold', 'low_rating_threshold', 'items_per_page', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SampleProduct)
class SampleProductAdmin(admin.ModelAdmin):
    list_display = ['nmId', 'brand', 'title', 'rating', 'quantity', 'price', 'is_active', 'updated_at']
    list_filter = ['is_active', 'brand', 'updated_at']
    search_fields = ['nmId', 'title', 'brand']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']

