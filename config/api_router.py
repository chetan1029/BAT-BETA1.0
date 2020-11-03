from django.urls import include, path
from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from bat.users.api.views import UserViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)


app_name = "api"
urlpatterns = router.urls

urlpatterns += [
    path("", include("bat.users.urls", namespace="users")),
    path("", include("bat.core.urls", namespace="core")),
    path("", include("bat.company.urls", namespace="company")),
]
