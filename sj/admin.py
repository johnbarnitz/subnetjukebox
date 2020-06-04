from django.contrib import admin

# Register your models here.

from .models import Subnet, User

admin.site.register(Subnet)
admin.site.register(User)