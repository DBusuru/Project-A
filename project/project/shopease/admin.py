from django.contrib import admin

from shopease.models import User,Order,OrderItem,UserCreationForm


# Register your models here.
admin.site.register(User)
admin.site.register(Order)
admin.site.register(OrderItem)


