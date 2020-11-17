from decimal import Decimal

from django.contrib.auth.models import Group, Permission
from django.utils.translation import ugettext_lazy as _
from invitations.utils import get_invitation_model
from measurement.measures import Weight
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rolepermissions.roles import get_user_roles

from bat.company import constants
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
from bat.company.utils import get_list_of_permissions, get_list_of_roles, get_member
from bat.serializersFields.serializers_fields import WeightField
from bat.setting.models import Category

Invitation = get_invitation_model()


class GroupsListField(serializers.ListField):
    def to_representation(self, data):
        """
        List of group name.
        """
        return [group.name for group in data.all()]

    def to_internal_value(self, data):
        """
        return queryset of Group model from list of group name.
        """
        qs = Group.objects.filter(name__in=data)
        return qs


class PermissionListField(serializers.ListField):
    def to_representation(self, data):
        """
        List of permission name.
        """
        return [permission.codename for permission in data.all()]

    def to_internal_value(self, data):
        """
        return queryset of Permission model from list of permission name.
        """
        qs = Permission.objects.filter(codename__in=data)
        return qs


class CompanySerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = (
            "id",
            "name",
            "abbreviation",
            "email",
            "logo",
            "phone_number",
            "organization_number",
            "currency",
            "unit_system",
            "weight_unit",
            "language",
            "time_zone",
            "is_active",
            "extra_data",
            "roles",
        )
        read_only_fields = ("id", "is_active", "extra_data", "roles")

    def get_roles(self, obj):
        user_id = self.context.get("user_id", None)
        member = get_member(company_id=obj.id, user_id=user_id)
        roles = get_user_roles(member)
        return [role.get_name() for role in roles]


class MemberSerializer(serializers.ModelSerializer):
    groups = GroupsListField()
    user_permissions = PermissionListField()

    class Meta:
        model = Member
        fields = (
            "id",
            "is_superuser",
            "groups",
            "user_permissions",
            "job_title",
            "user",
            "invited_by",
            "is_admin",
            "is_active",
            "invitation_accepted",
            "extra_data",
            "last_login",
        )
        read_only_fields = (
            "id",
            "is_superuser",
            "user",
            "is_active",
            "invited_by",
            "is_admin",
            "invitation_accepted",
            "extra_data",
            "last_login",
        )


class InvitationDataSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    job_title = serializers.CharField(required=True)
    role = serializers.ChoiceField(choices=get_list_of_roles(), required=False)
    permissions = serializers.MultipleChoiceField(
        choices=get_list_of_permissions(), required=False
    )
    invitation_type = serializers.ChoiceField(
        ["vendor_invitation", "member_invitation"], required=True
    )
    vendor_name = serializers.CharField(required=False)
    vendor_type = serializers.JSONField(required=False)

    # def __init__(self, *args, **kwargs):
    #     print("\n \n", self.fields,
    #           " : self.fields")
    #     super().__init__(self, *args, **kwargs)

    def validate(self, data):
        """
        Check that start is before finish.
        """
        email = data["email"]
        company_id = self.context.get("company_id", None)

        if (
            data["invitation_type"]
            and data["invitation_type"] == "vendor_invitation"
        ):
            if not data["vendor_name"]:
                raise serializers.ValidationError(
                    _("Vendor name is required field")
                )
            if not data["vendor_type"]:
                raise serializers.ValidationError(
                    _("Vendor type is required field")
                )
            if data["vendor_type"]:
                choices = list(Category.objects.values("id", "name"))
                if data["vendor_type"] not in choices:
                    raise serializers.ValidationError(
                        _("Vendor type is not valid")
                    )
            if data["vendor_type"] and data["vendor_name"] and email:
                invitations = Invitation.objects.filter(
                    email=email,
                    company_detail__company_name__iexact=data["vendor_name"],
                )
                if invitations.exists():
                    msg = _(
                        "Invitation already sent for this vendor and email."
                    )
                    raise serializers.ValidationError(msg)
        else:
            if not data["role"]:
                raise serializers.ValidationError(_("Role is required field"))
            if not data["permissions"]:
                raise serializers.ValidationError(
                    _("permissions is required field")
                )
            if company_id and email:
                if Member.objects.filter(
                    company_id=int(company_id), user__email=email
                ).exists():
                    raise serializers.ValidationError(
                        _("User already is your staff member.")
                    )
                else:
                    invitations = Invitation.objects.filter(
                        email=email, company_detail__company_id=int(company_id)
                    )
                    if invitations.exists():
                        msg = _("Invitation already sent for this email.")
                        raise serializers.ValidationError(msg)

        return super().validate(data)


