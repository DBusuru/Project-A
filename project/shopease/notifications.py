from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
import africastalking

# Initialize Africa's Talking
africastalking.initialize(
    username=settings.AT_USERNAME,
    api_key=settings.AT_API_KEY
)
sms = africastalking.SMS

def send_payment_success_notification(order, payment_details):
    """Send payment success notification via email and SMS"""
    try:
        # Prepare context for email
        context = {
            'order': order,
            'amount': payment_details.get('amount'),
            'mpesa_receipt': payment_details.get('mpesa_receipt'),
            'payment_date': payment_details.get('payment_date'),
            'order_url': f"{settings.BASE_URL}{reverse('shopease:order_detail', args=[order.id])}",
        }
        
        if order.payment_plan == 'installment':
            installments = order.paymentplan_set.all()
            paid_installments = installments.filter(status='paid').count()
            remaining_balance = sum(i.amount for i in installments.filter(status='pending'))
            next_installment = installments.filter(status='pending').first()
            
            context.update({
                'current_installment': paid_installments,
                'remaining_balance': remaining_balance,
                'next_due_date': next_installment.due_date if next_installment else None,
                'all_installments_paid': not remaining_balance
            })

        # Send email
        email_html = render_to_string('emails/payment_success.html', context)
        email_subject = f'Payment Received - Order #{order.id}'
        
        send_mail(
            subject=email_subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            html_message=email_html
        )

        # Send SMS
        phone_number = order.user.profile.phone_number
        if phone_number:
            sms_message = (
                f"Payment of KES {payment_details['amount']} received for Order #{order.id}. "
                f"Receipt: {payment_details['mpesa_receipt']}. "
                f"Thank you for shopping with ShopEase!"
            )
            
            sms.send(sms_message, [phone_number])

    except Exception as e:
        logger.error(f"Error sending payment success notification: {str(e)}")

def send_payment_failure_notification(order, failure_details):
    """Send payment failure notification via email and SMS"""
    try:
        # Prepare context for email
        context = {
            'order': order,
            'amount': failure_details.get('amount'),
            'attempt_date': failure_details.get('attempt_date'),
            'failure_reason': failure_details.get('reason'),
            'retry_url': f"{settings.BASE_URL}{reverse('shopease:payment_processing', args=[order.id])}"
        }

        # Send email
        email_html = render_to_string('emails/payment_failure.html', context)
        email_subject = f'Payment Failed - Order #{order.id}'
        
        send_mail(
            subject=email_subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            html_message=email_html
        )

        # Send SMS
        phone_number = order.user.profile.phone_number
        if phone_number:
            sms_message = (
                f"Payment failed for Order #{order.id}. "
                f"Please check your email for details or try again: "
                f"{settings.BASE_URL}{reverse('shopease:payment_processing', args=[order.id])}"
            )
            
            sms.send(sms_message, [phone_number])

    except Exception as e:
        logger.error(f"Error sending payment failure notification: {str(e)}")

def send_installment_reminder(payment_plan):
    """Send reminder for upcoming installment payment"""
    try:
        context = {
            'order': payment_plan.order,
            'due_date': payment_plan.due_date,
            'amount': payment_plan.amount,
            'installment_number': payment_plan.installment_number,
            'payment_url': f"{settings.BASE_URL}{reverse('shopease:payment_processing', args=[payment_plan.order.id])}"
        }

        # Send email
        email_html = render_to_string('emails/installment_reminder.html', context)
        email_subject = f'Payment Reminder - Order #{payment_plan.order.id}'
        
        send_mail(
            subject=email_subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment_plan.order.user.email],
            html_message=email_html
        )

        # Send SMS
        phone_number = payment_plan.order.user.profile.phone_number
        if phone_number:
            sms_message = (
                f"Reminder: Installment payment of KES {payment_plan.amount} for Order "
                f"#{payment_plan.order.id} is due on {payment_plan.due_date.strftime('%d/%m/%Y')}. "
                f"Click here to pay: {context['payment_url']}"
            )
            
            sms.send(sms_message, [phone_number])

    except Exception as e:
        logger.error(f"Error sending installment reminder: {str(e)}")