from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter

from django.utils.translation import ugettext_lazy as _

from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions

from bat.product import serializers
from bat.product.models import ProductParent


class ProductParentViewSet(viewsets.ModelViewSet):
    """Operations on ProductParent."""

    serializer_class = serializers.ProductParentSerializer
    queryset = ProductParent.objects.all()
    # permission_classes = (IsAuthenticated, DRYPermissions,)
    permission_classes = (IsAuthenticated,)
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
    ]
    filterset_fields = ["is_active"]
    search_fields = ["title"]

    archive_message = _("Product parent is archived")
    restore_message = _("Product parent is restored")

    def perform_update(self, serializer):
        """ update member with given roles and permissions """
        # instance = self.get_object()
        tags = serializer.validated_data.get("tags")
        serializer.validated_data.pop("tags")
        obj = serializer.save()
        obj.tags.set(tags)
