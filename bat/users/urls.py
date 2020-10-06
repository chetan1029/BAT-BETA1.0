"""URL Patterns for User app."""
from django.contrib.auth import views as auth_views
from django.urls import path, re_path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path(
        "logout/",
        auth_views.LogoutView.as_view(template_name="user/logout.html"),
        name="logout",
    ),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="user/password_reset_form.html", success_url="done"
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="user/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    re_path(
        r"^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="user/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="user/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path(
        "password-change/",
        views.CustomPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password-change/done/",
        views.CustomPasswordChangeView.as_view(),
        name="password_change_done",
    ),
    path("signup/", views.SignUp.as_view(), name="signup"),
    # path("signup/", views.SignUpClose.as_view(), name="signup"),
    path(
        "company-login/",
        views.CompanyLoginView.as_view(),
        name="company_login",
    ),
    path(
        "update-profile/", views.UpdateProfile.as_view(), name="update_profile"
    ),
    path(
        "my-companies/", views.MyCompaniesView.as_view(), name="my_companies"
    ),
    path(
        "roles/<int:pk>/edit/",
        views.RoleEditView.as_view(),
        name="update_roles",
    ),
    path("roles/", views.RolesView.as_view(), name="list_roles"),
]