class CompanyPaymentTermsSerializer(serializers.ModelSerializer):
    """Serializer for payment terms."""

    class Meta:
        """Define field that we wanna show in the Json."""

        model = CompanyPaymentTerms
        fields = (
            "id",
            "title",
            "deposit",
            "on_delivery",
            "receiving",
            "remaining",
            "payment_days",
            "is_active",
            "extra_data",
        )
        read_only_fields = (
            "id",
            "is_active",
            "extra_data",
            "remaining",
            "company",
            "title",
        )

    def validate(self, data):
        """Validate if total percetange is more than 100%."""
        deposit = data["deposit"]
        on_delivery = data["on_delivery"]
        receiving = data["receiving"]
        if deposit and on_delivery and receiving:
            total = (
                Decimal(deposit) + Decimal(on_delivery) + Decimal(receiving)
            )
            if total > 100:
                raise serializers.ValidationError(
                    _(
                        "Total amount can't be more than 100%. Please check again."
                    )
                )
        return super().validate(data)


class BankSerializer(serializers.ModelSerializer):
    """Serializer for bank."""

    class Meta:
        """Define field that we wanna show in the Json."""

        model = Bank
        fields = (
            "id",
            "name",
            "account_number",
            "iban",
            "swift_code",
            "currency",
            "is_active",
            "extra_data",
        )
        read_only_fields = (
            "id",
            "is_active",
            "extra_data",
            "company",
            "create_date",
            "update_date",
        )


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for location."""

    class Meta:
        """Define field that we wanna show in the Json."""

        model = Location
        fields = (
            "id",
            "name",
            "is_active",
            "extra_data",
            "address1",
            "address2",
            "zip",
            "city",
            "region",
            "country",
        )
        read_only_fields = (
            "id",
            "is_active",
            "extra_data",
            "company",
            "create_date",
            "update_date",
        )


class PackingBoxSerializer(serializers.ModelSerializer):
    """Serializer for PackingBox."""

    weight = WeightField(required=True)

    class Meta:
        """Define field that we wanna show in the Json."""

        model = PackingBox
        fields = (
            "id",
            "name",
            "length",
            "width",
            "depth",
            "length_unit",
            "weight",
            "cbm",
            "is_active",
            "extra_data",
        )
        read_only_fields = (
            "id",
            "is_active",
            "extra_data",
            "company",
            "cbm",
            "create_date",
            "update_date",
        )


class HsCodeSerializer(serializers.ModelSerializer):
    """Serializer for HsCode."""

    class Meta:
        """Define field that we wanna show in the Json."""

        model = HsCode
        fields = ("id", "hscode", "material", "use", "is_active", "extra_data")
        read_only_fields = (
            "id",
            "is_active",
            "extra_data",
            "company",
            "create_date",
            "update_date",
        )


class TaxSerializer(serializers.ModelSerializer):
    """Serializer for Tax."""

    class Meta:
        """Define field that we wanna show in the Json."""

        model = Tax
        fields = (
            "id",
            "from_country",
            "to_country",
            "custom_duty",
            "vat",
            "is_active",
            "extra_data",
        )
        read_only_fields = (
            "id",
            "is_active",
            "extra_data",
            "company",
            "create_date",
            "update_date",
        )
