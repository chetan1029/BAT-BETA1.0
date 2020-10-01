"""
bat's core URL Configuration.
"""

from django.urls import include, path

from . import views

app_name = "core"

urlpatterns = [
    path("dashboard/", views.DashboardPage.as_view(), name="dashboard"),
    path(
        "supply-chain/dashboard/",
        views.SupplyChainDashboardPage.as_view(),
        name="supplychain_dashboard",
    ),
    path(
        "amazon/dashboard/",
        views.AmazonDashboardPage.as_view(),
        name="amazondashboard",
    ),
    path("logout/", views.LogoutPage.as_view(), name="logoutpage"),
    path("", views.HomePage.as_view(), name="home"),
]
