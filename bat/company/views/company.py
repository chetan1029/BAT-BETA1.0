from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import mixins, viewsets, status
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from bat.setting.models import Category
from bat.company import serializers
from bat.company.models import (
    Company,
    CompanyType,
    CompanyContract,
    CompanyCredential,
    CompanyOrder,
    CompanyOrderCase,
    CompanyOrderDelivery,
    CompanyOrderDeliveryTestReport,
    CompanyOrderInspection,
    CompanyOrderPayment,
    CompanyOrderPaymentPaid,
    CompanyProduct,
    ComponentGoldenSample,
    ComponentMe,
    ComponentPrice,
)
from bat.mixins.mixins import ArchiveMixin, RestoreMixin


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
        queryset = super().filter_queryset(queryset)
        company_id = self.kwargs.get("company_pk", None)
        return queryset.filter(companytype__company__id=company_id).order_by(
            "-create_date"
        )


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


class ComponentGoldenSampleViewSet(
    ArchiveMixin, RestoreMixin, viewsets.ModelViewSet
):
    """Operations on Component Golden Sample."""

    serializer_class = serializers.ComponentGoldenSampleSerializer
    queryset = ComponentGoldenSample.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Component golden sample is archived")
    restore_message = _("Component golden sample is restored")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user"] = self.request.user
        return context

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(
            componentme__companytype__company__id=company_id
        ).order_by("-create_date")


class ComponentPriceViewSet(ArchiveMixin, RestoreMixin, viewsets.ModelViewSet):
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
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(
            componentgoldensample__componentme__companytype__company__id=company_id
        ).order_by("-create_date")


class CompanyProductViewSet(ArchiveMixin, RestoreMixin, viewsets.ModelViewSet):
    """Operations on Company Product."""

    serializer_class = serializers.CompanyProductSerializer
    queryset = CompanyProduct.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Company product is archived")
    restore_message = _("Company product is restored")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user"] = self.request.user
        return context

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(companytype__company__id=company_id).order_by(
            "-create_date"
        )


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

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(companytype__company__id=company_id).order_by(
            "-create_date"
        )


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

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(
            companyorder__companytype__company__id=company_id
        ).order_by("-create_date")


class CompanyOrderCaseViewSet(viewsets.ModelViewSet):
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
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(
            companyorder__companytype__company__id=company_id
        ).order_by("-create_date")


class CompanyOrderInspectionViewSet(viewsets.ModelViewSet):
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
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(
            companyorder__companytype__company__id=company_id
        ).order_by("-create_date")


class CompanyOrderDeliveryTestReportViewSet(viewsets.ModelViewSet):
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
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(
            companyorderdelivery__companyorder__companytype__company__id=company_id
        ).order_by("-create_date")


class CompanyOrderPaymentPaidViewSet(viewsets.ModelViewSet):
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
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(
            companyorderpayment__companyorderdelivery__companyorder__companytype__company__id=company_id
        ).order_by("-create_date")


class CompanyOrderPaymentViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = serializers.CompanyOrderPaymentSerializer
    queryset = CompanyOrderPayment.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status"]

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(
            companyorderdelivery__companyorder__companytype__company__id=company_id
        ).order_by("-create_date")


class PartnerCompanyViewSet(
    ArchiveMixin, RestoreMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = CompanyType.objects.all()
    serializer_class = serializers.PartnerCompanySerializer
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Partner is archived")
    restore_message = _("Partner is restored")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user_id"] = self.request.user.id
        context["company_id"] = self.kwargs.get("company_pk", None)
        return context

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        company_id = self.kwargs.get("company_pk", None)
        queryset = queryset.filter(company_id=company_id)
        return queryset


class ClientCompanyViewSet(
    ArchiveMixin, RestoreMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = CompanyType.objects.all()
    serializer_class = serializers.PartnerCompanySerializer
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    archive_message = _("Client is archived")
    restore_message = _("Client is restored")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user_id"] = self.request.user.id
        context["company_id"] = self.kwargs.get("company_pk", None)
        return context

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        company_id = self.kwargs.get("company_pk", None)
        queryset = queryset.filter(partner_id=company_id)
        return queryset
