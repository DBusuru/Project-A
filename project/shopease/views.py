from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .models import WishlistItem, Newsletter
from .utils import send_payment_success_notification, send_payment_failure_notification

# ... rest of your views code ... 