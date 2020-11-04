from django.urls import include, path

app_name = "api"

urlpatterns = [
    path("", include("bat.users.urls", namespace="users")),
    path("", include("bat.core.urls", namespace="core")),
    path("", include("bat.company.urls", namespace="company")),
]
