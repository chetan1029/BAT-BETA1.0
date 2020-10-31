from django.contrib import admin

# Register your models here.

from bat.setting.models import Category, Status, PaymentTerms

admin.site.register(Category)
admin.site.register(Status)
admin.site.register(PaymentTerms)
