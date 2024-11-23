from django.urls import path
from . import views

urlpatterns = [
        path('', views.index, name='index'),
        path('checkout/', views.checkout, name='checkout'),
        path('product/', views.product, name='product'),
        path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
]