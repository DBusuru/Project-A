from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from users import views as user_views
from django.conf import settings
from django.conf.urls.static import static
from shopease.views import index  # changed from 'home' to 'index'

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
    path('', include('shopease.urls')),
    path('users/', include('users.urls')),
    path('login/', user_views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', index, name='index'),
    path('cart/', include('shopping_cart.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)