from django.db.models import Q
from decimal import Decimal
from .models import Product

def get_equivalent_product(paid_amount):
    """
    Find a suitable alternative product based on the amount paid.
    
    Args:
        paid_amount (Decimal): The total amount paid by the customer
        
    Returns:
        Product: A product with value close to the paid amount
    """
    # Define acceptable price range (±10% of paid amount)
    min_price = paid_amount * Decimal('0.9')
    max_price = paid_amount * Decimal('1.1')
    
    # First try to find products within the exact price range
    products = Product.objects.filter(
        price__gte=min_price,
        price__lte=max_price,
        stock__gt=0,
        is_active=True
    ).order_by('price')
    
    if products.exists():
        return products.first()
    
    # If no products found, try to find the closest match below paid amount
    lower_product = Product.objects.filter(
        price__lt=paid_amount,
        stock__gt=0,
        is_active=True
    ).order_by('-price').first()
    
    # Find the closest match above paid amount
    higher_product = Product.objects.filter(
        price__gt=paid_amount,
        stock__gt=0,
        is_active=True
    ).order_by('price').first()
    
    # Compare which product is closer to paid amount
    if lower_product and higher_product:
        lower_diff = paid_amount - lower_product.price
        higher_diff = higher_product.price - paid_amount
        return lower_product if lower_diff < higher_diff else higher_product
    
    return lower_product or higher_product

def process_default_order(order):
    """
    Process an order that has defaulted on payments.
    
    Args:
        order (Order): The original order that defaulted
    
    Returns:
        tuple: (new_order, refund_product)
    """
    from .models import Order, OrderItem
    
    # Calculate total paid amount
    paid_amount = order.paymentplan_set.filter(
        status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Get equivalent product
    refund_product = get_equivalent_product(paid_amount)
    
    if refund_product:
        # Create new order for the refund product
        new_order = Order.objects.create(
            user=order.user,
            total_amount=refund_product.price,
            payment_status='paid',
            delivery_status='processing',
            original_order=order,
            order_type='refund'
        )
        
        # Create order item
        OrderItem.objects.create(
            order=new_order,
            product=refund_product,
            quantity=1,
            price=refund_product.price
        )
        
        # Update stock
        refund_product.stock -= 1
        refund_product.save()
        
        # Update original order status
        order.status = 'defaulted_processed'
        order.save()
        
        return new_order, refund_product
    
    return None, None

def send_default_processing_notification(order, new_order, refund_product):
    """
    Send notification about the processed default and refund product.
    
    Args:
        order (Order): Original defaulted order
        new_order (Order): New order with refund product
        refund_product (Product): The product being offered as refund
    """
    context = {
        'order': order,
        'new_order': new_order,
        'refund_product': refund_product,
        'claim_url': f"{settings.BASE_URL}{reverse('shopease:claim_refund_product', args=[new_order.id])}",
    }
    
    # Send email notification
    email_html = render_to_string('emails/payment_default.html', context)
    send_mail(
        subject=f'Important: Alternative Product Offer - Order #{order.id}',
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
        html_message=email_html
    )
    
    # Send SMS notification
    phone_number = order.user.profile.phone_number
    if phone_number:
        sms_message = (
            f"Important: Your order #{order.id} has been updated with an "
            f"alternative product offer. Please check your email for details "
            f"or visit: {context['claim_url']}"
        )
        sms.send(sms_message, [phone_number])