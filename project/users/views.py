from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .forms import CustomUserCreationForm, LoginForm, ProfilePictureForm
from shopease.models import Order, Transaction

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

@login_required
def account(request):
    if request.method == 'POST':
        if 'profile_pic' in request.FILES:
            request.user.profile_pic = request.FILES['profile_pic']
            request.user.save()
            messages.success(request, 'Profile picture updated successfully!')
            return redirect('users:account')
    
    return render(request, 'account.html')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {
        'form': form,
        'next': request.GET.get('next', '')
    })

@login_required
def logout_view(request):
    logout(request)
    return redirect('users:login')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'register.html', {'form': form})

@login_required
def profile_view(request):
    return render(request, 'profile.html', {
        'user': request.user
    })

@login_required
def dashboard(request):
    order_status = request.GET.get('order_status', 'all')
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    if order_status != 'all':
        orders = orders.filter(status=order_status)

    transactions = Transaction.objects.filter(order__user=request.user).order_by('-created_at')

    # Paginate orders and transactions
    order_paginator = Paginator(orders, 5)  # 5 orders per page
    transaction_paginator = Paginator(transactions, 5)  # 5 transactions per page

    order_page_number = request.GET.get('order_page')
    transaction_page_number = request.GET.get('transaction_page')

    orders_page = order_paginator.get_page(order_page_number)
    transactions_page = transaction_paginator.get_page(transaction_page_number)

    context = {
        'orders': orders_page,
        'transactions': transactions_page,
        'order_status': order_status,
    }
    return render(request, 'dashboard.html', context)

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile picture updated successfully.')
            return redirect('users:dashboard')
        else:
            messages.error(request, 'Error updating profile picture.')
    return redirect('users:dashboard')