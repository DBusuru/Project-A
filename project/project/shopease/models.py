from django.db import models
from django.contrib.auth.models import User
# from products.models import Product

# Assuming Product model should be in shopease app
class Product(models.Model):
    name = models.CharField(max_length=200)
    # Add other product fields as needed

class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email 