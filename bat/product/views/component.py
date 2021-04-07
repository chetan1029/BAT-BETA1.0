from drf_yasg2.openapi import Response as SwaggerResponse
from bat.company.utils import get_member
from bat.product.import_file import ProductCSVErrorBuilder, ProductExcelErrorBuilder, ProductCSVParser, ProductExcelParser
from bat.company.models import Company, HsCode
from bat.setting.utils import get_status
from bat.product.models import ComponentMe, Product, Image
from bat.product.filters import ProductFilter
from bat.product.constants import (
    PRODUCT_STATUS,
    PRODUCT_PARENT_STATUS,
    PRODUCT_STATUS_ACTIVE,
    PRODUCT_STATUS_DISCONTINUED,
    PRODUCT_STATUS
)
from bat.product import serializers
from bat.mixins.mixins import ArchiveMixin, ExportMixin, RestoreMixin
from drf_yasg2.utils import swagger_auto_schema
from rolepermissions.checkers import has_permission
from taggit.models import Tag
from measurement.measures import Weight
import openpyxl
from taggit.models import Tag, TaggedItem
import json
from decimal import Decimal
import tempfile
from django.utils.decorators import method_decorator
from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.contenttypes.models import ContentType


from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@method_decorator(
    name="bulk_action",
    decorator=swagger_auto_schema(
        operation_description="Performs the given action on provided set of component/product ids. Available actions are: active, archive, draft and delete.",
        request_body=serializers.BulkActionSerializer(),
        responses={status.HTTP_200_OK: SwaggerResponse({"details": "string"})}
    ),
)
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
        "tags",
        "status__name",
    ]
    field_header_map = {"status__name": "status"}

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user_id"] = self.request.user.id
        return context

    @action(detail=False, methods=["post"])
    def bulk_action(self, request, *args, **kwargs):
        """Set the update_status_bulk action."""
        serializer = serializers.BulkActionSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            ids = serializer.validated_data.get("ids")
            bulk_action = serializer.validated_data.get("action").lower()
            member = get_member(
                company_id=self.kwargs.get("company_pk", None),
                user_id=self.request.user.id,
            )
            if bulk_action == "delete":
                if not has_permission(member, "delete_product"):
                    return Response({"detail": _("You do not have permission to perform delete action.")}, status=status.HTTP_403_FORBIDDEN)
                try:
                    ids_cant_delete = Product.objects.bulk_delete(ids)
                    content = {"detail": _("All selected components/products are deleted.")}
                    if ids_cant_delete:
                        content["detail"] = _("Can't delete few components/products from selected.")
                        content["not_deleted_products"] = ids_cant_delete
                    return Response(
                        content, status=status.HTTP_200_OK
                    )
                except IntegrityError:
                    return Response(
                        {"detail": _("Can't delete products")},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    )
            else:
                if not has_permission(member, "change_product"):
                    return Response({"detail": _("You do not have permission to perform this action.")}, status=status.HTTP_403_FORBIDDEN)
                try:
                    Product.objects.bulk_status_update(
                        ids, serializer.validated_data.get("action").lower())
                    return Response(
                        {"detail": _("The status has been updated for selected components/products.")}, status=status.HTTP_200_OK
                    )
                except IntegrityError:
                    return Response(
                        {"detail": _("Can't update status")},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
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

    @action(detail=False, methods=["post"], url_path="import")
    def import_bulk(self, request, *args, **kwargs):
        """Set the update_status_bulk action."""
        # get company
        company_id = kwargs.get("company_pk", None)
        company = get_object_or_404(Company, pk=company_id)

        #  get and validate input
        serializer = serializers.ImportProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # get uploaded file type
        file_format = serializer.validated_data.get("file_format")
        # get uploaded file
        import_file = serializer.validated_data.get("import_file")

        if file_format == "excel":
            parser_classes = ProductExcelParser
            error_builder = ProductExcelErrorBuilder
        elif file_format == "csv":
            parser_classes = ProductCSVParser
            error_builder = ProductCSVErrorBuilder
        else:
            return HttpResponse({"message": "File type is invalid."}, status=status.HTTP_400_BAD_REQUEST)

        data, columns = parser_classes.parse(import_file)
        is_successful, invalid_records = Product.objects.import_bulk(
            data=data, columns=columns, company=company)

        if is_successful:
            if invalid_records:
                error_file = error_builder.write(
                    invalid_records, import_file.name)
                if error_file:
                    ext = import_file.name.split(".")[-1]
                    response_args = {'content_type': 'application/'+ext}
                    response = HttpResponse(error_file, **response_args)
                    response['Content-Disposition'] = 'attachment; filename=' + \
                        import_file.name
                    response['Cache-Control'] = 'no-cache'
                    return response
                else:
                    return HttpResponse(_("Data import performed successfully but can't generate error file."), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return HttpResponse(_("Data import performed successfully."), status=status.HTTP_200_OK)
        else:
            return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ComponentMeViewSet(ArchiveMixin, RestoreMixin, viewsets.ModelViewSet):
    """Operations on Component ME."""

    serializer_class = serializers.ComponentMeSerializer
    queryset = ComponentMe.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Component ME is archived")
    restore_message = _("Component ME is restored")
