from django.core.management.base import BaseCommand
from shopease.models import Product, Category
import random

class Command(BaseCommand):
    help = 'Sets discounts for products to create hot deals'

    def add_arguments(self, parser):
        # Optional arguments
        parser.add_argument(
            '--category',
            help='Specify category name to apply discounts to'
        )
        parser.add_argument(
            '--min-discount',
            type=int,
            default=5,
            help='Minimum discount percentage (default: 5)'
        )
        parser.add_argument(
            '--max-discount',
            type=int,
            default=30,
            help='Maximum discount percentage (default: 30)'
        )
        parser.add_argument(
            '--probability',
            type=float,
            default=0.3,
            help='Probability of a product getting a discount (default: 0.3)'
        )

    def handle(self, *args, **options):
        # Get the category if specified
        category_name = options.get('category')
        min_discount = options['min_discount']
        max_discount = options['max_discount']
        probability = options['probability']

        # Get products query
        products = Product.objects.all()
        if category_name:
            try:
                category = Category.objects.get(name=category_name)
                products = products.filter(category=category)
                self.stdout.write(f'Applying discounts to {category_name} category')
            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Category "{category_name}" not found')
                )
                return

        # Counter for statistics
        total_products = products.count()
        discounted_products = 0

        # Set random discounts
        for product in products:
            if random.random() < probability:
                discount = random.randint(min_discount, max_discount)
                old_discount = product.discount
                product.discount = discount
                product.save()
                discounted_products += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated "{product.name}": {old_discount}% -> {discount}%'
                    )
                )

        # Print summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary:\n'
                f'Total products processed: {total_products}\n'
                f'Products discounted: {discounted_products}\n'
                f'Discount range: {min_discount}% - {max_discount}%'
            )
        ) 