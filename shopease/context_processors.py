from .models import Category
from shopping_cart.models import Cart, CartItem
from django.db import models
from django.db.models import Sum

def categories_processor(request):
    return {
        'categories': Category.objects.all()
    }

def cart_count(request):
    if request.user.is_authenticated:
        count = CartItem.objects.filter(cart__user=request.user).aggregate(
            total_items=Sum('quantity'))['total_items'] or 0
        return {'cart_count': count}
    return {'cart_count': 0}