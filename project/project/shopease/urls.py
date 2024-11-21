from django.urls import path

from.import views
from django.contrib.auth.views import LogoutView

from .views import update_profile

urlpatterns = [
        path('', views.index, name='index'),
        path('checkout/', views.checkout, name='checkout'),
        path('product/', views.product, name='product'),
        path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
        path('login/', views.login_view,  name='login'),
        path('logout/', views.logout_view , name='logout'),
        path('register/', views.register_view, name='register'),
        path('account/', views.account, name='account'),
        path('update-profile/', update_profile, name='update_profile'),

]