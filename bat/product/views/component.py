from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db import IntegrityError, transaction

from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions

from bat.company.utils import get_member
from bat.mixins.mixins import ArchiveMixin, RestoreMixin
from bat.product import serializers
from bat.product.models import ProductParent, Product
from bat.setting.utils import get_status


class ProductParentViewSet(ArchiveMixin, RestoreMixin, viewsets.ModelViewSet):
    """Operations on ProductParent."""

    serializer_class = serializers.ProductParentSerializer
    queryset = ProductParent.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions,)
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
        status = get_status("Product", "Active")
        # TODO hscode
        obj = serializer.save(company=member.company, status=status)
        obj.tags.set(*tags)

    def perform_update(self, serializer):
        """ update ProductParent with given tags """
        tags = serializer.validated_data.get("tags")
        serializer.validated_data.pop("tags")
        status = get_status("Product", "Active")
        obj = serializer.save(status=status)
        obj.tags.set(*tags)


class ProductViewSet(ArchiveMixin, RestoreMixin, mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Operations on ProductParent."""

    serializer_class = serializers.ProductSerializer
    queryset = ProductParent.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["is_active"]
    search_fields = ["title"]

    archive_message = _("Product parent is archived")
    restore_message = _("Product parent is restored")

    def perform_create(self, serializer):
        print("\n \n \n \n serializer.validated_data :",
              serializer.validated_data)
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        tags = serializer.validated_data.get("tags")
        products = serializer.validated_data.get("products", None)
        print("\n \n \n products....:", products)
        serializer.validated_data.pop("tags")
        serializer.validated_data.pop("products")
        # try:
        with transaction.atomic():
            status = get_status("Product", "Active")
            obj = serializer.save(company=member.company, status=status)
            # set tags
            obj.tags.set(*tags)
            # save variations
            for product in products:
                Product.objects.create(productparent=obj, **product)
        # except IntegrityError:
        #     raise IntegrityError
