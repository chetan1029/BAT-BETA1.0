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
from bat.company.models import HsCode
from bat.mixins.mixins import ArchiveMixin, RestoreMixin
from bat.product import serializers
from bat.product.models import ProductParent, Product, ProductOption, ProductVariationOption
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
        '''
        save product parent with all children products and related objects.
        '''

        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        # try:
        with transaction.atomic():
            hscode = serializer.validated_data.get("hscode", None)
            if hscode:
                hscode, _c = HsCode.objects.get_or_create(
                    hscode=hscode, company=member.company
                )
            tags = serializer.validated_data.get("tags", None)
            serializer.validated_data.pop("tags", None)
            products = serializer.validated_data.get("products", None)
            serializer.validated_data.pop("products")
            status = get_status("Product", "Active")
            product_parent = serializer.save(
                company=member.company, status=status)
            if tags:
                # set tags
                product_parent.tags.set(*tags)
            # save variations
            for product in products or []:
                product_variation_options = product.get(
                    "product_variation_options", None)
                product.pop("product_variation_options", None)
                new_product = Product.objects.create(
                    productparent=product_parent, **product)
                # save options
                for variation_option in product_variation_options or []:
                    name = variation_option.get(
                        "productoption", None).get("name", None)
                    value = variation_option.get(
                        "productoption", None).get("value", None)
                    if name and value:
                        productoption, _c = ProductOption.objects.get_or_create(
                            name=name,
                            value=value,
                            productparent=product_parent,
                        )
                        ProductVariationOption.objects.create(
                            product=new_product,
                            productoption=productoption,
                        )
        # except IntegrityError:
        #     raise IntegrityError
