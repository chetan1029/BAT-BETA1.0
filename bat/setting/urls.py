from django.urls import include, path

from rest_framework_nested import routers

from bat.company.urls import router
from bat.setting.views import CategoryViewSet


category_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
category_router.register(
    "categories", CategoryViewSet, basename="company-categories"
)

app_name = "setting"
urlpatterns = [
    path("", include(category_router.urls)),
]
