from django.db import migrations, models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import CartItem, Product, Category, Brand, ProductVariant, Review, Order, OrderItem, Wishlist, NewsletterSubscriber, PaymentPlan, Transaction
from django.db.models import Avg
from decimal import Decimal
from django.db.models import Q
from django.db.models import Min, Max
from django.views.decorators.csrf import csrf_protect
from shopping_cart.models import Cart, CartItem
from django.utils import timezone
import requests
from datetime import datetime
from base64 import b64encode
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

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

class MpesaGateway:
    def __init__(self):
        self.business_shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.access_token_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        self.stk_push_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

    def get_access_token(self):
        try:
            auth = b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode()
            headers = {'Authorization': f'Basic {auth}'}
            
            response = requests.get(self.access_token_url, headers=headers)
            response.raise_for_status()  # Raise exception for non-200 status codes
            
            result = response.json()
            return result.get('access_token')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None

    def generate_password(self):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{self.business_shortcode}{self.passkey}{timestamp}"
        return b64encode(password_str.encode()).decode(), timestamp

    def initiate_stk_push(self, phone_number, amount, order_id):
        try:
            access_token = self.get_access_token()
            if not access_token:
                return False, "Could not get access token"

            password, timestamp = self.generate_password()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            }
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.business_shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": f"{settings.BASE_URL}/mpesa/callback/",
                "AccountReference": f"ShopEase-{order_id}",
                "TransactionDesc": f"Payment for order {order_id}"
            }

            response = requests.post(self.stk_push_url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return True, result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error initiating STK push: {str(e)}")
            return False, str(e)

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
    cart = request.user.cart
    cart_items = cart.cartitem_set.all()
    
    if not cart_items.exists():
        messages.error(request, 'Your cart is empty')
        return redirect('shopease:cart')

    if request.method == 'POST':
        payment_plan = request.POST.get('payment_plan', 'full')
        total_amount = cart.get_total()
        
        # Create the order
        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            payment_plan=payment_plan,
            delivery_status='pending'
        )

        # Create payment plan details if installment selected
        if payment_plan == 'installment':
            monthly_amount = total_amount / 3
            for i in range(3):
                PaymentPlan.objects.create(
                    order=order,
                    installment_number=i + 1,
                    amount=monthly_amount,
                    due_date=timezone.now() + timezone.timedelta(days=30 * (i + 1)),
                    status='pending'
                )
            order.delivery_status = 'awaiting_payment'
        else:
            # For full payment, mark as paid and ready for delivery
            order.payment_status = 'paid'
            order.delivery_status = 'processing'

        # Create order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )

        # Clear the cart
        cart_items.delete()
        order.save()

        # Redirect based on payment plan
        if payment_plan == 'installment':
            return redirect('shopease:installment_setup', order_id=order.id)
        else:
            return redirect('shopease:payment_processing', order_id=order.id)

    context = {
        'cart_items': cart_items,
        'total': cart.get_total(),
        'shipping_address': request.user.shipping_address,
    }
    return render(request, 'checkout.html', context)

