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
    Bank,
    Company,
    CompanyPaymentTerms,
    HsCode,
    Location,
    Member,
    PackingBox,
    Tax,
)
from bat.company.utils import get_member
from bat.mixins.mixins import ArchiveMixin, RestoreMixin


Invitation = get_invitation_model()
User = get_user_model()


class CompanyViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):  # TODO perform delete
    queryset = Company.objects.all()
    serializer_class = serializers.CompanySerializer
    permission_classes = (IsAuthenticated, DRYPermissions)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user_id"] = self.request.user.id
        return context

    def perform_create(self, serializer):
        company = serializer.save()
        request = self.request

        extra_data = {}
        extra_data["user_role"] = "company_admin"
        member, create = Member.objects.get_or_create(
            job_title="Admin",
            user=self.request.user,
            company=company,
            invited_by=self.request.user,
            is_admin=True,
            is_active=True,
            invitation_accepted=True,
            extra_data=extra_data,
        )
        if create:
            # fetch user role from the User and assign after signup.
            assign_role(member, member.extra_data["user_role"])

        if self.request.user.extra_data["step"] == 1:
            self.request.user.extra_data["step"] = 2
            self.request.user.extra_data["step_detail"] = "account setup"
            self.request.user.save()

    def filter_queryset(self, queryset):
        request = self.request
        queryset = queryset.filter(member_company__user__id=request.user.id)
        return queryset


"""
input to content
{
"first_name":"chetan",
"last_name":"singh",
"email":"chetanbadgujar92@gmail.com",
"job_title":"manager",
"invitation_type":"member_invitation",
"role":"supply_chain_manager",
"permissions":["view_company_banks","add_company_banks","change_company_banks","archived_company_banks","restore_company_banks"]
}

{
"first_name":"fname",
"last_name":"lname",
"email":"fnamelname@gmail.com",
"job_title":"manager",
"invitation_type":"vendor_invitation",
"vendor_name":"test",
"vendor_type":{"id":1,"name":"test"}
}
"""


