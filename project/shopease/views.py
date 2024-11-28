from django.db import migrations, models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import CartItem, Product, Category, Brand, ProductVariant, Review, Order, OrderItem, Wishlist, NewsletterSubscriber
from django.db.models import Avg
from decimal import Decimal
from django.db.models import Q
from django.db.models import Min, Max
from django.views.decorators.csrf import csrf_protect

class Migration(migrations.Migration):
    dependencies = [
        ('shopease', 'previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='discount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ]

def index(request):
    # Get featured/latest products
    latest_products = Product.objects.all().order_by('-created_at')[:8]
    
    # Get products with calculated discounts
    products = Product.objects.all()
    deals = []
    
    for product in products:
        variants = product.variants.all()
        if variants.exists():
            prices = [variant.price for variant in variants]
            if len(prices) > 0:
                max_price = max(prices)
                min_price = min(prices)
                
                if max_price > min_price:
                    discount = ((max_price - min_price) / max_price) * 100
                    product.discount = discount
                    product.discounted_price = min_price
                    product.original_price = max_price
                    deals.append(product)
    
    # Get top 4 deals
    deals.sort(key=lambda x: x.discount, reverse=True)
    top_deals = deals[:4]
    
    context = {
        'latest_products': latest_products,
        'top_deals': top_deals,
    }
    return render(request, 'index.html', context)

@login_required
def checkout(request):
    if request.user.is_authenticated:
        cart_items = request.user.shopease_cart.items.all()
        context = {
            'cart_items': cart_items,
        }
        return render(request, 'shopease/checkout.html', context)
    else:
        return redirect('users:login')

@login_required
def order_confirmation(request):
    return render(request, 'order_confirmation.html')

def product_list(request):
    products = Product.objects.all()  # Assuming you have a Product model
    context = {
        'products': products,
    }
    return render(request, 'shopease/product_list.html', context)

@login_required
def delete_product(request, product_id):
    # Only allow staff/admin to delete products
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to delete products.")
        return redirect('shopease:home')
    
    # Get the product or return 404
    product = get_object_or_404(Product, id=product_id)
    
    try:
        # Delete the product
        product.delete()
        messages.success(request, f'Product "{product.name}" has been deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting product: {str(e)}')
    
    # Redirect back to product list or admin dashboard
    return redirect('shopease:product_list')

@login_required
def view_cart(request):
    # Get cart items for the current user
    cart_items = []
    if request.user.is_authenticated:
        cart_items = request.user.shopease_cart.items.all()
    
    context = {
        'cart_items': cart_items,
    }
    return render(request, 'shopease/cart.html', context)

@login_required
@require_POST
def update_cart_quantity(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, user=request.user)
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid quantity'})
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def remove_from_cart(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, user=request.user)
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')
    except CartItem.DoesNotExist:
        messages.error(request, 'Item not found.')
    
    return redirect('shopease:view_cart')

@login_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        # Get the product
        product = get_object_or_404(Product, id=product_id)
        
        # Get the selected variant ID from the form
        variant_id = request.POST.get('variant')
        quantity = int(request.POST.get('quantity', 1))
        
        if not variant_id:
            # If no variant selected, get the first available variant
            variant = product.variants.first()
        else:
            variant = get_object_or_404(ProductVariant, id=variant_id)
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            variant=variant,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # If item exists, update quantity
            cart_item.quantity += quantity
            cart_item.save()
            messages.success(request, 'Cart updated successfully!')
        else:
            messages.success(request, 'Item added to cart!')
            
    return redirect('shopease:view_cart')

@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    context = {
        'wishlist_items': wishlist_items
    }
    return render(request, 'wishlist.html', context)

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check if item already in wishlist
    wishlist_item, created = WishlistItem.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if created:
        messages.success(request, 'Item added to wishlist!')
    else:
        messages.info(request, 'Item already in wishlist!')
        
    return redirect('shopease:product_detail', product_id=product_id)

@login_required
def remove_from_wishlist(request, item_id):
    wishlist_item = get_object_or_404(WishlistItem, id=item_id, user=request.user)
    wishlist_item.delete()
    messages.success(request, 'Item removed from wishlist!')
    return redirect('shopease:wishlist')

@login_required
def toggle_wishlist(request, product_id):
    """Toggle a product in/out of the user's wishlist"""
    product = get_object_or_404(Product, id=product_id)
    
    # Try to find existing wishlist item
    wishlist_item = WishlistItem.objects.filter(
        user=request.user,
        product=product
    ).first()
    
    if wishlist_item:
        # If item exists, remove it
        wishlist_item.delete()
        return JsonResponse({
            'status': 'removed',
            'message': 'Removed from wishlist'
        })
    else:
        # If item doesn't exist, add it
        WishlistItem.objects.create(
            user=request.user,
            product=product
        )
        return JsonResponse({
            'status': 'added',
            'message': 'Added to wishlist'
        })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    context = {
        'product': product,
    }
    return render(request, 'shopease/product_detail.html', context)

@login_required
def process_checkout(request):
    if request.method == 'POST':
        # Get cart items
        cart_items = CartItem.objects.filter(user=request.user)
        
        if not cart_items.exists():
            messages.error(request, 'Your cart is empty!')
            return redirect('shopease:view_cart')
        
        try:
            # Create order
            order = Order.objects.create(
                user=request.user,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                email=request.POST.get('email'),
                address=request.POST.get('address'),
                city=request.POST.get('city'),
                country=request.POST.get('country'),
                postal_code=request.POST.get('zip_code'),
                phone=request.POST.get('phone'),
                payment_method=request.POST.get('payment_method', 'Credit Card'),
                total_amount=sum(item.get_total() for item in cart_items)
            )
            
            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.variant.product,
                    variant=cart_item.variant,
                    quantity=cart_item.quantity,
                    price=cart_item.variant.price
                )
            
            # Clear cart
            cart_items.delete()
            
            # Send order confirmation email (implement this later)
            # send_order_confirmation_email(order)
            
            messages.success(request, 'Order placed successfully!')
            return redirect('shopease:thank_you_with_order', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f'Error processing order: {str(e)}')
            return redirect('shopease:checkout')
    
    return redirect('shopease:checkout')

