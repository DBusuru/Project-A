# Email Settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your_smtp_host'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@example.com'
EMAIL_HOST_PASSWORD = 'your_email_password'
DEFAULT_FROM_EMAIL = 'ShopEase <noreply@shopease.com>'

# Africa's Talking Settings (for SMS)
AT_USERNAME = 'your_username'
AT_API_KEY = 'your_api_key'