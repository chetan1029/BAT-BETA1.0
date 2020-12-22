from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from bat.company.models import Member
from bat.company.utils import get_member
from bat.setting import serializers
from bat.setting.models import Category, DeliveryTermName, DeliveryTerms, Category, Status

vendors_only_param = openapi.Parameter(
    "vendors_only",
    openapi.IN_QUERY,
    description="Returns only vendor categories",
    type=openapi.TYPE_BOOLEAN,
    required=False,
)

sales_channel_only_param = openapi.Parameter(
    'sales_channel_only', openapi.IN_QUERY, description="Returns only sales channel categories", type=openapi.TYPE_BOOLEAN, required=False)


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Returns all the categories",
        responses={200: serializers.CategorySerializer(many=True)},
        manual_parameters=[vendors_only_param, sales_channel_only_param],
    ),
)
class CategoryViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Operations on Category."""

    serializer_class = serializers.CategorySerializer
    queryset = Category.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]

    filterset_fields = ["is_active"]

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        only_vendor_categories = self.request.GET.get("vendors_only", False)
        if only_vendor_categories:
            queryset = queryset.filter(
                is_vendor_category=True if only_vendor_categories == 'true' else False)

        sales_channel_only = self.request.GET.get('sales_channel_only', False)
        if sales_channel_only:
            queryset = queryset.filter(
                is_sales_channel_category=True if sales_channel_only == 'true' else False)
        return queryset


<< << << < HEAD


class StatusViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    gives list of available status in the system
    """
    serializer_class = serializers.StatusSerializer
    queryset = Status.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]

    filterset_fields = ["is_active", "name"]


== == == =
# delivery terms Name


class DeliveryTermNameViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Operations on delivery term name."""

    serializer_class = serializers.DeliveryTermNameSerializer
    queryset = DeliveryTermName.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]


>>>>>> > develop
