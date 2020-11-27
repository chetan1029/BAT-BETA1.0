from django.urls import include, path

from rest_framework import permissions

from bat.docs_utils import get_schema_view
from drf_yasg2 import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="Bat Beta API",
        default_version='v1',
        description="Bat - Business Automation",
        terms_of_service="https://thebatonline.com/terms",
        contact=openapi.Contact(email="chetan@volutz.com"),
    ),
    schemes=['HTTPS', 'HTTP'],
    public=True,
    permission_classes=(permissions.AllowAny,),
)


app_name = "api"

urlpatterns = [
    path('docs/', schema_view.with_ui('swagger',
                                      cache_timeout=0), name='schema-swagger-ui'),
    path("", include("bat.users.urls", namespace="users")),
    path("", include("bat.core.urls", namespace="core")),
    path("", include("bat.company.urls", namespace="company")),
    path("", include("bat.product.urls", namespace="product")),
    path("", include("bat.setting.urls", namespace="setting")),
]
