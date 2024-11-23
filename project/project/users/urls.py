from django.urls import path
from django.contrib.auth import views as a_views
from . import views

urlpatterns = [
    path('login/', views.login_view,  name='login'),
    path('logout/', a_views.LogoutView.as_view() , name='logout'),
    path('register/', views.register_view, name='register'),
]