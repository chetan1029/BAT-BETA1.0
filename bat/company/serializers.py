from decimal import Decimal

from rest_framework import serializers
from rest_framework.utils import json
from rest_framework.exceptions import ValidationError


from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Group, Permission

from invitations.utils import get_invitation_model
from measurement.measures import Weight
from rolepermissions.roles import get_user_roles, assign_role
from rolepermissions.permissions import available_perm_status


from bat.company.models import (
    Company, Member, CompanyPaymentTerms, Bank, Location, PackingBox, HsCode, Tax)
from bat.company.utils import get_list_of_roles, get_list_of_permissions
from bat.company import constants
from bat.company.utils import get_member

Invitation = get_invitation_model()


class WeightField(serializers.Field):

    def to_representation(self, value):
        ret = {"weight": value.value,
               "unit": value.unit}
        return ret

    def to_internal_value(self, data):
        try:
            data = eval(data)
            unit = data["unit"]
            value = data["weight"]
            kwargs = {unit: value}
            if unit in constants.WEIGHT_UNIT_TYPE_LIST:
                return Weight(**kwargs)
            else:
                raise ValidationError("%s is not a valid %s" % (data, "Unit"))
        except Exception:
            if data:
                raise ValidationError(
                    "%s is not a valid %s" % (data, "formate"))
            else:
                if self.required:
                    raise ValidationError("%s is %s" % ("weight", "required"))
                else:
                    # TODO
                    return data


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
        fields = "__all__"
        # read_only_fields = ('owner',)

    def get_roles(self, obj):
        user_id = self.context.get("user_id", None)
        member = get_member(company_id=obj.id, user_id=user_id)
        roles = get_user_roles(member)
        return [role.get_name() for role in roles]


class MemberSerializer(serializers.ModelSerializer):
    # roles = serializers.SerializerMethodField()
    # user_permissions_list = serializers.SerializerMethodField()
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
        read_only_fields = ("is_superuser", "user", "is_active",
                            "invited_by", "is_admin", "invitation_accepted", "extra_data", "last_login")

    # def get_roles(self, obj):
    #     roles = get_user_roles(obj)
    #     return [role.get_name() for role in roles]

    # def get_user_permissions_list(self, obj):
    #     perms = available_perm_status(obj)
    #     return [perm for perm, condition in perms.items() if condition]


class InvitationDataSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    job_title = serializers.CharField(required=True)
    role = serializers.ChoiceField(choices=get_list_of_roles(), required=True)
    permissions = serializers.MultipleChoiceField(
        choices=get_list_of_permissions(), required=True)

    def validate(self, data):
        """
        Check that start is before finish.
        """
        email = data['email']
        company_id = self.context.get("company_id", None)
        if company_id and email:
            if Member.objects.filter(
                company_id=int(company_id), user__email=email
            ).exists():
                raise serializers.ValidationError(
                    _("User already is your staff member."))
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
        read_only_fields = ("is_active", "extra_data", "remaining", "title")


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
        read_only_fields = ("is_active", "extra_data",
                            "company", "create_date", "update_date")


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
        read_only_fields = ("is_active", "extra_data",
                            "company", "create_date", "update_date")


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
            "cbm",
            "length_unit",
            "weight",
            "is_active",
            "extra_data",
        )
        read_only_fields = ("is_active", "extra_data",
                            "company", "create_date", "update_date")


class HsCodeSerializer(serializers.ModelSerializer):
    """Serializer for HsCode."""

    class Meta:
        """Define field that we wanna show in the Json."""

        model = HsCode
        fields = (
            "id",
            "hscode",
            "material",
            "use",
            "is_active",
            "extra_data",
        )
        read_only_fields = ("is_active", "extra_data",
                            "company", "create_date", "update_date")


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
        read_only_fields = ("is_active", "extra_data",
                            "company", "create_date", "update_date")
