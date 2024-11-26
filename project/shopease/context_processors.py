from .models import Category
from shopping_cart.models import Cart

def categories_processor(request):
    return {
        'categories': Category.objects.all()
    }

def cart_count(request):
    if request.user.is_authenticated:
        cart_items_count = Cart.objects.filter(user=request.user).count()
    else:
        cart_items_count = 0
    return {'cart_items_count': cart_items_count}