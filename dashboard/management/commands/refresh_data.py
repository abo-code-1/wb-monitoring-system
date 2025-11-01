"""
Management command to refresh product data and generate alerts/advice.
Usage: python manage.py refresh_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import Product, ProductSnapshot, Settings
from dashboard.services import generate_business_alerts, generate_ai_advice
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Refresh product data, create snapshots, generate alerts and AI advice'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Username to process products for (default: admin)',
        )

    def handle(self, *args, **options):
        username = options['user']
        
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" not found.')
            )
            return

        self.stdout.write('Starting data refresh...')
        
        # 1. Randomly vary product data (±10%)
        products = Product.objects.filter(user=user, is_active=True)
        updated_count = 0
        
        for product in products:
            # Apply random variance
            variance = random.uniform(0.9, 1.1)
            
            # Update fields with variance
            product.quantity = max(0, int(product.quantity * variance))
            product.sales_7d = max(0, int(product.sales_7d * variance))
            product.sales_30d = max(0, int(product.sales_30d * variance))
            
            # Small rating variations
            rating_change = random.uniform(-0.05, 0.05)
            new_rating = float(product.rating) + rating_change
            product.rating = round(max(0.0, min(5.0, new_rating)), 2)
            
            # Some products might get feedbacks
            if random.random() < 0.1:  # 10% chance
                product.feedbacks += random.randint(1, 5)
            
            product.save()
            updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Updated {updated_count} products with random variations')
        )

        # 2. Create new snapshot for today
        now = timezone.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        snapshot_count = 0
        for product in products:
            # Check if snapshot already exists for today
            if ProductSnapshot.objects.filter(product=product, snapshot_at__date=today.date()).exists():
                continue
            
            # Determine stock status
            if product.quantity == 0:
                stock_status = 'Out of Stock'
            elif product.quantity < 10:
                stock_status = 'Low Stock'
            else:
                stock_status = 'In Stock'
            
            ProductSnapshot.objects.create(
                product=product,
                snapshot_at=today,
                price=product.price,
                rating=product.rating,
                quantity=product.quantity,
                feedbacks=product.feedbacks,
                sales_7d=product.sales_7d,
                sales_30d=product.sales_30d,
                storage_cost=product.storage_cost,
                stock_status=stock_status,
            )
            snapshot_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Created {snapshot_count} new product snapshots')
        )

        # 3. Generate business alerts
        try:
            alerts_generated = generate_business_alerts(user)
            self.stdout.write(
                self.style.SUCCESS(f'Generated {alerts_generated} business alerts')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating alerts: {e}')
            )

        # 4. Generate AI advice
        try:
            advice_generated = generate_ai_advice(user)
            self.stdout.write(
                self.style.SUCCESS(f'Generated {advice_generated} AI advice entries')
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'AI advice generation failed (may be due to missing API key): {e}')
            )

        self.stdout.write(self.style.SUCCESS('Data refresh completed!'))

