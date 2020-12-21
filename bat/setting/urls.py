from django.urls import include, path

from rest_framework_nested import routers

from bat.company.urls import router as company_router
from bat.setting.views import CategoryViewSet, StatusViewSet


category_router = routers.NestedSimpleRouter(
    company_router, "companies", lookup="company"
)
category_router.register(
    "categories", CategoryViewSet, basename="company-categories"
)

router = routers.SimpleRouter()

router.register("status", StatusViewSet)

app_name = "setting"
urlpatterns = router.urls
urlpatterns += [
    path("", include(category_router.urls)),
]
