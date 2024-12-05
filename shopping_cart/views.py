from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from shopease.models import Product
from .models import Cart, CartItem

# Create your views here.

@login_required
def add_to_cart(request, product_id):
    cart, created = Cart.objects.get_or_create(user=request.user)
    product = get_object_or_404(Product, id=product_id)
    
    # Try to get existing cart item or create new one
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    # If item already existed, increment quantity
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'{product.name} has been added to your cart.')
    return redirect('shopease:view_cart')

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('product')
    
    total = sum(item.quantity * item.product.price for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    
    return render(request, 'cart.html', context)

@login_required
def remove_from_cart(request, item_id):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        cart_item.delete()
        messages.success(request, "Item removed from cart successfully.")
    except Cart.DoesNotExist:
        messages.error(request, "Cart not found.")
    except CartItem.DoesNotExist:
        messages.error(request, "Item not found in your cart.")
    except Exception as e:
        messages.error(request, f"Error removing item: {str(e)}")
    
    return redirect('shopping_cart:cart_detail')

@login_required
def clear_cart(request):
    """Clear all items from the user's cart"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart.items.all().delete()  # Delete all cart items
        messages.success(request, 'Your cart has been cleared.')
    except Cart.DoesNotExist:
        messages.info(request, 'Your cart is already empty.')
    
    return redirect('shopease:view_cart')

@login_required
def cart_detail(request):
    try:
        cart = Cart.objects.get(user=request.user)
        # Force refresh from database
        cart_items = CartItem.objects.filter(cart=cart).select_related('product')
        if not cart_items.exists():
            messages.info(request, "Your cart is empty.")
            
        total = sum(item.get_total() for item in cart_items)
        
        context = {
            'cart_items': cart_items,
            'total': total,
        }
    except Cart.DoesNotExist:
        messages.info(request, "Your cart is empty.")
        context = {
            'cart_items': [],
            'total': 0,
        }
    
    return render(request, 'cart.html', context)

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('product')
    
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('shopping_cart:cart_detail')
    
    total = sum(item.get_total() for item in cart_items)
    
    if request.method == 'POST':
        # Collect form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        county = request.POST.get('county')
        
        # Here you would typically:
        # 1. Create an Order record
        # 2. Initiate M-Pesa payment
        # 3. Handle the response
        
        messages.info(request, "Payment processing will be implemented soon.")
        return redirect('shopping_cart:checkout')
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'checkout.html', context)