class InvitationCreate(viewsets.ViewSet):
    def create(self, request, company_pk):
        """
        create and seng invivation to given email address
        """
        member = get_member(company_id=company_pk, user_id=request.user.id)
        company = member.company
        if not has_permission(member, "add_staff_member"):
            return Response(
                {
                    "message": _(
                        "You are not allowed to add staff member to this company"
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        context = {}
        context["company_id"] = company.id
        serializer = serializers.InvitationDataSerializer(
            data=request.data, context=context
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        data = serializer.data

        email = data["email"].lower()
        notify_verb = _("sent you an staff member invitation")
        notify_description = _(
            "{} has invited you to access {} as a staff \
                    member."
        )

        # User Detail
        first_name = data["first_name"]
        last_name = data["last_name"]
        job_title = data["job_title"]
        user_detail = {
            "first_name": first_name,
            "last_name": last_name,
            "job_title": job_title,
        }

        # TODO vendor_invitation test
        invitation_type = data["invitation_type"]
        if invitation_type and invitation_type == "vendor_invitation":
            notify_verb = _("sent you an vendor admin invitation")
            notify_description = _(
                "{} has invited you to access {} as a vendor \
                    admin."
            )
            # Company Detail
            company_detail = {
                "company_id": company.id,
                "company_name": company.name,
                "vendor_name": data["vendor_name"],
                "vendor_type": data["vendor_type"],
            }

            # User Roles
            role = "vendor_admin"
            role_obj = RolesManager.retrieve_role(role)
            user_roles = {
                "role": role,
                "perms": list(role_obj.permission_names_list()),
            }

            extra_data = {}
            extra_data["type"] = "Vendor Invitation"
        else:
            # Company Detail
            company_detail = {
                "company_id": company.id,
                "company_name": company.name,
            }

            # User Roles
            user_roles = {
                "role": data["role"],
                "perms": list(data["permissions"]),
            }

            extra_data = {}
            extra_data["type"] = "Member Invitation"

        inviter = User.objects.get(pk=request.user.id)

        invite = Invitation.create(
            email,
            inviter=inviter,
            user_detail=user_detail,
            company_detail=company_detail,
            user_roles=user_roles,
            extra_data=extra_data,
        )
        invite.send_invitation(request)

        user = User.objects.filter(email=email).first()
        # url to accept invitation
        print(
            "\n \n \naccept url : ",
            reverse(
                "api:users:invitationdetail-accept", kwargs={"pk": invite.id}
            ),
            "\n \n \n",
        )
        if user:
            actions = [
                {
                    "href": reverse(
                        "api:users:invitationdetail-accept",
                        kwargs={"pk": invite.id},
                    ),
                    "title": _("View invitation"),
                }
            ]
            notify.send(
                request.user,
                recipient=user,
                verb=notify_verb,
                action_object=invite,
                target=company,
                description=notify_description.format(
                    request.user.username, company.name
                ),
                actions=actions,
            )
        return Response(
            {"message": _("Invitation was successfully sent.")},
            status=status.HTTP_200_OK,
        )


# class SetCompanyAndUserInContexMixin(viewsets.GenericViewSet):

#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         context["user_id"] = self.request.user.id
#         return context


# Member

class MemberViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    ArchiveMixin,
    RestoreMixin,
    viewsets.GenericViewSet,
):
    serializer_class = serializers.MemberSerializer
    queryset = Member.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["is_active", "is_admin", "invitation_accepted"]
    search_fields = ["job_title"]

    archive_message = _("Member is archived")
    restore_message = _("Member is restored")

    def filter_queryset(self, queryset):
        """Filter members by current company"""

        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        queryset = queryset.filter(company=member.company).order_by(
            "-create_date"
        )
        return super().filter_queryset(queryset)

    def perform_update(self, serializer):
        """ update member with given roles and permissions """
        instance = self.get_object()
        data = serializer.validated_data.copy()
        clear_roles(instance)
        for group in data.get("groups", None):
            assign_role(instance, group.name)
            role_obj = RolesManager.retrieve_role(group.name)
            # remove unneccesary permissions
            for perm in role_obj.get_all_permissions():
                if perm not in data.get("user_permissions", None):
                    revoke_permission(instance, perm.codename)
        serializer.validated_data.pop("groups")
        serializer.validated_data.pop("user_permissions")
        serializer.save()


# Company setting common viewset
class CompanySettingBaseViewSet(
    ArchiveMixin, RestoreMixin, viewsets.ModelViewSet
):
    """List all the payment terms."""

    class Meta:
        abstract = True

    def filter_queryset(self, queryset):
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        queryset = queryset.filter(company=member.company).order_by(
            "-create_date"
        )
        return super().filter_queryset(queryset)

    def perform_create(self, serializer):
        """Set the data for who is the owner or creater."""
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        serializer.validated_data.pop("force_create", None)
        serializer.save(company=member.company)


# Payment terms

class CompanyPaymentTermsViewSet(CompanySettingBaseViewSet):
    """Operations on payment terms."""

    serializer_class = serializers.CompanyPaymentTermsSerializer
    queryset = CompanyPaymentTerms.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["is_active", "payment_days"]
    search_fields = ["title"]

    archive_message = _("Paymentterms is archived")
    restore_message = _("Paymentterms is restored")

    def perform_create(self, serializer):
        """
        Append extra data in validated data.
        """
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        serializer.save(
            company=member.company
        )

# Bank


class BankViewSet(CompanySettingBaseViewSet):
    """Operations on bank."""

    serializer_class = serializers.BankSerializer
    queryset = Bank.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["is_active"]
    search_fields = ["name"]

    archive_message = _("Bank is archived")
    restore_message = _("Bank is restored")


# Location


class LocationViewSet(CompanySettingBaseViewSet):
    """Operations on location."""

    serializer_class = serializers.LocationSerializer
    queryset = Location.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["is_active", "city", "region"]
    search_fields = ["name", "city", "region"]

    archive_message = _("Location is archived")
    restore_message = _("Location is restored")


# PackingBox


class PackingBoxViewSet(CompanySettingBaseViewSet):
    """Operations on PackingBox."""

    serializer_class = serializers.PackingBoxSerializer
    queryset = PackingBox.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["is_active"]
    search_fields = ["name"]

    archive_message = _("Packing box is archived")
    restore_message = _("Packing box is restored")

    def perform_create(self, serializer):
        """
        Append extra data in validated data.
        """
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        serializer.save(company=member.company)


# For weight use
# {'weight': 1.0, 'unit': 'kg'}


# HsCode
class HsCodeBoxViewSet(CompanySettingBaseViewSet):
    """Operations on HsCode."""

    serializer_class = serializers.HsCodeSerializer
    queryset = HsCode.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["is_active"]
    search_fields = ["hscode", "material", "use"]

    archive_message = _("HsCode is archived")
    restore_message = _("HsCode is restored")


# Tax
class TaxBoxViewSet(CompanySettingBaseViewSet):
    """Operations on Tax."""

    serializer_class = serializers.TaxSerializer
    queryset = Tax.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [
        DjangoFilterBackend,
        # SearchFilter,
    ]
    filterset_fields = ["is_active"]
    # search_fields = ["name"]

    archive_message = _("Tax is archived")
    restore_message = _("Tax is restored")
