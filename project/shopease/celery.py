from celery import Celery
from celery.schedules import crontab

app = Celery('shopease')

app.conf.beat_schedule = {
    'check-upcoming-installments': {
        'task': 'shopease.tasks.check_upcoming_installments',
        'schedule': crontab(hour=9, minute=0),  # Run daily at 9 AM
    },
    'check-overdue-payments': {
        'task': 'shopease.tasks.send_payment_overdue_notification',
        'schedule': crontab(hour=10, minute=0),  # Run daily at 10 AM
    },
    'check-defaulted-payments': {
        'task': 'shopease.tasks.check_defaulted_payments',
        'schedule': crontab(day_of_week='monday', hour=8, minute=0),  # Run weekly on Monday at 8 AM
    },
}