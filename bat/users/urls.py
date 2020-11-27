from django.urls import include, path
from rest_framework_nested.routers import DefaultRouter
from allauth.account.views import confirm_email
from rest_auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from rest_auth.registration.views import VerifyEmailView

from rest_framework_jwt import views as jwt_views

from bat.users.views import InvitationViewSet, RolesandPermissionsViewSet, UserViewSet

app_name = "users"

router = DefaultRouter()

router.register("user", UserViewSet)
router.register("invitations", InvitationViewSet)
router.register(
    "role-permissions", RolesandPermissionsViewSet, basename="role-permissions"
)


urlpatterns = [path("", include(router.urls))]

urlpatterns += [
    path("password/reset/", PasswordResetView.as_view(),
         name="rest_password_reset"),
    path(
        "password/reset/confirm/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(),
         name="rest_password_reset_confirm"),
    path("login/", LoginView.as_view(), name="rest_login"),
    # URLs that require a user to be logged in with a valid session / token.
    path("logout/", LogoutView.as_view(), name="rest_logout"),
    path("password/change/", PasswordChangeView.as_view(),
         name="rest_password_change"),
    path("token-refresh/", jwt_views.refresh_jwt_token),
    path(
        "registration/account-confirm-email/<key>",
        confirm_email,
        name="account_confirm_email",
    ),  # redirect to verify-email and POST key
    path(
        "verify-email/", VerifyEmailView.as_view(), name="verify_email"
    ),  # POST value of key
]
