from django.core.mail import send_mail
from django.conf import settings

def send_payment_success_notification(user, order):
    """Send email notification for successful payment"""
    subject = 'Payment Successful'
    message = f"""
    Dear {user.get_full_name() or user.username},
    
    Your payment for order #{order.id} was successful.
    Total amount paid: ${order.total}
    
    Thank you for shopping with us!
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )

def send_payment_failure_notification(user, order, error=None):
    """Send email notification for failed payment"""
    subject = 'Payment Failed'
    message = f"""
    Dear {user.get_full_name() or user.username},
    
    Your payment for order #{order.id} was unsuccessful.
    {f"Error: {error}" if error else ""}
    
    Please try again or contact our support team if you need assistance.
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    ) 