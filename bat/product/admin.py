from django.contrib import admin

from bat.product.models import (
    Product,
    ProductOption,
    ProductParent,
    ProductVariationOption,
)

admin.site.register(Product)
admin.site.register(ProductOption)
admin.site.register(ProductParent)
admin.site.register(ProductVariationOption)
