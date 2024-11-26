from django.contrib import admin
from shopease.models import CartItem, Product, Category, Brand, ProductVariant, Review, Order, OrderItem, Wishlist


admin.site.register(CartItem)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(ProductVariant)
admin.site.register(Review)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Wishlist)