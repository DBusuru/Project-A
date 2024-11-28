from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        null=True, 
        blank=True,
        default='profile_pics/default.png'
    )
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    
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



