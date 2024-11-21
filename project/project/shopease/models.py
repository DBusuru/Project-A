from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.views import LoginView
from project import settings
from django import forms
from django.contrib.auth.forms import UserCreationForm



# Create your models here.


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.id} - {'Completed' if self.is_complete else 'Pending'}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    @property
    def total_price(self):
        return self.quantity * self.price


class User(AbstractUser):
    # Define your custom fields if necessary

    # Resolving the conflict with related_name for groups
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='shopease_user_set',  # Unique reverse relationship name
        blank=True,
        help_text='The groups this user belongs to.'
    )

    # Resolving the conflict with related_name for user_permissions
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='shopease_user_permissions_set',  # Unique reverse relationship name
        blank=True,
        help_text='Specific permissions for this user.'
    )

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='default.jpg')

    def __str__(self):
        return f"{self.user.username}'s Profile"





