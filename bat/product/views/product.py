from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter

from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions

from bat.product import serializers
from bat.product.models import Product
from bat.company.utils import get_member
from bat.setting.utils import get_status


class ProductViewSet(viewsets.ModelViewSet):
    """Operations on ProductParent."""

    serializer_class = serializers.ProductSerializer
    queryset = Product.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions,)
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
    ]
    filterset_fields = ["is_active"]
    search_fields = ["title"]

    archive_message = _("Product is archived")
    restore_message = _("Product is restored")

    def filter_queryset(self, queryset):
        return queryset.filter(
            productparent__company__pk=self.kwargs.get("company_pk", None),
            productparent__is_component=False,
        )

    def perform_create(self, serializer):
        serializer.save()
        # member = get_member(company_id=self.kwargs.get(
        #     "company_pk", None), user_id=self.request.user.id)
        # tags = serializer.validated_data.get("tags")
        # serializer.validated_data.pop("tags")
        # if serializer.validated_data.get("is_component", False):
        #     # TODO  set status as get_status("Product", "Inactive")
        #     status = get_status("Product", "Inactive")
        # else:
        #     # TODO what is status if not is_component?
        #     status = get_status(settings.STATUS_PRODUCT)

        # obj = serializer.save(company=member.company,
        #                       status=status)
        # obj.tags.set(*tags)
        pass

    def perform_update(self, serializer):
        serializer.save()
        """ update ProductParent with given tags """
        # tags = serializer.validated_data.get("tags")
        # serializer.validated_data.pop("tags")
        # obj = serializer.save()
        # obj.tags.set(*tags)
        pass