@login_required
def installment_setup(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    payment_plans = order.paymentplan_set.all()
    
    context = {
        'order': order,
        'payment_plans': payment_plans,
        'monthly_amount': order.total_amount / 3,
    }
    return render(request, 'installment_setup.html', context)

@login_required
def payment_processing(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    
    context = {
        'order': order,
        'amount': order.total_amount if order.payment_plan == 'full' else order.paymentplan_set.filter(status='pending').first().amount,
    }
    return render(request, 'payment_processing.html', context)

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
    # Get or create the user's cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Get cart items with related product data
    cart_items = CartItem.objects.select_related('product').filter(cart=cart)
    
    # Calculate total price
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'monthly_payment': total_price / 3 if total_price else 0,
    }
    
    return render(request, 'cart.html', context)

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
        # Get the user's cart
        cart = Cart.objects.get(user=request.user)
        # Get the cart item that belongs to this cart
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        cart_item.delete()
        return JsonResponse({'status': 'success'})
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart.objects.get_or_create(user=request.user)[0]
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
            
        messages.success(request, 'Item added to cart successfully!')
        return redirect('shopease:product_detail', product_id=product_id)
    
    return redirect('shopease:product_detail', product_id=product_id)

@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    context = {
        'wishlist_items': wishlist_items
    }
    return render(request, 'wishlist.html', context)

@login_required
def add_to_wishlist(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login first'}, status=401)
        
    product = get_object_or_404(Product, id=product_id)
    
    # Check if the item exists in wishlist
    wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()
    
    if wishlist_item:
        # If it exists, remove it
        wishlist_item.delete()
        message = 'Product removed from wishlist'
        is_in_wishlist = False
    else:
        wishlist.products.add(product)
        messages.success(request, 'Product added to wishlist')
    
    return JsonResponse({
        'message': message,
        'is_in_wishlist': is_in_wishlist
    })

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
        'product': product
    }
    return render(request, 'product_details.html', context)

@login_required
def process_checkout(request):
    if request.method == 'POST':
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        
        # Process the order here
        # You might want to create an Order model and save the order details
        
        # Clear the cart after successful checkout
        cart_items.delete()
        
        messages.success(request, 'Order placed successfully!')
        return redirect('/')
    
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

def category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    
    # Pagination
    paginator = Paginator(products, 9)  # Show 9 products per page
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results.
        products = paginator.page(paginator.num_pages)
    
    context = {
        'category': category,
        'products': products,
        'categories': Category.objects.all(),
        'brands': Brand.objects.all(),
    }
    
    return render(request, 'categories.html', context)

@login_required
def add_review(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        # Create the review
        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment
        )
        
        return redirect('shopease:product_detail', product_id=product_id)
    
    return redirect('shopease:product_detail', product_id=product_id)

@login_required
def initiate_payment(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        
        # Get the amount based on payment plan
        if order.payment_plan == 'full':
            amount = order.total_amount
        else:
            current_installment = order.paymentplan_set.filter(status='pending').first()
            if not current_installment:
                return JsonResponse({'error': 'No pending installments found'}, status=400)
            amount = current_installment.amount

        # Get phone number from POST data
        phone_number = request.POST.get('phone_number')
        if not phone_number:
            return JsonResponse({'error': 'Phone number is required'}, status=400)

        # Format phone number (remove leading 0 and add country code if needed)
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif not phone_number.startswith('254'):
            phone_number = '254' + phone_number

        # Initiate M-Pesa payment
        mpesa = MpesaGateway()
        success, response = mpesa.initiate_stk_push(phone_number, amount, order.id)

        if success:
            # Store the checkout request ID for verification
            order.mpesa_checkout_request_id = response.get('CheckoutRequestID')
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Please check your phone to complete the payment',
                'checkout_request_id': response.get('CheckoutRequestID')
            })
        else:
            return JsonResponse({
                'success': False,
                'error': response
            }, status=400)

    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}")
        return JsonResponse({'error': 'An error occurred while processing payment'}, status=500)

@csrf_exempt
def mpesa_callback(request):
    try:
        data = json.loads(request.body)
        result = data.get('Body', {}).get('stkCallback', {})
        checkout_request_id = result.get('CheckoutRequestID')
        
        order = Order.objects.get(mpesa_checkout_request_id=checkout_request_id)
        
        if result.get('ResultCode') == 0:
            # Payment successful
            payment_details = result.get('CallbackMetadata', {}).get('Item', [])
            amount = next((item.get('Value') for item in payment_details if item.get('Name') == 'Amount'), None)
            mpesa_receipt = next((item.get('Value') for item in payment_details if item.get('Name') == 'MpesaReceiptNumber'), None)
            
            if order.payment_plan == 'full':
                order.payment_status = 'paid'
                order.delivery_status = 'processing'
            else:
                current_installment = order.paymentplan_set.filter(status='pending').first()
                if current_installment:
                    current_installment.mark_as_paid()
                    current_installment.mpesa_receipt = mpesa_receipt
                    current_installment.save()

            order.save()
            
            # Send success notification
            send_payment_success_notification(order)
            
        else:
            # Payment failed
            order.payment_status = 'failed'
            order.save()
            
            # Send failure notification
            send_payment_failure_notification(order)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error processing M-Pesa callback: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def account_dashboard(request):
    # Get order status filter
    order_status = request.GET.get('order_status', 'all')
    
    # Get user's orders
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    if order_status != 'all':
        orders = orders.filter(status=order_status)
    
    # Get user's transactions
    transactions = Transaction.objects.filter(
        order__user=request.user
    ).order_by('-created_at')
    
    context = {
        'orders': orders,
        'transactions': transactions,
    }
    return render(request, 'account/dashboard.html', context)