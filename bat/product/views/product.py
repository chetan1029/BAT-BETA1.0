from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from bat.mixins.mixins import ArchiveMixin, ExportMixin, RestoreMixin
from bat.product import serializers
from bat.product.models import Product, ProductComponent, ProductPackingBox, ProductRrp


@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        reqeust={serializers.UpdateProductSerializer()}
    ),
)
class ProductVariationViewSet(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
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
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(company__pk=company_id)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        context = self.get_serializer_context()
        serializer = serializers.UpdateProductSerializer(
            instance=instance,
            data=request.data,
            context=context,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)


class ProductMetadatMxin(viewsets.ModelViewSet):
    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        product_id = self.kwargs.get("product_pk", None)
        company_id = self.kwargs.get("company_pk", None)
        return queryset.filter(
            product__id=product_id, product__company__id=company_id
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

class ComponentProductViewSet(ArchiveMixin, RestoreMixin, ProductMetadatMxin):
    """Operations on ComponentProduct."""

    serializer_class = serializers.ProductComponentSerializer
    queryset = ProductComponent.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Product component  is archived")
    restore_message = _("Product component is restored")

    def filter_queryset(self, queryset):
        product_pk = self.kwargs.get("product_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(component__pk=product_pk)


country_field = openapi.Parameter(
    "country",
    openapi.IN_QUERY,
    description="Filters by country",
    type=openapi.TYPE_STRING,
    required=False,
)

currency_field = openapi.Parameter(
    "rrp_currency",
    openapi.IN_QUERY,
    description="Filters by currency",
    type=openapi.TYPE_STRING,
    required=False,
)


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Returns all the Product rrps",
        responses={200: serializers.ProductRrpSerializer(many=True)},
        manual_parameters=[country_field, currency_field],
    ),
)
class ProductRrpViewSet(ExportMixin, ProductMetadatMxin):
    """Operations on ProductRrp."""

    serializer_class = serializers.ProductRrpSerializer
    queryset = ProductRrp.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]
    export_fields = [
        "id",
        "product__title",
        "product__sku",
        "product__series",
        "rrp",
        "country",
        "is_active",
    ]
    field_header_map = {
        "product__title": "title",
        "product__sku": "sku",
        "product__series": "series",
    }

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        if self.request.GET.get("rrp_currency", None):
            queryset = queryset.filter(
                rrp_currency=self.request.GET.get("rrp_currency")
            )
        if self.request.GET.get("country", None):
            queryset = queryset.filter(country=self.request.GET.get("country"))
        return queryset


class ProductPackingBoxViewSet(ArchiveMixin, RestoreMixin, ProductMetadatMxin):
    """Operations on ProductPackingBox."""

    serializer_class = serializers.ProductPackingBoxSerializer
    queryset = ProductPackingBox.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Product packing box  is archived")
    restore_message = _("Product packing box is restored")
