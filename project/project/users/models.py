from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    profile_pic = models.ImageField(upload_to='profiles/')
    phone_number = models.CharField(max_length=16)

    def __str__(self):
        return self.username

