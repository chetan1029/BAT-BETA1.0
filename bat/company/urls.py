"""URL Patterns for Setting app."""

from django.urls import path

from . import views

app_name = "company"

urlpatterns = [
    # global Settings
    # Account Setup
    path(
        "account-setup", views.AccountSetupView.as_view(), name="account_setup"
    )
]
