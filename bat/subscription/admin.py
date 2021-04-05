from django.contrib import admin
from bat.subscription import models

admin.site.register(models.Plan)
admin.site.register(models.Subscription)
admin.site.register(models.SubscriptionTransaction)
admin.site.register(models.Quota)
admin.site.register(models.PlanQuota)
