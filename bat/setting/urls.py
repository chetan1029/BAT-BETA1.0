from django.urls import include, path
from rest_framework_nested import routers

from bat.company.urls import router as company_router
from bat.setting.views import CategoryViewSet, DeliveryTermNameViewSet, StatusViewSet

category_router = routers.NestedSimpleRouter(
    company_router, "companies", lookup="company"
)
category_router.register(
    "categories", CategoryViewSet, basename="company-categories"
)

deliverytermname_router = routers.NestedSimpleRouter(
    company_router, "companies", lookup="company"
)
deliverytermname_router.register(
    "delivery-terms", DeliveryTermNameViewSet, basename="delivery-terms-name"
)


router = routers.SimpleRouter()

router.register("status", StatusViewSet)


app_name = "setting"
urlpatterns = router.urls
urlpatterns += [
    path("", include(category_router.urls)),
    path("", include(deliverytermname_router.urls)),
]
