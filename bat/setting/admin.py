from django.contrib import admin

from bat.setting.models import (
    Category,
    DeliveryTermName,
    DeliveryTerms,
    LogisticLeadTime,
    PaymentTerms,
    Status,
)

# Register your models here.


admin.site.register(Category)
admin.site.register(Status)
admin.site.register(PaymentTerms)
admin.site.register(DeliveryTermName)
admin.site.register(DeliveryTerms)
admin.site.register(LogisticLeadTime)
