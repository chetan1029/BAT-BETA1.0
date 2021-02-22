import json
from decimal import Decimal
import tempfile


from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.http import HttpResponse


from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from taggit.models import Tag, TaggedItem
import openpyxl
from measurement.measures import Weight


from bat.mixins.mixins import ArchiveMixin, ExportMixin, RestoreMixin
from bat.product import serializers
from bat.product.constants import (
    PRODUCT_PARENT_STATUS,
    PRODUCT_STATUS_ACTIVE,
    PRODUCT_STATUS_DISCONTINUED,
    PRODUCT_STATUS
)
from bat.product.filters import ProductFilter
from bat.product.models import ComponentMe, Product, Image
from bat.setting.utils import get_status
from bat.company.models import Company, HsCode


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

    @action(detail=False, methods=["post"])
    def import_bulk(self, request, *args, **kwargs):
        """Set the update_status_bulk action."""
        # get company
        company_id = kwargs.get("company_pk", None)
        company = get_object_or_404(Company, pk=company_id)

        #  get and validate input
        serializer = serializers.ImportProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # get model_number map with map
        products_map_tuple = Product.objects.filter(
            company_id=company_id).values_list("model_number", "id")
        products_map = {k: v for k, v in products_map_tuple}

        # get exsisting hscoad map
        hscode_map_tuple = HsCode.objects.filter(company_id=company_id).values_list("hscode", "id")
        hscode_map = {k: v for k, v in hscode_map_tuple}

        # get uploaded file
        import_file = serializer.validated_data.get("import_file")

        # read file
        ws = openpyxl.load_workbook(import_file)
        sheet = ws.active

        # get column's list
        header = [cell.value for cell in sheet[1]]
        header = header[1:]

        # add column for errors
        lat_col_index = len(header)+2
        header_cell = sheet.cell(row=1, column=lat_col_index)
        header_cell.value = "errors"
        header.append(header_cell.value)

        # create model objects
        products_update = []
        hscode_objs = []
        for row in sheet.iter_rows(min_row=2, min_col=2):
            values = {}
            # process each value
            for key, cell in zip(header, row):
                if key == "status":
                    values[key] = get_status(PRODUCT_PARENT_STATUS, PRODUCT_STATUS.get(
                        cell.value.lower())) if cell.value else None
                elif key == "weight":
                    value = cell.value.replace(" g", "") if cell.value else None
                    value = Weight({"g": Decimal(value)})
                    values[key] = value
                elif key == "tags":
                    values[key] = cell.value.split(",") if cell.value else None
                    # print(Tag.objects.all(), "........", TaggedItem.objects.all())
                elif key == "hscode":
                    try:
                        _hscode_id = hscode_map.get(cell.value)
                        values[key] = cell.value if cell.value else ""
                    except KeyError as e:
                        hscode_objs.append(HsCode(company=company, hscode=cell.value))
                elif key in ["bullet_points", "description"]:
                    values[key] = cell.value if cell.value else ""
                elif key == "errors":
                    pass
                else:
                    values[key] = cell.value
            try:
                product_id = products_map.get(values.get("model_number", None))
                product = Product(id=product_id, company=company, **values)
                try:
                    # validate object
                    product.full_clean(exclude=["id"])
                    products_update.append(product)
                except ValidationError as e:
                    # add validation error in file
                    error_cell = sheet.cell(row=row[0].row, column=lat_col_index)
                    error_cell.value = json.dumps(e.message_dict)
            except KeyError as e:
                print("have to create object")

        # create temporaryfile
        tmp_dir = tempfile.TemporaryDirectory()
        tmp_xlsx_file_path = tmp_dir.name + "/" + import_file.name

        # save changes in uploaded file
        ws.save(tmp_xlsx_file_path)
        ws.close()

        # open saved file
        ext = import_file.name.split(".")[-1]
        f = open(tmp_xlsx_file_path, "rb")

        response_args = {'content_type': 'application/'+ext}
        response = HttpResponse(f, **response_args)
        response['Content-Disposition'] = 'attachment; filename=' + \
            import_file.name

        response['Cache-Control'] = 'no-cache'
        try:
            # perform bulk operations
            HsCode.objects.bulk_create(hscode_objs)
            Product.objects.bulk_update(products_update, header[:-1])
        except Exception as e:
            response_args["status"] = status.HTTP_500_INTERNAL_SERVER_ERROR

        # send file in response
        return response


class ComponentMeViewSet(ArchiveMixin, RestoreMixin, viewsets.ModelViewSet):
    """Operations on Component ME."""

    serializer_class = serializers.ComponentMeSerializer
    queryset = ComponentMe.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Component ME is archived")
    restore_message = _("Component ME is restored")
