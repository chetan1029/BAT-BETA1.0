
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend


from bat.setting import serializers
from bat.setting.models import (
    Category
)
from bat.company.utils import get_member


class CategoryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Operations on Category."""

    serializer_class = serializers.CategorySerializer
    queryset = Category.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]

    filterset_fields = ["is_active"]

    def filter_queryset(self, queryset):
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        queryset = queryset.filter(user__id=self.request.user.id).order_by(
            "-create_date"
        )
        return super().filter_queryset(queryset)
