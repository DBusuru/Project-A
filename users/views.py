from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, LoginForm
from shopease.models import Order, InstallmentPlan, OrderTracking, BNPLInstallment
from django.db.models import Sum
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import ValidationError

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
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # or wherever you want to redirect after login
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'login.html')

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
def account_dashboard(request):
    active_installments = InstallmentPlan.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-created_at')
    
    context = {
        'active_installments': active_installments,
    }
    return render(request, 'account_dashboard.html', context)

@login_required
def account_orders(request):
    order_list = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(order_list, 10)  # Show 10 orders per page
    page = request.GET.get('page')
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    
    context = {
        'orders': orders,
    }
    return render(request, 'account_orders.html', context)

@login_required
def account_installments(request):
    installment_list = BNPLInstallment.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'installments': installment_list,
        'active_tab': 'installments'
    }
    
    return render(request, 'my_installments.html', context)

@login_required
def account_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.phone_number = request.POST.get('phone_number')
        user.address = request.POST.get('address')
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            # Delete old picture if it exists
            if user.profile_picture:
                user.profile_picture.delete()
            user.profile_picture = request.FILES['profile_picture']
        
        try:
            user.full_clean()
            user.save()
            messages.success(request, 'Profile updated successfully!')
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
        
        return redirect('users:account_profile')
    
    return render(request, 'account_profile.html')

@login_required
def pay_installment(request, installment_id):
    if request.method == 'POST':
        installment = get_object_or_404(BNPLInstallment, id=installment_id, user=request.user)
        # Add your payment processing logic here
        messages.success(request, 'Payment processed successfully!')
        return redirect('users:my_installments')