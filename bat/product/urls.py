from django.urls import include, path
from rest_framework_nested import routers

from bat.company.urls import router
from bat.product.views.component import ProductViewSet, ComponentMeViewSet
from bat.product.views.product import (
    ProductVariationViewSet, ProductComponentViewSet, ProductRrpViewSet, ProductPackingBoxViewSet
    )
from bat.product.views.image import ProductImagesViewSet, ProductVariationImagesViewSet
from bat.company.views.file import (
    ComponentMeFilesViewSet,
)

product_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
product_router.register(
    "products", ProductViewSet, basename="company-product"
)

# product_variation_router = routers.NestedSimpleRouter(
#     product_router, "products", lookup="product"
# )
# product_variation_router.register(
#     "product-variations", ProductVariationViewSet, basename="company-product-Product-variation"
# )


product_variation_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
product_variation_router.register(
    "product-variations", ProductVariationViewSet, basename="company-Product-variation"
)

product_image_router = routers.NestedSimpleRouter(
    product_router, "products", lookup="object"
)

product_image_router.register(
    "images", ProductImagesViewSet, basename="company-product-images"
)


product_variation_image_router = routers.NestedSimpleRouter(
    product_variation_router, "product-variations", lookup="object"
)

product_variation_image_router.register(
    "images", ProductVariationImagesViewSet, basename="company-product-variation-images"
)


product_component_router = routers.NestedSimpleRouter(
    product_router, "products", lookup="product"
)

product_component_router.register(
    "components", ProductComponentViewSet, basename="company-product-components"
)


product_rrp_router = routers.NestedSimpleRouter(
    product_router, "products", lookup="product"
)

product_rrp_router.register(
    "rrps", ProductRrpViewSet, basename="company-product-rrps"
)

product_packingbox_router = routers.NestedSimpleRouter(
    product_router, "products", lookup="product"
)

product_packingbox_router.register(
    "packingboxes", ProductPackingBoxViewSet, basename="company-product-packingboxes"
)

componentme_router = routers.NestedSimpleRouter(
    product_router, "products", lookup="product"
)
componentme_router.register(
    "component-me", ComponentMeViewSet, basename="company-me"
)

componentme_file_router = routers.NestedSimpleRouter(
    componentme_router, "component-me", lookup="object"
)

componentme_file_router.register(
    "files", ComponentMeFilesViewSet, basename="company-component-me-files"
)


app_name = "product"

urlpatterns = [
    path("", include(product_router.urls)),
    path("", include(product_variation_router.urls)),
    path("", include(product_image_router.urls)),
    path("", include(product_variation_image_router.urls)),
    path("", include(product_component_router.urls)),
    path("", include(product_rrp_router.urls)),
    path("", include(product_packingbox_router.urls)),
    path("", include(componentme_router.urls)),
    path("", include(componentme_file_router.urls)),
]
