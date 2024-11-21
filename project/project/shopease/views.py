from django.shortcuts import render,redirect
from django.dispatch import receiver
from.forms import RegisterForm
from django.db.models.signals import post_save
from.models import OrderItem
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

# Create your views here.

def index(request):
    return render(request, 'index.html')

def checkout(request):
    return render(request, 'checkout.html')

def product(request):
    return render(request, 'product.html')

@login_required
def delete_product(request, product_id):
    try:
        # Fetch the order item belonging to the logged-in user
        order_item = OrderItem.objects.get(
            id=product_id,
            order__user=request.user,
            order__is_complete=False
        )
        order_item.delete()
    except OrderItem.DoesNotExist:
        raise Http404("Product not found or you don't have permission to delete it.")
    return redirect('checkout')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')  # Replace 'home' with your desired redirect URL name
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')

    # Redirect to the login page or any other page

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the user
            login(request, user)  # Log in the user after registration
            return redirect('login')  # Redirect to home page or dashboard
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def account(request):
    # You can add logic here to display user details or a dashboard
    return render(request, 'account.html')

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('my_account')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

@login_required
def update_profile(request):
    if request.method == 'POST':
        profile = request.user.profile
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
            profile.save()
        return redirect('account')


