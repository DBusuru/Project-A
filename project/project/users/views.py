from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegistrationForm

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




def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the user
            login(request, user)  # Log in the user after registration
            return redirect('login')  # Redirect to home page or dashboard
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})
