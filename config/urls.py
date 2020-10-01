"""URL Patterns for the project."""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.decorators.csrf import csrf_exempt
from django_ses.views import handle_bounce

urlpatterns = [
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    path("admin/django-ses/", include("django_ses.urls")),
    # email
    path("ses/bounce/", csrf_exempt(handle_bounce)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    # App Url Patterns
    path("accounts/", include("bat.users.urls", namespace="accounts")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("setting/", include("bat.setting.urls", namespace="setting")),
    path("", include("bat.core.urls", namespace="core")),
    # https://docs.djangoproject.com/en/dev/topics/i18n/translation/#language-prefix-in-url-patterns
    prefix_default_language=False,
)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls))
        ] + urlpatterns
