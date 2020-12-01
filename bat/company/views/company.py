
from django.utils.translation import ugettext_lazy as _

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions


from bat.company import serializers
from bat.company.models import (
    CompanyContract,
    CompanyCredential,
    ComponentGoldenSample,
    ComponentMe,
)
from bat.company.utils import get_member
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
    permission_classes = (IsAuthenticated, DRYPermissions,)
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
