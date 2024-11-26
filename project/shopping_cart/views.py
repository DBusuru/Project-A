from django.shortcuts import render
from django.http import JsonResponse
from shopping_cart.models import Cart
from django.contrib.auth.decorators import login_required

# Create your views here.

def add_to_cart(request):
    if request.method == 'POST':
        # ... your existing add to cart logic ...
        
        cart_count = Cart.objects.filter(user=request.user).count()
        return JsonResponse({
            'success': True,
            'cart_count': cart_count
        })

@login_required
def cart_view(request):
    # Get the user's cart items
    cart_items = request.user.cart_items.all()
    
    context = {
        'cart_items': cart_items,
        'total': sum(item.product.price * item.quantity for item in cart_items)
    }
    
    return render(request, 'shopping_cart/cart.html', context)
