from django.utils.decorators import method_decorator
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from drf_yasg2.utils import swagger_auto_schema
from drf_yasg2 import openapi

from django_filters.rest_framework import DjangoFilterBackend


from bat.setting import serializers
from bat.setting.models import (
    Category
)
from bat.company.models import Member
from bat.company.utils import get_member


vendors_only_param = openapi.Parameter(
    'vendors_only', openapi.IN_QUERY, description="Returns only vendor categories", type=openapi.TYPE_BOOLEAN, required=False)

@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_description="Returns all the categories",
    responses={200: serializers.CategorySerializer(many=True)},
    manual_parameters=[vendors_only_param]
))
class CategoryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Operations on Category."""

    serializer_class = serializers.CategorySerializer
    queryset = Category.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]

    filterset_fields = ["is_active"]

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)

        # TODO - permission check?
        member = get_member(
            company_id=company_id,
            user_id=self.request.user.id,
        )

        all_users = Member.objects.filter(company=company_id).values_list('user', flat=True)

        queryset = queryset.filter(user__id__in=all_users).order_by(
            "-create_date"
        )

        only_vendor_categories = self.request.GET.get('vendors_only', False)
        if only_vendor_categories:
            queryset = queryset.filter(is_vendor_category=True if only_vendor_categories == 'true' else False)

        return super().filter_queryset(queryset)
