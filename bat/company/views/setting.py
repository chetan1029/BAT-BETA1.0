from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from dry_rest_permissions.generics import DRYPermissions
from invitations.utils import get_invitation_model
from notifications.signals import notify
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rolepermissions.checkers import has_permission
from rolepermissions.permissions import revoke_permission
from rolepermissions.roles import RolesManager, assign_role, clear_roles

from bat.company import serializers
from bat.company.models import (
    Asset,
    AssetTransfer,
    Bank,
    Company,
    CompanyPaymentTerms,
    CompanyType,
    HsCode,
    Location,
    Member,
    PackingBox,
    Tax,
)
from bat.company.utils import get_member, set_default_company_payment_terms
from bat.mixins.mixins import ArchiveMixin, RestoreMixin
from bat.setting.models import Category
from bat.subscription.utils import set_default_subscription_plan_on_company
from bat.users.serializers import InvitationSerializer

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
        with transaction.atomic():
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

            set_default_company_payment_terms(company=company)
            if not company.companytype_company.exists():
                set_default_subscription_plan_on_company(company=company)

            if self.request.user.extra_data["step"] == 1:
                self.request.user.extra_data["step"] = 2
                self.request.user.extra_data["step_detail"] = "account setup"
                self.request.user.save()

    def filter_queryset(self, queryset):
        request = self.request
        queryset = super().filter_queryset(queryset)
        return queryset.filter(member_company__user__id=request.user.id)


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


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        operation_description="Allows to invite member or vendor or other users",
        request_body=serializers.InvitationDataSerializer(),
        responses={201: serializers.InvitationDataSerializer()},
    ),
)
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
                    "detail": _(
                        "You are not allowed to add staff member to this company"
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        context = {}
        context["company_id"] = company.id
        context["user"] = request.user

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


is_accepted_param = openapi.Parameter(
    "is_accepted",
    openapi.IN_QUERY,
    description="Filters by status",
    type=openapi.TYPE_BOOLEAN,
    required=False,
)


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Returns all the invitations",
        responses={200: InvitationSerializer(many=True)},
        manual_parameters=[is_accepted_param],
    ),
)
class CompanyInvitationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer

    def filter_queryset(self, queryset):
        """
        filter invitations for current user.
        return pending invitations
        """
        queryset = super().filter_queryset(queryset)
        queryset = queryset.filter(
            company_detail__company_id=int(self.kwargs.get("company_pk", None))
        )

        is_accepted = self.request.GET.get("is_accepted", None)
        if is_accepted:
            queryset = queryset.filter(accepted=is_accepted == "true")
        return queryset

    @action(detail=True, methods=["post"])
    def resend(self, request, company_pk=None, pk=None):
        """
        Allows to resend the invite
        """
        instance = self.get_object()
        if instance.accepted == True:
            return Response(
                {"detail": _("Accepted successfully")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.send_invitation(request)

        return Response(
            {"detail": _("Invitations resent successfully")},
            status=status.HTTP_200_OK,
        )


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
        queryset = super().filter_queryset(queryset)
        return queryset.filter(company=member.company).order_by("-create_date")

    def perform_update(self, serializer):
        """ update member with given roles and permissions """
        instance = self.get_object()
        data = serializer.validated_data.copy()

        clear_roles(instance)
        for group in data.get("groups", []):
            assign_role(instance, group.name)
            role_obj = RolesManager.retrieve_role(group.name)
            # remove unneccesary permissions
            for perm in role_obj.get_all_permissions():
                if perm not in data.get("user_permissions", []):
                    revoke_permission(instance, perm.codename)
        serializer.validated_data.pop("groups", None)
        serializer.validated_data.pop("user_permissions", None)
        serializer.save()


# Company setting common viewset
class CompanySettingBaseViewSet(
    ArchiveMixin, RestoreMixin, viewsets.ModelViewSet
):
    """Company setting base view set."""

    class Meta:
        abstract = True

    def filter_queryset(self, queryset):
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        queryset = super().filter_queryset(queryset)
        return queryset.filter(company=member.company).order_by("-create_date")

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
        serializer.save(company=member.company)


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
class TaxViewSet(CompanySettingBaseViewSet):
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


# Asset
class AssetViewSet(CompanySettingBaseViewSet):
    """Operations on Asset."""

    serializer_class = serializers.AssetSerializer
    queryset = Asset.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [
        DjangoFilterBackend,
        # SearchFilter,
    ]
    filterset_fields = ["is_active"]
    # search_fields = ["name"]

    archive_message = _("Asset is archived")
    restore_message = _("Asset is restored")

    @action(detail=False, methods=["GET"], url_path="types")
    def get_types(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        types = (
            queryset.exclude(type__exact="")
            .exclude(type__isnull=True)
            .distinct("type")
            .values_list("type", flat=True)
            .order_by("type")
        )
        data = {}
        data["type_data"] = types
        return Response(data, status=status.HTTP_200_OK)


# Asset Transfer
class AssetTransferViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Operations on Asset Transfer."""

    serializer_class = serializers.AssetTransferSerializer
    queryset = AssetTransfer.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filterset_fields = ["asset", ]
    filter_backends = [
        DjangoFilterBackend,
        # SearchFilter,
    ]


category_param = openapi.Parameter(
    "category",
    openapi.IN_QUERY,
    description="Returns vendors belong to this category",
    type=openapi.TYPE_INTEGER,
    required=False,
)


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Returns all the vendors",
        responses={200: serializers.VendorCompanySerializer(many=True)},
        manual_parameters=[category_param],
    ),
)
@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        reqeust={serializers.CreateVendorCompanySerializer()}
    ),
)
class VendorCompanyViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Company.objects.all()
    serializer_class = serializers.VendorCompanySerializer
    permission_classes = (IsAuthenticated, DRYPermissions)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user_id"] = self.request.user.id
        context["company_id"] = self.kwargs.get("company_pk", None)
        return context

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        request = self.request

        company_id = self.kwargs.get("company_pk", None)

        category = self.request.GET.get("category", False)
        if category:
            vendor_categories = [category]
        else:
            # get vendor category
            vendor_categories = Category.objects.vendor_categories().values_list(
                "id", flat=True
            )

        vendor_companies = CompanyType.objects.filter(
            category__id__in=vendor_categories, company_id=company_id
        ).values_list("partner", flat=True)

        queryset = queryset.filter(pk__in=vendor_companies)
        return queryset

    def create(self, request, *args, **kwargs):
        context = {"request": request}
        context["user_id"] = self.request.user.id
        context["company_id"] = self.kwargs.get("company_pk", None)

        serializer = serializers.CreateVendorCompanySerializer(
            data=request.data, context=context
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        data = serializers.VendorCompanySerializer(instance=instance).data
        headers = self.get_success_headers(data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["GET"], url_path="members")
    def get_vendormembers(self, request, *args, **kwargs):
        company_id = self.kwargs.get("pk", None)
        if company_id:
            queryset = Member.objects.filter(company__id=company_id)
            members = serializers.VendorMemberSerializer(
                queryset, many=True
            ).data
            data = {}
            data["results"] = members
            return Response(data, status=status.HTTP_200_OK)


class SalesChannelCompanyViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Company.objects.all()
    serializer_class = serializers.VendorCompanySerializer
    permission_classes = (IsAuthenticated, DRYPermissions)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user_id"] = self.request.user.id
        context["company_id"] = self.kwargs.get("company_pk", None)
        return context

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        request = self.request

        company_id = self.kwargs.get("company_pk", None)

        category = self.request.GET.get("category", False)
        if category:
            sales_categories = [category]
        else:
            # get categories
            sales_categories = Category.objects.sales_channel_categories().values_list(
                "id", flat=True
            )

        companies = CompanyType.objects.filter(
            category__id__in=sales_categories, company_id=company_id
        ).values_list("partner", flat=True)

        queryset = queryset.filter(pk__in=companies)
        return queryset
