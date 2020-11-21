from django.urls import include, path
from rest_framework_nested import routers

from bat.company.urls import router
from bat.product.views.component import ProductViewSet
from bat.product.views.image import ProductImageViewSet, ImageListViewset, TestViewSet

product_parent_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)


product_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
product_router.register(
    "products", ProductViewSet, basename="company-product"
)


# product_image_router = routers.NestedSimpleRouter(
#     product_router, "products", lookup="product"
# )

# product_image_router.register(
#     "images", ProductImageViewSet, basename="company-product-images"
# )


product_image_router = routers.NestedSimpleRouter(
    product_router, "products", lookup="product"
)

product_image_router.register(
    "images", TestViewSet, basename="company-product-images"
)


app_name = "product"

urlpatterns = [
    path("", include(product_parent_router.urls)),
    path("", include(product_router.urls)),
    path("", include(product_image_router.urls)),
]
