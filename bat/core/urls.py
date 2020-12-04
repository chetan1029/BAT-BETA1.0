
from django.urls import path, include

from rest_framework_nested.routers import DefaultRouter

from bat.core.views import CurrencyChoicesViewSet

app_name = "core"

router = DefaultRouter()

router.register(
    "currency-choices", CurrencyChoicesViewSet, basename="currency-choices"
)

urlpatterns = [
    path("", include(router.urls))
]
