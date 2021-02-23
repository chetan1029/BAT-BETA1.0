from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from taggit.models import Tag

from bat.mixins.mixins import ArchiveMixin, ExportMixin, RestoreMixin
from bat.product import serializers
from bat.product.constants import (
    PRODUCT_STATUS,
    PRODUCT_PARENT_STATUS,
    PRODUCT_STATUS_ACTIVE,
    PRODUCT_STATUS_DISCONTINUED,
)
from bat.product.filters import ProductFilter
from bat.product.models import ComponentMe, Product, Image
from bat.setting.utils import get_status


class ProductViewSet(
    ArchiveMixin,
    RestoreMixin,
    ExportMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Operations on Products."""

    serializer_class = serializers.ProductSerializer
    queryset = Product.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = [
        "title",
        "type",
        "series",
        "hscode",
        "sku",
        "bullet_points",
        "description",
    ]
    ordering_fields = ["create_date", "title"]

    archive_message = _("Product is archived")
    restore_message = _("Product is restored")
    active_message = _("Product is active")
    discontinued_message = _("Product is discontinued")

    export_fields = [
        "id",
        "title",
        "type",
        "model_number",
        "manufacturer_part_number",
        "hscode",
        "length",
        "width",
        "depth",
        "length_unit",
        "weight",
        "bullet_points",
        "description",
        "tags__name",
        "status__name",
    ]
    field_header_map = {"status__name": "status", "tags__name": "tags"}

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user_id"] = self.request.user.id
        return context

    @action(detail=False, methods=["post"])
    def update_status_bulk(self, request, *args, **kwargs):
        """Set the update_status_bulk action."""
        serializer = serializers.UpdateStatusSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            ids = serializer.data.get("ids")
            try:
                with transaction.atomic():
                    status_obj = get_status(PRODUCT_PARENT_STATUS, PRODUCT_STATUS.get(
                        serializer.data.get("status").lower()))
                    Product.objects.filter(id__in=ids).update(status=status_obj)
                    return Response(
                        {"detail": "Products status updated."}, status=status.HTTP_200_OK
                    )
            except IntegrityError:
                return Response(
                    {"detail": _("Can't update status")},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

    @action(detail=False, methods=["delete"])
    def delete_bulk(self, request, *args, **kwargs):
        """Set the delete_bulk action."""
        ids = request.GET.get("ids", None)
        if ids:
            ids = ids.split(",")
            ids = list(filter(None, ids))
            if not ids:
                return Response(
                    {"detail": _("Id list should not empty.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                with transaction.atomic():
                    products = Product.objects.filter(id__in=ids)
                    for product in products:
                        if not product.is_deletable():
                            ids.remove(str(product.id))
                    products = Product.objects.filter(id__in=ids).delete()
                return Response(
                    {"detail": "Products deleted."}, status=status.HTTP_200_OK
                )
            except IntegrityError:
                return Response(
                    {"detail": _("Can't delete products")},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
        return Response(
            {"detail": _("Provide id list")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def active(self, request, *args, **kwargs):
        """Set the active action."""
        instance = self.get_object()
        if instance.get_status_name == PRODUCT_STATUS_ACTIVE:
            return Response(
                {"detail": _("Already active")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            with transaction.atomic():
                instance.status = get_status(
                    PRODUCT_PARENT_STATUS, PRODUCT_STATUS_ACTIVE
                )
                instance.save()
            return Response(
                {"detail": self.active_message}, status=status.HTTP_200_OK
            )
        except IntegrityError:
            return Response(
                {"detail": _("Can't activate")},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

    @action(detail=True, methods=["post"])
    def discontinued(self, request, *args, **kwargs):
        """Set the discontinued status."""
        instance = self.get_object()
        if instance.get_status_name == PRODUCT_STATUS_DISCONTINUED:
            return Response(
                {"detail": _("Already discontinued")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            with transaction.atomic():
                instance.status = get_status(
                    PRODUCT_PARENT_STATUS, PRODUCT_STATUS_DISCONTINUED
                )
                instance.save()
                # post_save.send(ProductParent, instance=instance,
                #                created=False, using=None)
            return Response(
                {"detail": self.discontinued_message},
                status=status.HTTP_200_OK,
            )
        except IntegrityError:
            return Response(
                {"detail": _("Can't discontinued")},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        company_id = self.kwargs.get("company_pk", None)
        return queryset.filter(company__pk=company_id)

    @action(detail=False, methods=["GET"], url_path="tags-types")
    def get_tags_and_types(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        types = (
            queryset.exclude(type__exact="")
            .exclude(type__isnull=True)
            .distinct("type")
            .values_list("type", flat=True)
        )
        tags = (
            queryset.exclude(tags__isnull=True)
            .distinct("tags__name")
            .values_list("tags__name", flat=True)
        )
        series = (
            queryset.exclude(series__exact="")
            .exclude(series__isnull=True)
            .distinct("series")
            .values_list("series", flat=True)
        )
        hscode = (
            queryset.exclude(hscode__exact="")
            .exclude(hscode__isnull=True)
            .distinct("hscode")
            .values_list("hscode", flat=True)
        )
        data = {}
        data["tag_data"] = tags
        data["type_data"] = types
        data["series_data"] = series
        data["hscode_data"] = hscode
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["GET"], url_path="types-with-images")
    def get_types(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        types = (
            queryset.exclude(type__exact="")
            .exclude(type__isnull=True)
            .distinct("type")
            .values_list("type", flat=True)
        )
        type_data = []
        for type in types:
            product_data = {}
            queryset_type = queryset.filter(type__exact=type)
            product_images = queryset_type.values_list(
                "images", flat=True
            )[:3]
            product_images = Image.objects.filter(id__in=product_images)

            type_data.append({
                "type": type,
                "total": queryset_type.count(),
                "products": ["http://localhost:8000" + image.image.url for image in product_images]
            })
        # data = {}
        # data["type_data"] = type_data
        return Response(type_data, status=status.HTTP_200_OK)


class ComponentMeViewSet(ArchiveMixin, RestoreMixin, viewsets.ModelViewSet):
    """Operations on Component ME."""

    serializer_class = serializers.ComponentMeSerializer
    queryset = ComponentMe.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Component ME is archived")
    restore_message = _("Component ME is restored")
