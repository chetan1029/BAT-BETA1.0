"""URL Patterns for Company app."""

from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "company"

router = routers.DefaultRouter()
router.register(r"settings/payment-terms", views.SettingsPaymentTermsList)
urlpatterns = [path("api/", include(router.urls))]
urlpatterns += [
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
    # Vendors
    path(
        "vendor", views.VendorDashboardView.as_view(), name="vendor_dashboard"
    ),
    path(
        "vendor/invite", views.VendorInviteView.as_view(), name="vendor_invite"
    ),
    # Member
    path(
        "settings/member",
        views.SettingsMemberListView.as_view(),
        name="settingsmember_list",
    ),
    path(
        "settings/member/<int:pk>",
        views.SettingsMemberDetailView.as_view(),
        name="settingsmember_detail",
    ),
    path(
        "settings/invite",
        views.SettingsMemberCreateView.as_view(),
        name="settingsmember_create",
    ),
    # Payment Terms
    # path(
    #     "settings/payment-terms",
    #     views.SettingsPaymentTermsActiveListView.as_view(),
    #     name="settingspaymentterms_list",
    # ),
    # path(
    #     "settings/payment-terms/archived",
    #     views.SettingsPaymentTermsArchivedListView.as_view(),
    #     name="settingspaymenttermsarchived_list",
    # ),
    # path(
    #     "settings/payment-terms/add",
    #     views.SettingsPaymentTermsCreateView.as_view(),
    #     name="settingspaymentterms_create",
    # ),
    # path(
    #     "settings/payment-terms/<int:pk>/edit/",
    #     views.SettingsPaymentTermsUpdateView.as_view(),
    #     name="settingspaymentterms_update",
    # ),
    # path(
    #     "settings/payment-terms/<int:pk>/archived/",
    #     views.SettingsPaymentTermsArchivedView.as_view(),
    #     name="settingspaymentterms_archived",
    # ),
    # path(
    #     "settings/payment-terms/<int:pk>/delete/",
    #     views.SettingsPaymentTermsDeleteView.as_view(),
    #     name="settingspaymentterms_delete",
    # ),
    # path(
    #     "settings/payment-terms/<int:pk>/restore/",
    #     views.SettingsPaymentTermsRestoreView.as_view(),
    #     name="settingspaymentterms_restore",
    # ),
    # Membership
    path(
        "settings/membership",
        views.MembershipView.as_view(),
        name="membership",
    ),
    # Bank
    path(
        "settings/bank",
        views.SettingsBankListView.as_view(),
        name="settingsbank_list",
    ),
    path(
        "settings/bank/add",
        views.SettingsBankCreateView.as_view(),
        name="settingsbank_create",
    ),
    path(
        "settings/bank/<int:pk>",
        views.SettingsBankDetailView.as_view(),
        name="settingsbank_detail",
    ),
    path(
        "settings/bank/<int:pk>/delete/",
        views.SettingsBankDeleteView.as_view(),
        name="settingsbank_delete",
    ),
    # Location
    path(
        "settings/location",
        views.SettingsLocationListView.as_view(),
        name="settingslocation_list",
    ),
    path(
        "settings/location/add",
        views.SettingsLocationCreateView.as_view(),
        name="settingslocation_create",
    ),
    path(
        "settings/location/<int:pk>/edit/",
        views.SettingsLocationUpdateView.as_view(),
        name="settingslocation_update",
    ),
    path(
        "settings/location/<int:pk>/delete/",
        views.SettingsLocationDeleteView.as_view(),
        name="settingslocation_delete",
    ),
    # Packing Box
    path(
        "settings/packing-box",
        views.SettingsPackingBoxListView.as_view(),
        name="settingspackingbox_list",
    ),
    path(
        "settings/packing-box/add",
        views.SettingsPackingBoxCreateView.as_view(),
        name="settingspackingbox_create",
    ),
    path(
        "settings/packing-box/<int:pk>/edit/",
        views.SettingsPackingBoxUpdateView.as_view(),
        name="settingspackingbox_update",
    ),
    path(
        "settings/packing-box/<int:pk>/delete/",
        views.SettingsPackingBoxDeleteView.as_view(),
        name="settingspackingbox_delete",
    ),
    # Company HSCode
    path(
        "settings/hscode",
        views.SettingsHsCodeListView.as_view(),
        name="settingshscode_list",
    ),
    path(
        "settings/hscode/add",
        views.SettingsHsCodeCreateView.as_view(),
        name="settingshscode_create",
    ),
    path(
        "settings/hscode/<int:pk>/edit/",
        views.SettingsHsCodeUpdateView.as_view(),
        name="settingshscode_update",
    ),
    path(
        "settings/hscode/<int:pk>/delete/",
        views.SettingsHsCodeDeleteView.as_view(),
        name="settingshscode_delete",
    ),
    # Tax
    path(
        "settings/tax",
        views.SettingsTaxListView.as_view(),
        name="settingstax_list",
    ),
    path(
        "settings/tax/add",
        views.SettingsTaxCreateView.as_view(),
        name="settingstax_create",
    ),
    path(
        "settings/tax/<int:pk>/edit/",
        views.SettingsTaxUpdateView.as_view(),
        name="settingstax_update",
    ),
    path(
        "settings/tax/<int:pk>/delete/",
        views.SettingsTaxDeleteView.as_view(),
        name="settingstax_delete",
    ),
]
