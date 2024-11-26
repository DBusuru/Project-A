from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from .models import CustomUser

@receiver(post_save, sender=SocialAccount)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        # Set any default values or additional processing for new social users
        user.email_verified = True
        user.save()