from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from .models import PaymentPlan
from .utils.notifications import send_installment_reminder

@shared_task
def check_upcoming_installments():
    """
    Check for upcoming installments and send reminders
    Runs daily to check for payments due in the next 3 days
    """
    reminder_date = timezone.now().date() + timedelta(days=3)
    upcoming_payments = PaymentPlan.objects.filter(
        status='pending',
        due_date__date=reminder_date
    )

    for payment in upcoming_payments:
        send_installment_reminder(payment)

@shared_task
def send_payment_overdue_notification():
    """
    Check for overdue payments and send notifications
    Runs daily to check for missed payments
    """
    overdue_payments = PaymentPlan.objects.filter(
        status='pending',
        due_date__lt=timezone.now()
    )

    for payment in overdue_payments:
        # Update payment status to overdue
        payment.status = 'overdue'
        payment.save()
        
        # Send overdue notification
        context = {
            'order': payment.order,
            'amount': payment.amount,
            'due_date': payment.due_date,
            'days_overdue': (timezone.now().date() - payment.due_date.date()).days,
            'payment_url': f"{settings.BASE_URL}/payment/{payment.order.id}/"
        }
        
        # Send email
        email_html = render_to_string('emails/payment_overdue.html', context)
        send_mail(
            subject=f'Payment Overdue - Order #{payment.order.id}',
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment.order.user.email],
            html_message=email_html
        )

        # Send SMS
        phone_number = payment.order.user.profile.phone_number
        if phone_number:
            sms_message = (
                f"REMINDER: Your payment of KES {payment.amount} for Order "
                f"#{payment.order.id} is overdue. Please make payment to avoid "
                f"order cancellation. Pay now: {context['payment_url']}"
            )
            
            sms.send(sms_message, [phone_number])

@shared_task
def check_defaulted_payments():
    """
    Check for severely overdue payments and handle defaults
    Runs weekly to check for payments more than 30 days overdue
    """
    default_threshold = timezone.now() - timedelta(days=30)
    defaulted_payments = PaymentPlan.objects.filter(
        status='overdue',
        due_date__lt=default_threshold
    )

    for payment in defaulted_payments:
        # Update payment and order status
        payment.status = 'defaulted'
        payment.save()
        
        order = payment.order
        order.payment_status = 'defaulted'
        order.save()
        
        # Calculate refund amount based on paid installments
        paid_amount = order.paymentplan_set.filter(
            status='paid'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Send default notification with refund information
        context = {
            'order': order,
            'paid_amount': paid_amount,
            'refund_product': get_equivalent_product(paid_amount)
        }
        
        email_html = render_to_string('emails/payment_default.html', context)
        send_mail(
            subject=f'Important Notice - Order #{order.id}',
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            html_message=email_html
        )