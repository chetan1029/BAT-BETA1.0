from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions
from invitations.utils import get_invitation_model
from notifications.signals import notify
from rest_framework import mixins, status, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rolepermissions.checkers import has_permission
from rolepermissions.permissions import revoke_permission
from rolepermissions.roles import RolesManager, assign_role, clear_roles

from bat.company import serializers
from bat.company.models import (
    CompanyContract,
    CompanyCredential,
    CompanyOrder,
    CompanyOrderProduct,
    CompanyProduct,
    ComponentGoldenSample,
    ComponentMe,
    ComponentPrice,
)
from bat.company.utils import get_member
from bat.mixins.mixins import ArchiveMixin, RestoreMixin
from bat.product.constants import PRODUCT_STATUS_ACTIVE, PRODUCT_STATUS_DRAFT
from bat.setting.utils import get_status


# Company base view set.
class CompanySettingBaseViewSet(
    ArchiveMixin, RestoreMixin, viewsets.ModelViewSet
):
    """Company setting base view set."""

    class Meta:
        abstract = True

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user"] = self.request.user
        return context

    def filter_queryset(self, queryset):
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        queryset = queryset.filter(
            companytype__company=member.company
        ).order_by("-create_date")
        return super().filter_queryset(queryset)


class CompanyContractViewSet(CompanySettingBaseViewSet):
    """Operations on CompanyContract."""

    serializer_class = serializers.CompanyContractSerializer
    queryset = CompanyContract.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Company contract is archived")
    restore_message = _("Company contract is restored")

    def perform_create(self, serializer):
        company_contract = serializer.save()
        company_contract.save_pdf_file()


class CompanyCredentialViewSet(CompanySettingBaseViewSet):
    """Operations on Company Credential."""

    serializer_class = serializers.CompanyCredentialSerializer
    queryset = CompanyCredential.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Company credential is archived")
    restore_message = _("Company credential is restored")


class ComponentMeViewSet(CompanySettingBaseViewSet):
    """Operations on Component ME."""

    serializer_class = serializers.ComponentMeSerializer
    queryset = ComponentMe.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Component ME is archived")
    restore_message = _("Component ME is restored")


class ComponentGoldenSampleViewSet(viewsets.ModelViewSet):
    """Operations on Component Golden Sample."""

    serializer_class = serializers.ComponentGoldenSampleSerializer
    queryset = ComponentGoldenSample.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Component Golden Sample is archived")
    restore_message = _("Component Golden Sample is restored")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user"] = self.request.user
        return context

    def filter_queryset(self, queryset):
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        queryset = queryset.filter(
            componentme__companytype__company=member.company
        ).order_by("-create_date")
        return super().filter_queryset(queryset)


class ComponentPriceViewSet(viewsets.ModelViewSet):
    """Operations on Component Price."""

    serializer_class = serializers.ComponentPriceSerializer
    queryset = ComponentPrice.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Component Price is archived")
    restore_message = _("Component Price is restored")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user"] = self.request.user
        return context

    def filter_queryset(self, queryset):
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        queryset = queryset.filter(
            componentgoldensample__componentme__companytype__company=member.company
        ).order_by("-create_date")
        return super().filter_queryset(queryset)


class CompanyProductViewSet(viewsets.ModelViewSet):
    """Operations on Company Product."""

    serializer_class = serializers.CompanyProductSerializer
    queryset = CompanyProduct.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Company Product is archived")
    restore_message = _("Company Product is restored")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user"] = self.request.user
        return context

    def filter_queryset(self, queryset):
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        queryset = queryset.filter(
            companytype__company=member.company
        ).order_by("-create_date")
        return super().filter_queryset(queryset)


class CompanyOrderViewSet(
    ArchiveMixin,
    RestoreMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Operations on Company Order."""

    serializer_class = serializers.CompanyOrderSerializer
    queryset = CompanyOrder.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["status"]
    search_fields = ["batch_id"]

    archive_message = _("Order is archived")
    restore_message = _("Order is restored")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user"] = self.request.user
        return context

    def perform_create(self, serializer):
        """
        save company order with the products and related objects.
        """
        try:
            with transaction.atomic():
                orderproducts = serializer.validated_data.get(
                    "orderproducts", None
                )
                serializer.validated_data.pop("orderproducts")
                # order_status = get_status("Basic", PRODUCT_STATUS_DRAFT)
                # # Draft, Active, Archived
                # companyorder = serializer.save(status=order_status)
                # # save order products
                # total_quantity = 0
                # total_amount = 0
                # for orderproduct in orderproducts or []:
                #     quantity = orderproduct.validated_data.get(
                #         "quantity", None
                #     )
                #     remaining_quantity = quantity
                #     componentprice_id = orderproduct.validated_data.get(
                #         "componentprice", None
                #     )
                #     componentprice = ComponentPrice.objects.get(
                #         pk=componentprice_id
                #     )
                #     price = componentprice.price
                #     amount = Decimal(price) * Decimal(quantity)
                #     total_quantity = total_quantity + quantity
                #     total_amount = Decimal(amount) + Decimal(total_amount)
                #     CompanyOrderProduct.objects.create(
                #         companyorder=companyorder,
                #         price=price,
                #         amount=amount,
                #         remaining_quantity=remaining_quantity,
                #         **orderproduct
                #     )
                # companyorder.sub_amount = total_amount
                # companyorder.total_amount = total_amount
                # companyorder.quantity = total_quantity
                # companyorder.save()
        except IntegrityError:
            return Response(
                {"detail": _("Can't have to same product in the same order")},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
