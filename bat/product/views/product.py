from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from bat.company.utils import get_member
from bat.product import serializers
from bat.product.models import Product
from bat.setting.utils import get_status


class ProductVariationViewSet(viewsets.ModelViewSet):
    """Operations on ProductVariation."""

    serializer_class = serializers.ProductSerializer
    queryset = Product.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["is_active"]
    search_fields = ["title"]

    archive_message = _("Product variation  is archived")
    restore_message = _("Product variation is restored")

    def filter_queryset(self, queryset):
        return queryset.filter(
            productparent__company__pk=self.kwargs.get("company_pk", None),
            productparent__is_component=False,
        )

    def perform_create(self, serializer):
        # TODO
        serializer.save()

    def perform_update(self, serializer):
        # TODO
        serializer.save()
