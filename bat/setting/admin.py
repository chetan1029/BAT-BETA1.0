from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin

from bat.setting.models import (
    Category,
    DeliveryTermName,
    DeliveryTerms,
    LogisticLeadTime,
    PaymentTerms,
    Status,
)

# Register your models here.


admin.site.register(
    Category,
    DraggableMPTTAdmin,
    list_display=("tree_actions", "indented_title"),
    list_display_links=("indented_title",),
)
admin.site.register(
    Status,
    DraggableMPTTAdmin,
    list_display=("tree_actions", "indented_title"),
    list_display_links=("indented_title",),
)
admin.site.register(PaymentTerms)
admin.site.register(DeliveryTermName)
admin.site.register(DeliveryTerms)
admin.site.register(LogisticLeadTime)
