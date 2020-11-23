from django.urls import include, path
from rest_framework_nested import routers

from bat.company.urls import router
from bat.product.views.component import ProductViewSet
from bat.product.views.image import ProductImagesViewSet, ProductVariationImagesViewSet

product_parent_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)


product_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
product_router.register(
    "products", ProductViewSet, basename="company-product"
)


product_image_router = routers.NestedSimpleRouter(
    product_router, "products", lookup="object"
)

product_image_router.register(
    "images", ProductImagesViewSet, basename="company-product-images"
)


# product_variation_image_router = routers.NestedSimpleRouter(
#     product_router, "products", lookup="object"
# )

# product_variation_image_router.register(
#     "images", ProductVariationImagesViewSet, basename="company-product-variation-images"
# )

app_name = "product"

urlpatterns = [
    path("", include(product_parent_router.urls)),
    path("", include(product_router.urls)),
    path("", include(product_image_router.urls)),
]
