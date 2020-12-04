from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import viewsets, mixins
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from bat.product import serializers
from bat.product.models import (
    Product, ProductComponent, ProductRrp, ProductPackingBox)
from bat.mixins.mixins import ArchiveMixin, RestoreMixin, ExportMixin


class ProductVariationViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Operations on ProductVariation."""

    serializer_class = serializers.ProductVariationSerializer
    queryset = Product.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["is_active"]
    search_fields = ["title"]

    archive_message = _("Product variation  is archived")
    restore_message = _("Product variation is restored")

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        # product_id = self.kwargs.get("product_pk", None)
        return queryset.filter(
            productparent__company__pk=company_id,
            # productparent__id=product_id
        )


class ProductMetadatMxin(viewsets.ModelViewSet):

    def filter_queryset(self, queryset):
        product_id = self.kwargs.get("product_pk", None)
        company_id = self.kwargs.get("company_pk", None)
        return queryset.filter(
            product__productparent__id=product_id,
            product__productparent__company__id=company_id
        )


class ProductComponentViewSet(ArchiveMixin, RestoreMixin, ProductMetadatMxin):
    """Operations on ProductComponent."""

    serializer_class = serializers.ProductComponentSerializer
    queryset = ProductComponent.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Product component  is archived")
    restore_message = _("Product component is restored")


class ProductRrpViewSet(ExportMixin, ProductMetadatMxin):
    """Operations on ProductRrp."""

    serializer_class = serializers.ProductRrpSerializer
    queryset = ProductRrp.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]
    csv_export_fields = ["id", "product__id", "product__model_number", "rrp",
                         "country", "is_active", "create_date", "update_date"]
    csv_field_header_map = {"product__id": "product id",
                            "product__model_number": "model number for product"}



class ProductPackingBoxViewSet(ArchiveMixin, RestoreMixin, ProductMetadatMxin):
    """Operations on ProductPackingBox."""

    serializer_class = serializers.ProductPackingBoxSerializer
    queryset = ProductPackingBox.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Product packing box  is archived")
    restore_message = _("Product packing box is restored")
