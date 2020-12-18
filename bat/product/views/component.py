from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db import IntegrityError, transaction

from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions
from taggit.models import Tag

from bat.mixins.mixins import ArchiveMixin, RestoreMixin, ExportMixin
from bat.product import serializers
from bat.product.models import ProductParent
from bat.setting.utils import get_status
from bat.product.constants import PRODUCT_STATUS_ACTIVE
from bat.product.filters import ProductFilter


class ProductViewSet(ArchiveMixin,
                     RestoreMixin,
                     ExportMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     viewsets.GenericViewSet):
    """Operations on ProductParent."""

    serializer_class = serializers.ProductSerializer
    queryset = ProductParent.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend, SearchFilter,
                       OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["title", "type", "series",
                     "hscode", "sku", "bullet_points", "description"]
    ordering_fields = ['create_date', 'title']

    archive_message = _("Product parent is archived")
    restore_message = _("Product parent is restored")

    export_fields = ["id", "company", "is_component", "title", "type", "sku",
                     "bullet_points", "description", "tags", "is_active", "status__name", "products__title",
                     "products__sku", "extra_data", "series", "hscode"]
    field_header_map = {"status__name": "status",
                        "products__title": "veriation title", "products__sku": "veriation sku"}

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user_id"] = self.request.user.id
        return context

    @action(detail=True, methods=["post"])
    def active(self, request, *args, **kwargs):
        """Set the active action."""
        instance = self.get_object()
        if instance.get_status_name == PRODUCT_STATUS_ACTIVE:
            return Response({"detail": _("Already active")}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                instance.status = get_status("Basic", PRODUCT_STATUS_ACTIVE)
                instance.save()
            return Response({"detail": self.archive_message}, status=status.HTTP_200_OK)
        except IntegrityError:
            return Response({"detail": _("Can't activate")}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        company_id = self.kwargs.get("company_pk", None)
        return queryset.filter(company__pk=company_id)

    @action(detail=False, methods=["GET"], url_path="tags-types")
    def get_tags_and_types(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        types = queryset.exclude(type__exact="").exclude(type__isnull=True).distinct(
            "type").values_list("type", flat=True)
        tags = queryset.exclude(tags__isnull=True).distinct("tags__name").values_list(
            "tags__name", flat=True)
        data = {}
        data["tag_data"] = tags
        data["type_data"] = types
        return Response(data, status=status.HTTP_200_OK)
