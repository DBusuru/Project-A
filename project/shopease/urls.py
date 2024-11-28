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
        path('checkout/process/', views.process_checkout, name='process_checkout'),
        path('product/', views.product_list, name='product'),
        path('product/<int:product_id>/', views.product_detail, name='product_detail'),
        path('newsletter-signup/', views.newsletter_signup, name='newsletter_signup'),
        path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
        path('category/<int:category_id>/', views.category_view, name='category'),
        path('product/<int:product_id>/review/', views.add_review, name='add_review'),
        path('product/<int:product_id>/wishlist/', views.add_to_wishlist, name='add_to_wishlist'),
        path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
        path('installment-setup/<int:order_id>/', views.installment_setup, name='installment_setup'),
        path('payment-processing/<int:order_id>/', views.payment_processing, name='payment_processing'),
        path('account/dashboard/', views.account_dashboard, name='account_dashboard'),
]