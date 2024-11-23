from .models import CustomUser as User
from django.contrib.auth.forms import UserCreationForm


class RegistrationForm(UserCreationForm):
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
