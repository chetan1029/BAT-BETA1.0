from django.urls import include, path
from rest_framework_nested import routers

from bat.company.urls import router
from bat.keywordtracking.views import (
    KeywordTrackingProductViewsets,
    OverallDashboardAPIView,
    ProductKeywordAPIView,
    ProductKeywordRankViewSet,
    ProductKeywordViewSet,
    SaveProductKeyword,
)

product_keyword_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
product_keyword_router.register(
    "product-keyword",
    ProductKeywordViewSet,
    basename="company-product-keyword",
)
product_keyword_rank_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
product_keyword_rank_router.register(
    "product-keyword-rank",
    ProductKeywordRankViewSet,
    basename="company-product-keyword-rank",
)

keyword_tracking_product_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
keyword_tracking_product_router.register(
    "keyword-tracking-products",
    KeywordTrackingProductViewsets,
    basename="keyword-tracking-products",
)

app_name = "keywordtracking"

urlpatterns = [
    path(
        "companies/<company_pk>/save/product-keywords",
        SaveProductKeyword.as_view(),
    ),
    path("", include(product_keyword_router.urls)),
    path("", include(product_keyword_rank_router.urls)),
    path("", include(keyword_tracking_product_router.urls)),
    path(
        "companies/<company_pk>/keyword-tracking/dashboard/",
        OverallDashboardAPIView.as_view(),
        name="keyword-tracking-dashboard",
    ),
    path(
        "companies/<company_pk>/keyword-tracking/<product_keyword_pk>/dashboard/",
        ProductKeywordAPIView.as_view(),
        name="product-keyword-dashboard",
    ),
]
