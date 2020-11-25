from decimal import Decimal

from django.contrib.auth.models import Group, Permission
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from invitations.utils import get_invitation_model
from rolepermissions.roles import get_user_roles
from djmoney.settings import CURRENCY_CHOICES

from bat.company.models import (
    Bank,
    Company,
    CompanyPaymentTerms,
    HsCode,
    Location,
    Member,
    PackingBox,
    Tax,
    CompanyType,
)
from bat.company.utils import get_list_of_permissions, get_list_of_roles, get_member
from bat.serializersFields.serializers_fields import WeightField, CountrySerializerField
from bat.setting.models import Category
from bat.globalutils.utils import get_cbm


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
    country = CountrySerializerField()

    class Meta:
        model = Company
        fields = (
            "id",
            "address1",
            "address2",
            "zip",
            "city",
            "region",
            "country",
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


class ReversionSerializerMixin(serializers.ModelSerializer):

    force_create = serializers.BooleanField(default=False)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret.pop("force_create")
        return ret

    def find_similar_objects(self, user=None, company_id=None, data=None):
        """
        find similer objects based on passed data.
        override this method to provide complex filters.
        """
        ModelClass = self.Meta.model
        return ModelClass.objects.filter(
            is_active=True, company__id=company_id, **data)

    def validate(self, data):
        force_create = data.pop("force_create", False)
        data = super().validate(data)
        if not force_create:
            kwargs = self.context["request"].resolver_match.kwargs
            founded_data = self.find_similar_objects(
                user=self.context["request"].user, company_id=kwargs.get("company_pk", None), data=data)
            if founded_data.exists():
                raise serializers.ValidationError({"detail": _(
                    "Item with same data exixts."
                ), "existing_items": list(founded_data.values_list("id", flat=True))})
        return data


class CompanyPaymentTermsSerializer(ReversionSerializerMixin):
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
            "force_create",
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
        deposit = Decimal(data.get("deposit", 0))
        on_delivery = Decimal(data.get("on_delivery", 0))
        receiving = Decimal(data.get("receiving", 0))

        total = (
            deposit + on_delivery + receiving
        )
        if total > 100:
            raise serializers.ValidationError(
                _(
                    "Total amount can't be more than 100%. Please check again."
                )
            )
        remaining = Decimal(100) - total
        title = (
            "PAY"
            + str(deposit)
            + "-"
            + str(on_delivery)
            + "-"
            + str(receiving)
            + "-"
            + str(remaining)
            + "-"
            + str(data.get("payment_days", 0))
            + "Days"
        )
        data["remaining"] = remaining
        data["title"] = title
        return super().validate(data)


class BankSerializer(ReversionSerializerMixin):
    """Serializer for bank."""
    country = CountrySerializerField()
    currency = serializers.MultipleChoiceField(choices=CURRENCY_CHOICES)

    class Meta:
        """Define field that we wanna show in the Json."""

        model = Bank
        fields = (
            "id",
            "company",
            "name",
            "benificary",
            "account_number",
            "iban",
            "swift_code",
            "address1",
            "address2",
            "zip",
            "city",
            "region",
            "country",
            "currency",
            "is_active",
            "force_create",
        )
        read_only_fields = (
            "id",
            "is_active",
            "extra_data",
            "company",
            "create_date",
            "update_date",
        )

    def find_similar_objects(self, user=None, company_id=None, data=None):
        """
        find similer bank objects based on passed data
        """
        ModelClass = self.Meta.model
        query_data = {}
        query_data["name"] = data.get("name", "")
        query_data["benificary"] = data.get("benificary", "")
        query_data["account_number"] = data.get("account_number", "")
        query_data["iban"] = data.get("iban", "")
        query_data["swift_code"] = data.get("swift_code", "")
        query_data["address1"] = data.get("address1", "")
        query_data["address2"] = data.get("address2", "")
        query_data["zip"] = data.get("zip", "")
        query_data["region"] = data.get("region", "")
        query_data["country"] = data.get("country", "")
        currency = data.get("currency", "")
        if currency:
            query_data["currency__regex"] = ",".join(currency)

        return ModelClass.objects.filter(
            is_active=False, company__id=company_id, **query_data)


class LocationSerializer(ReversionSerializerMixin):
    """Serializer for location."""
    country = CountrySerializerField()

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
            "force_create",
        )
        read_only_fields = (
            "id",
            "is_active",
            "extra_data",
            "company",
            "create_date",
            "update_date",
        )

    def find_similar_objects(self, user=None, company_id=None, data=None):
        """
        find similer location objects based on passed data
        """
        ModelClass = self.Meta.model
        query_data = {}
        query_data["name"] = data.get("name", "")
        query_data["address1"] = data.get("address1", "")
        query_data["address2"] = data.get("address2", "")
        query_data["zip"] = data.get("zip", "")
        query_data["region"] = data.get("region", "")
        query_data["country"] = data.get("country", "")
        return ModelClass.objects.filter(
            is_active=False, company__id=company_id, **query_data)


class PackingBoxSerializer(ReversionSerializerMixin):
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
            "force_create",
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

    def validate(self, data):
        data["cbm"] = get_cbm(
            data.get("length"),
            data.get("width"),
            data.get("depth"),
            data.get("length_unit"),
        )
        return super().validate(data)

    def find_similar_objects(self, user=None, company_id=None, data=None):
        """
        find similer bank objects based on passed data
        """
        ModelClass = self.Meta.model
        query_data = {}
        query_data["name"] = data.get("name", "")
        query_data["length"] = data.get("length", "")
        query_data["width"] = data.get("width", "")
        query_data["depth"] = data.get("depth", "")
        query_data["length_unit"] = data.get("length_unit", "")
        query_data["cbm"] = data.get("cbm", "")
        query_data["weight"] = data.get("weight", "")
        return ModelClass.objects.filter(
            is_active=False, company__id=company_id, **query_data)


class HsCodeSerializer(ReversionSerializerMixin):
    """Serializer for HsCode."""

    class Meta:
        """Define field that we wanna show in the Json."""

        model = HsCode
        fields = ("id", "hscode", "material", "use",
                  "is_active", "extra_data", "force_create",)
        read_only_fields = (
            "id",
            "is_active",
            "extra_data",
            "company",
            "create_date",
            "update_date",
        )


class TaxSerializer(ReversionSerializerMixin):
    """Serializer for Tax."""
    from_country = CountrySerializerField()
    to_country = CountrySerializerField()

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
            "force_create",
        )
        read_only_fields = (
            "id",
            "is_active",
            "extra_data",
            "company",
            "create_date",
            "update_date",
        )

