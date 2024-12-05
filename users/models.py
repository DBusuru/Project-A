from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.conf import settings
from decimal import Decimal

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])]
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def get_social_auth(self):
        """Return social auth account if exists"""
        return self.socialaccount_set.first()

    def is_social_account(self):
        """Check if user logged in via social auth"""
        return self.socialaccount_set.exists()

class InstallmentPlan(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_installment_plans')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2)
    number_of_months = models.IntegerField()
    start_date = models.DateField(auto_now_add=True)
    next_payment_date = models.DateField()
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"Installment Plan for {self.user.email} - {self.total_amount}"

class InstallmentPayment(models.Model):
    installment_plan = models.ForeignKey(InstallmentPlan, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"Payment of {self.amount_paid} for {self.installment_plan}"

    def save(self, *args, **kwargs):
        # Update the remaining balance in the installment plan
        self.installment_plan.remaining_balance -= self.amount_paid
        self.installment_plan.save()
        super().save(*args, **kwargs)



