from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('account/', views.account_dashboard, name='account_dashboard'),
    path('account/orders/', views.account_orders, name='account_orders'),
    path('account/installments/', views.account_installments, name='account_installments'),
    path('account/profile/', views.account_profile, name='account_profile'),
    path('account/password_change/', 
         auth_views.PasswordChangeView.as_view(
             template_name='account_password_change.html',
             success_url='/users/account/profile/'
         ),
         name='password_change'),
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='password_reset.html',
             email_template_name='password_reset_email.html',
             subject_template_name='password_reset_subject.txt',
             success_url='/users/password-reset/done/'
         ),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password_reset_confirm.html',
             success_url='/users/password-reset-complete/'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='password_reset_complete.html'
         ),
         name='password_reset_complete'),
    path('pay-installment/<int:installment_id>/', views.pay_installment, name='pay_installment'),
]