"""
Management command to populate database with sample Wildberries product data.
Usage: python manage.py populate_sample_data
"""
from django.core.management.base import BaseCommand
from dashboard.models import SampleProduct
import random


class Command(BaseCommand):
    help = 'Populate database with sample Wildberries product data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of sample products to create (default: 50)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing sample products before creating new ones',
        )

    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']

        if clear:
            deleted_count = SampleProduct.objects.all().delete()[0]
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {deleted_count} existing sample products')
            )

        # Sample product data based on Wildberries API structure
        brands = [
            'Nike', 'Adidas', 'Puma', 'Reebok', 'New Balance',
            'Samsung', 'Apple', 'Xiaomi', 'Huawei', 'Sony',
            'Bosch', 'LG', 'Whirlpool', 'Indesit', 'Ariston',
            'Lacoste', 'Tommy Hilfiger', 'Calvin Klein', 'Levi\'s', 'Zara',
            'Nestle', 'Coca-Cola', 'Pepsi', 'Ferrero', 'Mars',
        ]

        categories_data = [
            {
                'category': 'Clothing & Shoes',
                'titles': [
                    'Running Shoes Sports', 'Casual T-Shirt', 'Winter Jacket',
                    'Jeans Classic', 'Sports Shorts', 'Dress Elegant',
                    'Sneakers Street', 'Boots Leather', 'Cap Baseball',
                ]
            },
            {
                'category': 'Electronics',
                'titles': [
                    'Smartphone 128GB', 'Wireless Earbuds', 'Smart Watch',
                    'Tablet 10 inch', 'Laptop Stand', 'Power Bank',
                    'Bluetooth Speaker', 'USB Cable', 'Phone Case',
                ]
            },
            {
                'category': 'Home & Kitchen',
                'titles': [
                    'Coffee Maker', 'Vacuum Cleaner', 'Iron Steam',
                    'Microwave Oven', 'Blender Multifunction', 'Toaster',
                    'Dishwasher Safe', 'Food Processor', 'Kettle Electric',
                ]
            },
            {
                'category': 'Beauty & Personal Care',
                'titles': [
                    'Shampoo Nourishing', 'Face Cream Moisturizing',
                    'Toothbrush Electric', 'Perfume 50ml', 'Lipstick Matte',
                    'Sunscreen SPF50', 'Hair Mask', 'Body Lotion',
                ]
            },
            {
                'category': 'Sports & Outdoors',
                'titles': [
                    'Yoga Mat', 'Dumbbells Set', 'Bicycle Helmet',
                    'Tennis Racket', 'Fitness Tracker', 'Jump Rope',
                    'Swimming Goggles', 'Backpack Hiking', 'Tent 2-person',
                ]
            },
        ]

        products_created = 0
        nm_id_start = 123456789  # Starting nmId

        for i in range(count):
            category_data = random.choice(categories_data)
            brand = random.choice(brands)
            title = f"{brand} {random.choice(category_data['titles'])}"

            # Generate realistic nmId (7-8 digits)
            nm_id = nm_id_start + i

            # Generate realistic rating (3.0-5.0, most products have 4.0-5.0)
            if random.random() < 0.7:  # 70% have good ratings
                rating = round(random.uniform(4.0, 5.0), 2)
            else:
                rating = round(random.uniform(3.0, 4.0), 2)

            # Generate feedbacks count (0-5000, most have some reviews)
            feedbacks = random.randint(0, 5000)
            if random.random() < 0.3:  # 30% have no feedbacks yet
                feedbacks = 0

            # Generate quantity (0-500, various stock levels)
            quantity = random.randint(0, 500)
            if random.random() < 0.2:  # 20% out of stock
                quantity = 0
            elif random.random() < 0.3:  # 30% low stock (1-10)
                quantity = random.randint(1, 10)

            # Generate price (100-50000 rubles)
            price = round(random.uniform(100, 50000), 2)

            # Generate storage cost (0.1% - 5% of price, sometimes null)
            if random.random() < 0.15:  # 15% have no storage cost data
                storage_cost = None
            else:
                cost_percentage = random.uniform(0.001, 0.05)
                storage_cost = round(float(price) * cost_percentage, 2)

            product, created = SampleProduct.objects.get_or_create(
                nmId=nm_id,
                defaults={
                    'title': title,
                    'brand': brand,
                    'rating': rating,
                    'feedbacks': feedbacks,
                    'quantity': quantity,
                    'price': price,
                    'storage_cost': storage_cost,
                    'is_active': True,
                }
            )

            if created:
                products_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {products_created} sample products'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                'Note: Sample products will be used when API calls fail or return empty data.'
            )
        )

