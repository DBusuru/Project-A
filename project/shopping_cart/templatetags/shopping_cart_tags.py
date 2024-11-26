from django import template
from shopping_cart.models import Cart

register = template.Library()

@register.simple_tag(takes_context=True)
def cart_item_count(context):
    request = context['request']
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            return cart.items.count()
    return 0

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiplies the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0