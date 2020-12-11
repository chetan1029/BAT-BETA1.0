from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db import IntegrityError, transaction

from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions

from bat.company.utils import get_member
from bat.mixins.mixins import ArchiveMixin, RestoreMixin, ExportMixin
from bat.company.models import HsCode
from bat.product import serializers
from bat.product.models import ProductParent, Product, ProductOption, ProductVariationOption
from bat.setting.utils import get_status
from bat.product.constants import PRODUCT_STATUS_ACTIVE, PRODUCT_STATUS_DRAFT


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
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["is_active", "is_component"]
    search_fields = ["title"]

    archive_message = _("Product parent is archived")
    restore_message = _("Product parent is restored")

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
        print("instance.get_status_name : ", instance.get_status_name)
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
        company_id = self.kwargs.get("company_pk", None)
        return queryset.filter(company__pk=company_id)
