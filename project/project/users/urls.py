from django.urls import path
from django.contrib.auth import views as a_views
from . import views

urlpatterns = [
    # path('login/', views.login_view,  name='login'),
    path('login/', a_views.LoginView.as_view(template_name = 'login.html'),  name='login'),
    path('logout/', a_views.LogoutView.as_view() , name='logout'),
    path('register/', views.register_view, name='register'),
    path('account/', views.account, name='account'),

]