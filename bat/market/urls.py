from django.urls import include, path
from rest_framework import routers
from rest_framework_nested import routers as nested_routers

from bat.company.urls import router as company_router
from bat.market.views import (
    AccountsReceiveAmazonCallback,
    AmazonAccountsAuthorization,
    AmazonMarketplaceViewsets,
    AmazonOrderViewsets,
    AmazonProductViewsets,
    TestAmazonClientCatalog,
)

router = routers.SimpleRouter()

router.register("amazon-marketplaces", AmazonMarketplaceViewsets)


amazon_product_router = nested_routers.NestedSimpleRouter(
    company_router, "companies", lookup="company"
)
amazon_product_router.register(
    "amazon-product", AmazonProductViewsets, basename="company-amazon-product"
)

amazon_order_router = nested_routers.NestedSimpleRouter(
    company_router, "companies", lookup="company"
)
amazon_order_router.register(
    "amazon-order", AmazonOrderViewsets, basename="company-amazon-order"
)


app_name = "market"

urlpatterns = router.urls

urlpatterns = urlpatterns + [
    path(
        "companies/<company_pk>/amazon-marketplaces/<market_pk>/authorize/",
        AmazonAccountsAuthorization.as_view(),
    ),
    path(
        "auth-callback/amazon-marketplaces/",
        AccountsReceiveAmazonCallback.as_view(),
    ),
    path("", include(amazon_product_router.urls)),
    path("", include(amazon_order_router.urls)),
    path("test-amazon-client/catalog", TestAmazonClientCatalog.as_view()),
]
