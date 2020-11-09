from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from rest_framework.authtoken.views import obtain_auth_token

# rest-auth
from rest_auth.views import PasswordResetConfirmView
from rest_auth.registration.views import VerifyEmailView
from allauth.account.views import confirm_email
# jwt
from rest_framework_jwt import views as jwt_views


urlpatterns = [

    # jwt
    path('api-token-auth/', jwt_views.obtain_jwt_token),
    path('api-token-refresh/', jwt_views.refresh_jwt_token),
    path('api-token-verify/', jwt_views.verify_jwt_token),

    # rest-auth urls
    path('auth/', include('users.rest_auth_custome_urls')),
    # path('auth/', include('rest_auth.urls')),

    # verifay mail (provide template name) # logic for verifay email address
    path('auth/registration/', include('rest_auth.registration.urls')),
    path('password/reset/confirm/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('registration/account-confirm-email/<key>', confirm_email,
         name='account_confirm_email'),  # redirect to verify-email and POST key
    path('verify-email/', VerifyEmailView.as_view(),
         name='verify_email'),  # POST value of key

    # pages
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path(
        "about/", TemplateView.as_view(template_name="pages/about.html"), name="about"
    ),

    # Django Admin, use {% url 'admin:index' %}
    path("admin/", admin.site.urls),
    # defender admin
    path('admin/defender/', include('defender.urls')),

    # User management
    # path("users/", include("bat.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),

    # Django Invitation
    path("invitations/", include("invitations.urls", namespace="invitations")),

    # API base url
    path("api/", include("config.api_router")),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API URLS
urlpatterns += [
    # DRF auth token
    path("auth-token/", obtain_auth_token),
]

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
            path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
