from django import template
from shopease.models import Wishlist

register = template.Library()

@register.filter
def in_wishlist(product, user):
    if user.is_authenticated:
        return Wishlist.objects.filter(user=user, product=product).exists()
    return False