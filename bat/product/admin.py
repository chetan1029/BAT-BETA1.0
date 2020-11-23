from django.contrib import admin

from bat.product.models import (
    Image,
    Product,
    ProductOption,
    ProductParent,
    ProductVariationOption,
)

admin.site.register(Image)
admin.site.register(Product)
admin.site.register(ProductOption)
admin.site.register(ProductParent)
admin.site.register(ProductVariationOption)
