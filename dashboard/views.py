"""
Views for WBMonitor dashboard.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from typing import List, Dict, Any, Optional
from dashboard.models import WBToken, Competitor, Settings
from dashboard.services import get_dashboard_data
from dashboard.utils import safe_str, safe_int, safe_float


@login_required
def dashboard_view(request):
    """
    Main dashboard view with product table, filters, sorting, and pagination.
    """
    # Get user settings
    try:
        settings = Settings.objects.get(user=request.user)
    except Settings.DoesNotExist:
        settings = Settings.objects.create(user=request.user)
    
    # Get dashboard data
    data = get_dashboard_data(request.user)
    
    # Apply filters
    search_query = request.GET.get('search', '').strip()
    stock_filter = request.GET.get('stock', '').strip()
    alert_filter = request.GET.get('alert', '').strip()
    
    filtered_data = data
    
    # Search filter
    if search_query:
        filtered_data = [
            item for item in filtered_data
            if search_query.lower() in safe_str(item.get('title', '')).lower()
            or search_query.lower() in safe_str(item.get('brand', '')).lower()
            or search_query in safe_str(item.get('nmId', ''))
        ]
    
    # Stock status filter
    if stock_filter:
        filtered_data = [
            item for item in filtered_data
            if item.get('stock_status') == stock_filter
        ]
    
    # Alert filter
    if alert_filter:
        filtered_data = [
            item for item in filtered_data
            if alert_filter in item.get('alerts', [])
        ]
    
    # Sorting
    sort_by = request.GET.get('sort', settings.default_sort)
    sort_order = request.GET.get('order', settings.default_sort_order)
    
    # Determine if sorting by numeric or string field
    def sort_key(item):
        value = item.get(sort_by)
        if sort_by in ['nmId', 'quantity', 'feedbacks', 'price', 'rating', 'storage_cost', 'cost_percentage']:
            numeric_val = safe_float(value) if value is not None else (0 if sort_order == 'desc' else float('inf'))
            return numeric_val
        return safe_str(value, '').lower()
    
    try:
        reverse = (sort_order == 'desc')
        filtered_data = sorted(filtered_data, key=sort_key, reverse=reverse)
    except Exception:
        pass  # Keep original order if sorting fails
    
    # Pagination
    paginator = Paginator(filtered_data, settings.items_per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'data': page_obj.object_list,
        'search_query': search_query,
        'stock_filter': stock_filter,
        'alert_filter': alert_filter,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'settings': settings,
        'total_items': len(filtered_data),
        'total_all': len(data),
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def reports_view(request):
    """
    Reports view with aggregated statistics and charts.
    """
    data = get_dashboard_data(request.user)
    
    # Calculate aggregates
    total_products = len(data)
    out_of_stock = len([item for item in data if item.get('stock_status') == 'Out of Stock'])
    low_stock = len([item for item in data if item.get('stock_status') == 'Low Stock'])
    in_stock = len([item for item in data if item.get('stock_status') == 'In Stock'])
    
    total_value = sum([safe_float(item.get('price', 0)) * safe_int(item.get('quantity', 0)) for item in data])
    avg_rating = sum([safe_float(item.get('rating', 0)) for item in data if item.get('rating')]) / max(len([item for item in data if item.get('rating')]), 1)
    
    alerts_count = {
        'low_rating': len([item for item in data if 'low_rating' in item.get('alerts', [])]),
        'low_stock': len([item for item in data if 'low_stock' in item.get('alerts', [])]),
        'out_of_stock': len([item for item in data if 'out_of_stock' in item.get('alerts', [])]),
    }
    
    context = {
        'total_products': total_products,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'in_stock': in_stock,
        'total_value': total_value,
        'avg_rating': avg_rating,
        'alerts_count': alerts_count,
    }
    
    return render(request, 'dashboard/reports.html', context)


@login_required
def alerts_view(request):
    """
    Alerts view showing all products with alerts.
    """
    data = get_dashboard_data(request.user)
    
    # Filter items with alerts
    alerted_items = [item for item in data if item.get('alerts')]
    
    # Sort by number of alerts (descending)
    alerted_items.sort(key=lambda x: len(x.get('alerts', [])), reverse=True)
    
    # Pagination
    try:
        settings = Settings.objects.get(user=request.user)
        items_per_page = settings.items_per_page
    except Settings.DoesNotExist:
        items_per_page = 50
    
    paginator = Paginator(alerted_items, items_per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'data': page_obj.object_list,
        'total_alerts': len(alerted_items),
    }
    
    return render(request, 'dashboard/alerts.html', context)


@login_required
def competitors_view(request):
    """
    Competitors view for tracking competitor products.
    """
    competitors = Competitor.objects.filter(user=request.user)
    
    # TODO: Implement fetch_competitor_data(url) service
    # For now, show competitor list
    competitor_data = []
    for competitor in competitors:
        competitor_data.append({
            'id': competitor.id,
            'name': competitor.name,
            'url': competitor.url,
            'created_at': competitor.created_at,
        })
    
    context = {
        'competitors': competitor_data,
    }
    
    return render(request, 'dashboard/competitors.html', context)


@login_required
@require_http_methods(["POST"])
def add_competitor_view(request):
    """Add a new competitor."""
    name = request.POST.get('name', '').strip()
    url = request.POST.get('url', '').strip()
    
    if not name or not url:
        messages.error(request, "Name and URL are required.")
        return redirect('dashboard:competitors')
    
    Competitor.objects.create(user=request.user, name=name, url=url)
    messages.success(request, f"Competitor '{name}' added successfully.")
    
    return redirect('dashboard:competitors')


@login_required
@require_http_methods(["POST"])
def delete_competitor_view(request, competitor_id):
    """Delete a competitor."""
    try:
        competitor = Competitor.objects.get(id=competitor_id, user=request.user)
        competitor.delete()
        messages.success(request, "Competitor deleted successfully.")
    except Competitor.DoesNotExist:
        messages.error(request, "Competitor not found.")
    
    return redirect('dashboard:competitors')


@login_required
def analysis_view(request):
    """
    Analysis view with trends and historical data visualization.
    """
    data = get_dashboard_data(request.user)
    
    # TODO: Implement historical data aggregation
    # For now, show current data analysis
    
    # Group by brand
    brand_stats = {}
    for item in data:
        brand = safe_str(item.get('brand', 'Unknown'))
        if brand not in brand_stats:
            brand_stats[brand] = {
                'count': 0,
                'total_quantity': 0,
                'avg_rating': 0,
                'ratings': [],
            }
        brand_stats[brand]['count'] += 1
        brand_stats[brand]['total_quantity'] += safe_int(item.get('quantity', 0))
        if item.get('rating'):
            brand_stats[brand]['ratings'].append(safe_float(item.get('rating')))
    
    # Calculate averages
    for brand, stats in brand_stats.items():
        if stats['ratings']:
            stats['avg_rating'] = sum(stats['ratings']) / len(stats['ratings'])
        else:
            stats['avg_rating'] = 0
    
    context = {
        'brand_stats': brand_stats,
        'total_products': len(data),
    }
    
    return render(request, 'dashboard/analysis.html', context)


@login_required
def settings_view(request):
    """
    Settings view for API tokens and user preferences.
    """
    # Get or create tokens
    try:
        tokens = WBToken.objects.get(user=request.user)
    except WBToken.DoesNotExist:
        tokens = WBToken.objects.create(user=request.user)
    
    # Get or create settings
    try:
        settings = Settings.objects.get(user=request.user)
    except Settings.DoesNotExist:
        settings = Settings.objects.create(user=request.user)
    
    if request.method == 'POST':
        # Update tokens
        tokens.content_token = request.POST.get('content_token', '').strip()
        tokens.stats_token = request.POST.get('stats_token', '').strip()
        tokens.prices_token = request.POST.get('prices_token', '').strip()
        tokens.analytics_token = request.POST.get('analytics_token', '').strip()
        tokens.save()
        
        # Update settings
        settings.low_stock_threshold = safe_int(request.POST.get('low_stock_threshold', 10))
        settings.low_rating_threshold = safe_float(request.POST.get('low_rating_threshold', 4.0))
        settings.items_per_page = safe_int(request.POST.get('items_per_page', 50))
        settings.default_sort = request.POST.get('default_sort', 'nmId')
        settings.default_sort_order = request.POST.get('default_sort_order', 'asc')
        settings.save()
        
        # Clear cache to force refresh
        from django.core.cache import cache
        cache.delete(f"dashboard_data_{request.user.id}")
        
        messages.success(request, "Settings saved successfully!")
        return redirect('dashboard:settings')
    
    context = {
        'tokens': tokens,
        'settings': settings,
    }
    
    return render(request, 'dashboard/settings.html', context)


@login_required
def api_refresh_view(request):
    """
    API endpoint to manually refresh dashboard data (clears cache).
    """
    from django.core.cache import cache
    cache.delete(f"dashboard_data_{request.user.id}")
    
    return JsonResponse({'status': 'success', 'message': 'Cache cleared. Data will refresh on next page load.'})

