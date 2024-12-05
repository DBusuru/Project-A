from .models import Cart, CartItem

def cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        cart_count = cart_items.count()
    else:
        cart_count = 0
    
    return {'cart_count': cart_count} 