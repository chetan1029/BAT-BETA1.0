from django.contrib import admin

from bat.market.models import (
    AmazonAccountCredentails,
    AmazonAccounts,
    AmazonCompany,
    AmazonMarketplace,
    AmazonOrder,
    AmazonOrderItem,
    AmazonOrderShipping,
    AmazonProduct,
    AmazonProductSessions,
    PPCCredentials,
    PPCProfile,
)

# Register your models here.

admin.site.register(AmazonMarketplace)
admin.site.register(AmazonAccounts)
admin.site.register(AmazonAccountCredentails)
admin.site.register(AmazonProduct)
admin.site.register(AmazonOrder)
admin.site.register(AmazonOrderItem)
admin.site.register(AmazonOrderShipping)
admin.site.register(AmazonCompany)
admin.site.register(PPCCredentials)
admin.site.register(PPCProfile)
admin.site.register(AmazonProductSessions)
