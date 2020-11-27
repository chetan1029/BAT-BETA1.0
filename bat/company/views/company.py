from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import mixins, status, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rolepermissions.checkers import has_permission
from rolepermissions.permissions import revoke_permission
from rolepermissions.roles import RolesManager, assign_role, clear_roles
from dry_rest_permissions.generics import DRYPermissions
from invitations.utils import get_invitation_model
from notifications.signals import notify


from bat.company import serializers
from bat.company.models import (
    CompanyContract
)
from bat.company.utils import get_member
from bat.mixins.mixins import ArchiveMixin, RestoreMixin


class CompanyContractViewSet(viewsets.ModelViewSet):
    """Operations on CompanyContract."""

    serializer_class = serializers.CompanyContractSerializer
    queryset = CompanyContract.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [
        DjangoFilterBackend,
    ]
    filterset_fields = ["is_active"]

    archive_message = _("Company contract is archived")
    restore_message = _("Company contract is restored")

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
        queryset = queryset.filter(company_member=member).order_by(
            "-create_date"
        )
        return super().filter_queryset(queryset)

    def perform_create(self, serializer):
        company_contract = serializer.save()
        company_contract.save_pdf_file()
