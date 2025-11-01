"""
Admin configuration for dashboard models.
"""
from django.contrib import admin
from .models import (
    WBToken, Competitor, Settings, Product, ProductSnapshot,
    BusinessAlert, AIAdvice, APICallLog
)


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


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['nm_id', 'title', 'brand', 'category', 'price', 'rating', 'quantity', 'sales_30d', 'is_active']
    list_filter = ['category', 'brand', 'is_active', 'is_sample', 'updated_at']
    search_fields = ['nm_id', 'title', 'brand']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']


@admin.register(ProductSnapshot)
class ProductSnapshotAdmin(admin.ModelAdmin):
    list_display = ['product', 'snapshot_at', 'price', 'rating', 'quantity', 'sales_7d', 'stock_status']
    list_filter = ['stock_status', 'snapshot_at']
    search_fields = ['product__nm_id', 'product__title']
    ordering = ['-snapshot_at']


@admin.register(BusinessAlert)
class BusinessAlertAdmin(admin.ModelAdmin):
    list_display = ['alert_type', 'product', 'severity', 'impact_score', 'is_active', 'detected_at']
    list_filter = ['alert_type', 'severity', 'is_active', 'detected_at']
    search_fields = ['product__title', 'product__nm_id', 'message']
    readonly_fields = ['detected_at', 'resolved_at']
    ordering = ['-impact_score', '-detected_at']


@admin.register(AIAdvice)
class AIAdviceAdmin(admin.ModelAdmin):
    list_display = ['advice_type', 'product', 'priority', 'status', 'created_at']
    list_filter = ['advice_type', 'priority', 'status', 'created_at']
    search_fields = ['product__title', 'product__nm_id', 'advice_text']
    readonly_fields = ['created_at', 'applied_at']
    ordering = ['priority', '-created_at']


@admin.register(APICallLog)
class APICallLogAdmin(admin.ModelAdmin):
    list_display = ['endpoint', 'status_code', 'response_time_ms', 'created_at']
    list_filter = ['status_code', 'created_at']
    search_fields = ['endpoint', 'error_message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
