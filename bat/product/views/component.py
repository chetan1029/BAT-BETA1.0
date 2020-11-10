from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from bat.company.utils import get_member
from bat.mixins.mixins import ArchiveMixin, RestoreMixin
from bat.product import serializers
from bat.product.models import ProductParent
from bat.setting.utils import get_status


class ProductParentViewSet(ArchiveMixin, RestoreMixin, viewsets.ModelViewSet):
    """Operations on ProductParent."""

    serializer_class = serializers.ProductParentSerializer
    queryset = ProductParent.objects.all()
    # permission_classes = (IsAuthenticated, DRYPermissions,)
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["is_active"]
    search_fields = ["title"]

    archive_message = _("Product parent is archived")
    restore_message = _("Product parent is restored")

    def perform_create(self, serializer):
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        tags = serializer.validated_data.get("tags")
        serializer.validated_data.pop("tags")
        if serializer.validated_data.get("is_component", False):
            # TODO  set status as get_status("Product", "Inactive")
            status = get_status("Product", "Inactive")
        else:
            # TODO what is status if not is_component?
            status = get_status(settings.STATUS_PRODUCT)

        obj = serializer.save(company=member.company, status=status)
        obj.tags.set(*tags)

    def perform_update(self, serializer):
        """ update ProductParent with given tags """
        tags = serializer.validated_data.get("tags")
        serializer.validated_data.pop("tags")
        obj = serializer.save()
        obj.tags.set(*tags)
