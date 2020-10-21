"""URL Patterns for Product app."""

from django.urls import path

from . import views

app_name = "product"

urlpatterns = [
    # Product
    path("", views.ProductDashboardView.as_view(), name="product_dashboard"),
    path("add", views.ProductCreateView.as_view(), name="product_create"),
    path(
        "product", views.ProductActiveListView.as_view(), name="product_list"
    ),
    path(
        "product/archived",
        views.ProductArchivedListView.as_view(),
        name="productarchived_list",
    ),
    path(
        "product/<int:pk>/archived/",
        views.ProductArchivedView.as_view(),
        name="product_archived",
    ),
    path(
        "product/<int:pk>/delete/",
        views.ProductDeleteView.as_view(),
        name="product_delete",
    ),
    path(
        "product/<int:pk>/restore/",
        views.ProductRestoreView.as_view(),
        name="product_restore",
    ),
    # Component
    path(
        "component/add",
        views.ComponentCreateView.as_view(),
        name="component_create",
    ),
    path(
        "component",
        views.ComponentActiveListView.as_view(),
        name="component_list",
    ),
    path(
        "component/archived",
        views.ComponentArchivedListView.as_view(),
        name="componentarchived_list",
    ),
    path(
        "component/<int:pk>/archived/",
        views.ComponentArchivedView.as_view(),
        name="component_archived",
    ),
    path(
        "component/<int:pk>/delete/",
        views.ComponentDeleteView.as_view(),
        name="component_delete",
    ),
    path(
        "component/<int:pk>/restore/",
        views.ComponentRestoreView.as_view(),
        name="component_restore",
    ),
]
