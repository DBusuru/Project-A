from django.urls import path
from . import views
app_name = 'shopease'  # Add this namespace
urlpatterns = [
        path('', views.index, name='index'),
        path('hot-deals/', views.hot_deals, name='hot_deals'),
        path('categories/', views.categories, name='categories'),
        path('laptops/', views.laptops, name='laptops'),
        path('smartphones/', views.smartphones, name='smartphones'),
        path('accessories/', views.accessories, name='accessories'),
        path('search/', views.search_products, name='search_products'),
        path('wishlist/', views.wishlist, name='wishlist'),
        path('cart/', views.view_cart, name='view_cart'),
        path('checkout/', views.checkout, name='checkout'),
        path('product/', views.product_list, name='product'),
        path('product/<int:product_id>/', views.product_detail, name='product_detail'),
        path('newsletter-signup/', views.newsletter_signup, name='newsletter_signup'),
       
]