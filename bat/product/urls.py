from django.urls import path, include

from rest_framework_nested import routers

from bat.product.views.component import (ProductParentViewSet)
from bat.company.urls import router


product_parent_router = routers.NestedSimpleRouter(
    router, "companies", lookup='company')
product_parent_router.register('product_parent', ProductParentViewSet,
                               basename='company-product_parent')

app_name = "product"

urlpatterns = [
    path('', include(product_parent_router.urls)),
]
