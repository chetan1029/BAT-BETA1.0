from django.urls import include, path
from drf_yasg2 import openapi
from rest_framework import permissions
from rest_framework.authtoken.views import obtain_auth_token
from bat.docs_utils import get_schema_view

schema_view = get_schema_view(
    openapi.Info(
        title="Bat Beta API",
        default_version="v1",
        description="Bat - Business Automation",
        terms_of_service="https://thebatonline.com/terms",
        contact=openapi.Contact(email="chetan@volutz.com"),
    ),
    schemes=["http", "https"],
    public=True,
    permission_classes=(permissions.AllowAny,),
)


app_name = "api"

urlpatterns = [
    path('docs/', schema_view.with_ui('swagger',
                                      cache_timeout=0), name='schema-swagger-ui'),
    # jwt
    # path("api-token-auth/", jwt_views.obtain_jwt_token),

    # path("api-token-verify/", jwt_views.verify_jwt_token),
    # path('auth/', include('rest_auth.urls')),
    # verifay mail (provide template name) # logic for verifay email address
    path("auth/registration/", include("rest_auth.registration.urls")),
    path("", include("bat.users.urls", namespace="users")),
    path("", include("bat.core.urls", namespace="core")),
    path("", include("bat.company.urls", namespace="company")),
    path("", include("bat.product.urls", namespace="product")),
    path("", include("bat.setting.urls", namespace="setting")),
]
