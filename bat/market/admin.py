from django.contrib import admin

from bat.market.models import (
    AmazonAccountCredentails,
    AmazonAccounts,
    AmazonMarketplace,
    AmazonOrder,
    AmazonOrderItem,
    AmazonOrderShipping,
    AmazonProduct,
)

# Register your models here.

admin.site.register(AmazonMarketplace)
admin.site.register(AmazonAccounts)
admin.site.register(AmazonAccountCredentails)
admin.site.register(AmazonProduct)
admin.site.register(AmazonOrder)
admin.site.register(AmazonOrderItem)
admin.site.register(AmazonOrderShipping)
