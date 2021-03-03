from django.contrib import admin
from bat.market.models import AmazonMarketplace, AmazonAccounts

# Register your models here.

admin.site.register(AmazonMarketplace)
admin.site.register(AmazonAccounts)
