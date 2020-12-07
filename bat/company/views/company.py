from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import mixins, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from bat.company import serializers
from bat.company.models import (
    CompanyContract,
    CompanyCredential,
    CompanyOrder,
    CompanyOrderDelivery,
    CompanyProduct,
    ComponentGoldenSample,
    ComponentMe,
    ComponentPrice,
    CompanyOrderCase,
    CompanyOrderInspection,
    CompanyOrderDeliveryTestReport,
    CompanyOrderPaymentPaid,
    CompanyOrderPayment
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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user_id"] = self.request.user.id
        return context


class CompanyOrderDeliveryViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Operations on Company Delivery Order."""

    serializer_class = serializers.CompanyOrderDeliverySerializer
    queryset = CompanyOrderDelivery.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["status"]
    search_fields = ["batch_id"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user_id"] = self.request.user.id
        return context


class CompanyOrderCaseViewSet(
    viewsets.ModelViewSet,
):
    """Operations on Company Order Case."""

    serializer_class = serializers.CompanyOrderCaseSerializers
    queryset = CompanyOrderCase.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user_id"] = self.request.user.id
        return context

    def filter_queryset(self, queryset):
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        queryset = queryset.filter(
            companyorder__companytype__company=member.company
        ).order_by("-create_date")
        return super().filter_queryset(queryset)


class CompanyOrderInspectionViewSet(
    viewsets.ModelViewSet,
):
    """Operations on Company Order Inspection."""

    serializer_class = serializers.CompanyOrderInspectionSerializer
    queryset = CompanyOrderInspection.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user_id"] = self.request.user.id
        return context

    def filter_queryset(self, queryset):
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        queryset = queryset.filter(
            companyorder__companytype__company=member.company
        ).order_by("-create_date")
        return super().filter_queryset(queryset)


class CompanyOrderDeliveryTestReportViewSet(
    viewsets.ModelViewSet,
):
    """Operations on Company Order Delivery TestReport."""

    serializer_class = serializers.CompanyOrderDeliveryTestReportSerializer
    queryset = CompanyOrderDeliveryTestReport.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user_id"] = self.request.user.id
        return context

    def filter_queryset(self, queryset):
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        queryset = queryset.filter(
            companyorderdelivery__companyorder__companytype__company=member.company
        ).order_by("-create_date")
        return super().filter_queryset(queryset)


class CompanyOrderPaymentPaidViewSet(
    viewsets.ModelViewSet,
):
    """Operations on Company order payment paid."""

    serializer_class = serializers.CompanyOrderPaymentPaidSerializer
    queryset = CompanyOrderPaymentPaid.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user_id"] = self.request.user.id
        return context

    def filter_queryset(self, queryset):
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        queryset = queryset.filter(
            companyorderpayment__companyorderdelivery__companyorder__companytype__company=member.company
        ).order_by("-create_date")
        return super().filter_queryset(queryset)


class CompanyOrderPaymentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.CompanyOrderPaymentSerializer
    queryset = CompanyOrderPayment.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status"]
