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
    path("component/add", views.create_component, name="component_create"),
    path(
        "component",
        views.ComponentParentActiveListView.as_view(),
        name="componentparent_list",
    ),
    path(
        "component/archived",
        views.ComponentParentArchivedListView.as_view(),
        name="componentparentarchived_list",
    ),
    path(
        "component/<int:pk>/delete-archived/",
        views.ComponentParentArchivedView.as_view(),
        name="componentparent_archived",
    ),
    path(
        "component/<int:pk>/delete/",
        views.ComponentParentDeleteView.as_view(),
        name="componentparent_delete",
    ),
    path(
        "component/<int:pk>/restore/",
        views.ComponentParentRestoreView.as_view(),
        name="componentparent_restore",
    ),
    path(
        "ajax/generate-variation",
        views.generate_variation,
        name="generate_variation",
    ),
    path(
        "component/<int:pk>",
        views.ComponentActiveListView.as_view(),
        name="component_list",
    ),
    path(
        "component/archived/<int:pk>",
        views.ComponentArchivedListView.as_view(),
        name="componentarchived_list",
    ),
    path(
        "component/parent/<int:pk>/delete-archived/",
        views.ComponentArchivedView.as_view(),
        name="component_archived",
    ),
    path(
        "component/parent/<int:pk>/delete/",
        views.ComponentDeleteView.as_view(),
        name="component_delete",
    ),
    path(
        "component/parent/<int:pk>/restore/",
        views.ComponentRestoreView.as_view(),
        name="component_restore",
    ),
]