@login_required
def thank_you(request, order_id=None):
    # Get the order if order_id is provided
    order = None
    if order_id:
        order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'thank_you.html', context)

def search_products(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    
    products = Product.objects.all()
    
    if query:
        products = products.filter(name__icontains=query)
    
    if category:
        products = products.filter(category_id=category)
        
    context = {
        'products': products,
        'search_query': query,
        'selected_category': category
    }
    return render(request, 'search_results.html', context)

def smartphones(request):
    # Get the smartphones category
    try:
        category = Category.objects.get(category_name__iexact='Smartphones')
    except Category.DoesNotExist:
        category = None
    
    # Get all smartphone products
    products = Product.objects.filter(category=category) if category else Product.objects.none()
    
    # Apply sorting if requested
    sort = request.GET.get('sort')
    if sort == 'price_low':
        products = products.order_by('variants__price')
    elif sort == 'price_high':
        products = products.order_by('-variants__price')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    elif sort == 'name_asc':
        products = products.order_by('name')
    
    # Apply price filter if provided
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    if min_price:
        products = products.filter(variants__price__gte=min_price)
    if max_price:
        products = products.filter(variants__price__lte=max_price)
    
    # Remove duplicates that might occur due to variant filtering
    products = products.distinct()
    
    # Pagination
    paginator = Paginator(products, 9)  # Show 9 products per page
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    context = {
        'products': products,
        'category': category,
        'selected_sort': sort,
        'min_price': min_price,
        'max_price': max_price,
    }
    
    return render(request, 'smartphones.html', context)

def hot_deals(request):
    # Get all products with variants
    products = Product.objects.filter(variants__isnull=False).distinct()
    
    # Calculate discounts based on price differences
    deals = []
    for product in products:
        variants = product.variants.all()
        if variants.exists():
            prices = [variant.price for variant in variants]
            if len(prices) > 0:
                max_price = max(prices)
                min_price = min(prices)
                
                if max_price > min_price:
                    # Calculate discount percentage
                    discount = ((max_price - min_price) / max_price) * 100
                    
                    # Only include products with actual discounts
                    if discount > 0:
                        product.discount = round(discount, 2)
                        product.discounted_price = min_price
                        product.original_price = max_price
                        deals.append(product)
    
    # Sort deals by discount percentage (highest first)
    deals.sort(key=lambda x: x.discount, reverse=True)
    
    # Apply filters
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_discount = request.GET.get('min_discount')
    
    if min_price:
        deals = [deal for deal in deals if deal.discounted_price >= float(min_price)]
    if max_price:
        deals = [deal for deal in deals if deal.discounted_price <= float(max_price)]
    if min_discount:
        deals = [deal for deal in deals if deal.discount >= float(min_discount)]
    
    # Pagination
    paginator = Paginator(deals, 9)  # Show 9 products per page
    page = request.GET.get('page')
    deals = paginator.get_page(page)
    
    context = {
        'deals': deals,
        'min_price': min_price,
        'max_price': max_price,
        'min_discount': min_discount,
    }
    
    return render(request, 'hot_deals.html', context)

def categories(request):
    # Get all categories
    categories = Category.objects.all()
    
    # Get selected category
    selected_category_id = request.GET.get('category')
    selected_category = None
    products = []
    
    if selected_category_id:
        try:
            selected_category = Category.objects.get(id=selected_category_id)
            products = Product.objects.filter(category=selected_category)
            
            # Apply sorting if requested
            sort = request.GET.get('sort')
            if sort == 'price_low':
                products = products.order_by('variants__price')
            elif sort == 'price_high':
                products = products.order_by('-variants__price')
            elif sort == 'newest':
                products = products.order_by('-created_at')
            elif sort == 'name_asc':
                products = products.order_by('name')
            
            # Remove duplicates
            products = products.distinct()
            
            # Pagination for products
            paginator = Paginator(products, 9)  # Show 9 products per page
            page = request.GET.get('page')
            products = paginator.get_page(page)
        except Category.DoesNotExist:
            pass
    
    context = {
        'categories': categories,
        'selected_category': selected_category,
        'products': products,
        'selected_sort': request.GET.get('sort'),
    }
    
    return render(request, 'categories.html', context)

def laptops(request):
    # Debug: Print all categories
    all_categories = Category.objects.all()
    print("Available categories:", [cat.category_name for cat in all_categories])
    
    # Try to get or create the Laptops category
    laptop_category, created = Category.objects.get_or_create(
        category_name='Laptops',
        defaults={
            'slug': 'laptops'  # Add any other required fields here
        }
    )
    
    if created:
        print("Created new Laptops category")
    
    # Get all products in the laptops category
    products = Product.objects.filter(category=laptop_category)
    
    # Get min and max prices for the filter
    min_price = products.aggregate(Min('price'))['price__min']
    max_price = products.aggregate(Max('price'))['price__max']
    
    # Handle price filtering
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    
    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)
    
    context = {
        'products': products,
        'min_price': min_price,
        'max_price': max_price,
        'current_min': price_min or min_price,
        'current_max': price_max or max_price,
    }
    
    return render(request, 'laptops.html', context)

def accessories(request):
    # Get accessories products from your database
    accessories_products = Product.objects.filter(category='accessories')  # Adjust the filter based on your model structure
    
    context = {
        'products': accessories_products,
        'category_name': 'Accessories'
    }
    return render(request, 'shopease/products.html', context)  # Adjust template path as needed

@require_POST
@csrf_protect
def newsletter_signup(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'success': False, 'error': 'Email is required'})
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({'success': False, 'error': 'Invalid email format'})
        
        # Check if email already exists
        if Newsletter.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'error': 'Email already subscribed'})
        
        # Save new subscription
        Newsletter.objects.create(email=email)
        
        return JsonResponse({
            'success': True,
            'message': 'Successfully subscribed to newsletter'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })