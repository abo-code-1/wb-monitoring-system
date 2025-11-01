"""
Management command to populate database with sample Wildberries product data.
Usage: python manage.py populate_sample_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from dashboard.models import Product, ProductSnapshot, Settings
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Populate database with realistic Wildberries product data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=60,
            help='Number of sample products to create (default: 60)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing sample products before creating new ones',
        )
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Username to assign products to (default: admin)',
        )

    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']
        username = options['user']

        # Get or create user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" not found. Please create it first with createsuperuser.')
            )
            return

        # Get or create settings
        settings, _ = Settings.objects.get_or_create(user=user)

        if clear:
            deleted_count = Product.objects.filter(user=user, is_sample=True).delete()[0]
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {deleted_count} existing sample products')
            )

        # Sample product data
        brands = [
            'Apple', 'Samsung', 'Xiaomi', 'Sony', 'LG', 'Philips',
            'Nike', 'Adidas', 'Puma', 'Reebok', 'New Balance',
            'Bosch', 'Whirlpool', 'Indesit', 'Ariston',
            'Tommy Hilfiger', 'Calvin Klein', 'Levi\'s', 'Zara',
        ]

        categories_data = [
            {
                'category': 'Electronics',
                'titles': [
                    'Smartphone 128GB', 'Wireless Earbuds Pro', 'Smart Watch Series',
                    'Tablet 10 inch', 'Laptop Stand Aluminum', 'Power Bank 10000mAh',
                    'Bluetooth Speaker JBL', 'USB-C Cable Fast Charge', 'Phone Case Protective',
                    'Wireless Charger Stand', 'Monitor 27 inch', 'Keyboard Mechanical',
                ]
            },
            {
                'category': 'Home',
                'titles': [
                    'Coffee Maker Espresso', 'Vacuum Cleaner Robot', 'Iron Steam Professional',
                    'Microwave Oven Digital', 'Blender Multifunction', 'Toaster 4 Slice',
                    'Air Fryer 5L', 'Food Processor 1000W', 'Kettle Electric 1.7L',
                    'Stand Mixer Kitchen', 'Coffee Grinder Burr', 'Juicer Cold Press',
                ]
            },
            {
                'category': 'Beauty',
                'titles': [
                    'Shampoo Nourishing 500ml', 'Face Cream Moisturizing 50ml',
                    'Toothbrush Electric Sonic', 'Perfume EDT 50ml', 'Lipstick Matte Red',
                    'Sunscreen SPF50 100ml', 'Hair Mask Repair', 'Body Lotion 400ml',
                    'Serum Vitamin C', 'Eye Cream Anti-Aging', 'Face Mask Clay',
                ]
            },
            {
                'category': 'Clothing',
                'titles': [
                    'Running Shoes Sports', 'Casual T-Shirt Cotton', 'Winter Jacket Down',
                    'Jeans Classic Fit', 'Sports Shorts Athletic', 'Dress Elegant',
                    'Sneakers Street Style', 'Boots Leather Ankle', 'Cap Baseball Snap',
                    'Hoodie Zip Fleece', 'Pants Business Casual', 'Shirt Dress Shirt',
                ]
            },
            {
                'category': 'Sports',
                'titles': [
                    'Yoga Mat Premium', 'Dumbbells Set 10kg', 'Bicycle Helmet Safety',
                    'Tennis Racket Carbon', 'Fitness Tracker GPS', 'Jump Rope Speed',
                    'Swimming Goggles Anti-Fog', 'Backpack Hiking 40L', 'Tent 2-Person',
                    'Bike Rack Car', 'Water Bottle 750ml', 'Resistance Bands Set',
                ]
            },
        ]

        products_created = 0
        nm_id_start = 123456789  # Starting nmId
        now = timezone.now()

        for i in range(count):
            category_data = random.choice(categories_data)
            brand = random.choice(brands)
            title = f"{brand} {random.choice(category_data['titles'])}"

            # Generate realistic nmId (7-8 digits)
            nm_id = nm_id_start + i

            # Generate realistic rating (3.0-5.0, 70% have 4.0+)
            if random.random() < 0.7:
                rating = round(random.uniform(4.0, 5.0), 2)
            else:
                rating = round(random.uniform(3.0, 4.0), 2)

            # Generate feedbacks count (0-5000)
            feedbacks = random.randint(0, 5000)
            if random.random() < 0.3:  # 30% have no feedbacks yet
                feedbacks = 0

            # Generate quantity (0-100)
            quantity = random.randint(0, 100)
            # 15% out of stock, 20% low stock, rest normal
            if random.random() < 0.15:
                quantity = 0
            elif random.random() < 0.35:  # 20% total have low stock
                quantity = random.randint(1, 9)

            # Generate sales data
            sales_30d = random.randint(0, 200)
            # 7-day sales is roughly proportional to 30-day but can vary
            sales_7d = max(0, random.randint(int(sales_30d * 0.15), int(sales_30d * 0.35)))
            # Some products can have zero sales
            if random.random() < 0.15:
                sales_30d = 0
                sales_7d = 0

            # Generate price (300-50000 rubles)
            price = round(random.uniform(300, 50000), 2)

            # Generate storage cost (0.01% - 0.05% of price)
            cost_percentage = random.uniform(0.01, 0.05)
            storage_cost = round(float(price) * cost_percentage, 2)

            # Create product
            product, created = Product.objects.get_or_create(
                user=user,
                nm_id=nm_id,
                defaults={
                    'title': title,
                    'brand': brand,
                    'category': category_data['category'],
                    'price': price,
                    'rating': rating,
                    'feedbacks': feedbacks,
                    'quantity': quantity,
                    'sales_7d': sales_7d,
                    'sales_30d': sales_30d,
                    'storage_cost': storage_cost,
                    'is_active': True,
                    'is_sample': True,
                }
            )

            if created:
                products_created += 1

                # Create snapshots for last 30 days
                self.create_snapshots(product, now)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {products_created} sample products with 30-day snapshots'
            )
        )

    def create_snapshots(self, product, now):
        """Create daily snapshots for the last 30 days."""
        for days_ago in range(30):
            snapshot_date = now - timedelta(days=days_ago)
            
            # Add some variance to snapshot data (±10%)
            variance = random.uniform(0.9, 1.1)
            
            # Simulate realistic changes over time
            age_factor = 1 - (days_ago / 300)  # Slight decline over time
            
            snapshot_quantity = max(0, int(product.quantity * variance * age_factor))
            snapshot_sales_7d = max(0, int(product.sales_7d * variance))
            snapshot_sales_30d = max(0, int(product.sales_30d * variance * age_factor))
            snapshot_rating = round(product.rating + random.uniform(-0.1, 0.1), 2)
            snapshot_rating = max(0.0, min(5.0, snapshot_rating))
            
            # Determine stock status
            if snapshot_quantity == 0:
                stock_status = 'Out of Stock'
            elif snapshot_quantity < 10:
                stock_status = 'Low Stock'
            else:
                stock_status = 'In Stock'
            
            ProductSnapshot.objects.create(
                product=product,
                snapshot_at=snapshot_date,
                price=product.price,
                rating=snapshot_rating,
                quantity=snapshot_quantity,
                feedbacks=int(product.feedbacks * age_factor),
                sales_7d=snapshot_sales_7d,
                sales_30d=snapshot_sales_30d,
                storage_cost=product.storage_cost,
                stock_status=stock_status,
            )
