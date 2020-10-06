"""URL Patterns for Setting app."""

from django.urls import path

from . import views

app_name = "company"

urlpatterns = [
    # Account Setup
    path(
        "account-setup", views.AccountSetupView.as_view(), name="account_setup"
    ),
    # Company Settings
    path(
        "company-profile",
        views.CompanyProfileView.as_view(),
        name="company_profile",
    ),
    # Member
    path(
        "member",
        views.CompanyMemberListView.as_view(),
        name="companymember_list",
    ),
]
