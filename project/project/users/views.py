from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import RegistrationForm

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def account(request):
    if request.method == 'POST':
        if 'profile_picture' in request.FILES:
            profile = request.user
            profile.profile_picture = request.FILES['profile_picture']
            profile.save()
        return redirect('account')
    return render(request, 'account.html')