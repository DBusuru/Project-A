from django.shortcuts import render,redirect
from django.dispatch import receiver
from django.db.models.signals import post_save
from.models import OrderItem
from django.contrib.auth.decorators import login_required
from django.http import Http404

# Create your views here.

def index(request):
    return render(request, 'index.html')

def checkout(request):
    return render(request, 'checkout.html')

def product(request):
    return render(request, 'product.html')

@login_required
def delete_product(request, product_id):
    try:
        # Fetch the order item belonging to the logged-in user
        order_item = OrderItem.objects.get(
            id=product_id,
            order__user=request.user,
            order__is_complete=False
        )
        order_item.delete()
    except OrderItem.DoesNotExist as e:
        raise Http404(
            "Product not found or you don't have permission to delete it."
        ) from e
    return redirect('checkout')

