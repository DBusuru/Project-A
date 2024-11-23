from django.contrib import admin
from shopease.models import models_ as m


for model in m:
    admin.site.register(model)