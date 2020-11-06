from django.urls import include, path

from rest_framework import permissions

from drf_yasg2.views import get_schema_view
from drf_yasg2 import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


app_name = "api"

urlpatterns = [
    path('doc/', schema_view.with_ui('swagger',
                                     cache_timeout=0), name='schema-swagger-ui'),
    path("", include("bat.users.urls", namespace="users")),
    path("", include("bat.core.urls", namespace="core")),
    path("", include("bat.company.urls", namespace="company")),
]
