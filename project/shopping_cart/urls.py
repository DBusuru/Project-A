from django.urls import path
from . import views

app_name = 'shopping_cart'

urlpatterns = [
    path('', views.cart_view, name='cart'),
]