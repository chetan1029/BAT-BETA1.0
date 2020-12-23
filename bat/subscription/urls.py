from django.urls import include, path
from rest_framework_nested import routers

from bat.company.urls import router
from bat.subscription.views import SubscriptionViewSet

subscription_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
subscription_router.register(
    "subscription", SubscriptionViewSet, basename="company-subscription"
)

app_name = "subscription"
urlpatterns = [
    path("", include(subscription_router.urls))
]
