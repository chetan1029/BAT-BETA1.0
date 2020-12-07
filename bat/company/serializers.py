from decimal import Decimal

from django.db.models import Sum
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from djmoney.contrib.django_rest_framework import MoneyField
from djmoney.settings import CURRENCY_CHOICES
from djmoney.money import Money
from invitations.utils import get_invitation_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rolepermissions.roles import get_user_roles, assign_role


from bat.company.file_serializers import FileSerializer
from bat.company.models import (
    Bank,
    Company,
    CompanyContract,
    CompanyCredential,
    CompanyOrder,
    CompanyOrderDelivery,
    CompanyOrderDeliveryProduct,
    CompanyOrderProduct,
    CompanyPaymentTerms,
    CompanyProduct,
    CompanyType,
    ComponentGoldenSample,
    ComponentMe,
    ComponentPrice,
    File,
    HsCode,
    Location,
    Member,
    PackingBox,
    Tax,
    CompanyOrderCase,
    CompanyOrderInspection,
    CompanyOrderPayment,
    CompanyOrderDeliveryTestReport,
    CompanyOrderPaymentPaid
)
from bat.company.utils import get_list_of_permissions, get_list_of_roles, get_member
from bat.globalutils.utils import get_cbm, set_field_errors
from bat.product.constants import PRODUCT_STATUS_DRAFT
from bat.serializersFields.serializers_fields import (
    CountrySerializerField,
    MoneySerializerField,
    QueryFieldsMixin,
    WeightField,
    StatusField,
)
from bat.setting.models import Category
from bat.setting.utils import get_status
from bat.users.serializers import UserLoginActivitySerializer, UserSerializer
from bat.globalutils.utils import get_status_object

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


class MemberSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    roles = GroupsListField(source="groups")
    user_permissions = PermissionListField()
    user = UserSerializer()
    login_activities = serializers.SerializerMethodField()

    def get_login_activities(self, obj):
        return UserLoginActivitySerializer(
            obj.user.get_recent_logged_in_activities(), many=True
        ).data

    class Meta:
        model = Member
        fields = (
            "id",
            "roles",
            "user_permissions",
            "job_title",
            "user",
            "invited_by",
            "is_admin",
            "is_active",
            "invitation_accepted",
            "extra_data",
            "login_activities",
        )
        read_only_fields = (
            "id",
            "user",
            "is_active",
            "invited_by",
            "is_admin",
            "invitation_accepted",
            "extra_data",
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
        errors = {}
        if (
            data["invitation_type"]
            and data["invitation_type"] == "vendor_invitation"
        ):
            if not data["vendor_name"]:
                raise serializers.ValidationError(
                    {"vendor_name": _("Vendor name is required field")}
                )
            if not data["vendor_type"]:
                raise serializers.ValidationError(
                    {"vendor_type": _("Vendor type is required field")}
                )
            if data["vendor_type"]:
                choices = list(Category.objects.values("id", "name"))
                if data["vendor_type"] not in choices:
                    raise serializers.ValidationError(
                        {"vendor_type": _("Vendor type is not valid")}
                    )
            if data["vendor_type"] and data["vendor_name"] and email:
                invitations = Invitation.objects.filter(
                    email=email,
                    company_detail__company_name__iexact=data["vendor_name"],
                )
                if invitations.exists():
                    msg = {
                        "detail": _(
                            "Invitation already sent for this vendor and email."
                        )
                    }
                    raise serializers.ValidationError(msg)
        else:
            if not data["role"]:
                raise serializers.ValidationError(
                    {"role": _("Role is required field")}
                )
            if not data["permissions"]:
                raise serializers.ValidationError(
                    {"permissions": _("permissions is required field")}
                )
            if company_id and email:
                if Member.objects.filter(
                    company_id=int(company_id), user__email=email
                ).exists():
                    raise serializers.ValidationError(
                        {"detail": _("User already is your staff member.")}
                    )
                else:
                    invitations = Invitation.objects.filter(
                        email=email, company_detail__company_id=int(company_id)
                    )
                    if invitations.exists():
                        msg = {
                            "detail": _(
                                "Invitation already sent for this email."
                            )
                        }
                        raise serializers.ValidationError(msg)

        return super().validate(data)


class ReversionSerializerMixin(serializers.ModelSerializer):

    force_create = serializers.BooleanField(default=False)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret.pop("force_create")
        return ret

    def get_query_data(self, data=None):
        """
        generate query_data to find similer objects based on passed data
        """
        return data

    def find_similar_objects(
        self, user=None, company_id=None, data=None, pk=None
    ):
        """
        find similer objects based on passed data.
        override this method to provide complex filters.
        """
        ModelClass = self.Meta.model
        query_data = self.get_query_data(data)
        if pk:
            founded_data = ModelClass.objects.filter(
                is_active=False, company__id=company_id, **query_data
            ).exclude(pk=pk)
        else:
            founded_data = ModelClass.objects.filter(
                is_active=False, company__id=company_id, **query_data
            )

        return founded_data

    def validate(self, data):
        force_create = data.pop("force_create", False)
        data = super().validate(data)
        kwargs = self.context["request"].resolver_match.kwargs
        if not force_create:
            founded_data = self.find_similar_objects(
                user=self.context["request"].user,
                company_id=kwargs.get("company_pk", None),
                data=data,
                pk=kwargs.get("pk", None),
            )
            if founded_data.exists():
                raise serializers.ValidationError(
                    {
                        "detail": _("Item with same data exixts."),
                        "existing_items": list(
                            founded_data.values_list("id", flat=True)
                        ),
                    }
                )
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

        total = deposit + on_delivery + receiving
        if total > 100:
            raise serializers.ValidationError(
                _("Total amount can't be more than 100%. Please check again.")
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

    def get_query_data(self, data=None):
        """
        generate query_data to find similer bank objects based on passed data
        """
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

        return query_data


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

    def get_query_data(self, data=None):
        """
        generate query_data to find similer location objects based on passed data
        """
        query_data = {}
        query_data["name"] = data.get("name", "")
        query_data["address1"] = data.get("address1", "")
        query_data["address2"] = data.get("address2", "")
        query_data["zip"] = data.get("zip", "")
        query_data["region"] = data.get("region", "")
        query_data["country"] = data.get("country", "")

        return query_data


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

    def get_query_data(self, data=None):
        """
        generate query_data to find similer bank objects based on passed data
        """
        query_data = {}
        query_data["name"] = data.get("name", "")
        query_data["length"] = data.get("length", "")
        query_data["width"] = data.get("width", "")
        query_data["depth"] = data.get("depth", "")
        query_data["length_unit"] = data.get("length_unit", "")
        query_data["cbm"] = data.get("cbm", "")
        query_data["weight"] = data.get("weight", "")

        return query_data


class HsCodeSerializer(ReversionSerializerMixin):
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


class CompanyContractSerializer(serializers.ModelSerializer):
    """Serializer for CompanyContract."""

    files = FileSerializer(many=True, required=False)

    class Meta:
        """Define field that we wanna show in the Json."""

        model = CompanyContract
        fields = (
            "id",
            "companytype",
            "title",
            "files",
            "note",
            "partner_member",
            "company_member",
            "paymentterms",
            "is_active",
            "status",
            "extra_data",
        )
        read_only_fields = (
            "id",
            "files",
            "is_active",
            "status",
            "company_member",
        )

    def validate(self, attrs):
        """
        validate that :
            the selected company type must relate to the current company.
        """
        company_id = self.context.get("company_id", None)
        companytype = attrs.get("companytype", None)
        paymentterms = attrs.get("paymentterms", None)
        errors = {}
        if companytype:
            if str(companytype.company.id) != str(company_id):
                errors = set_field_errors(
                    errors, "companytype", _("Invalid company type selected.")
                )
        if paymentterms:
            if str(paymentterms.company.id) != str(company_id):
                errors = set_field_errors(
                    errors,
                    "paymentterms",
                    _("Invalid payment terms selected."),
                )
        if errors:
            raise serializers.ValidationError(errors)

        attrs["company_member"] = get_member(
            company_id=self.context["company_id"], user_id=self.context["user"]
        )
        attrs["status"] = get_status("Basic", PRODUCT_STATUS_DRAFT)
        return super().validate(attrs)


class CompanyCredentialSerializer(serializers.ModelSerializer):
    """Serializer for Company Credential."""

    class Meta:
        """Define field that we wanna show in the Json."""

        model = CompanyCredential
        fields = (
            "id",
            "companytype",
            "region",
            "seller_id",
            "auth_token",
            "access_key",
            "secret_key",
            "is_active",
            "extra_data",
        )
        read_only_fields = ("id", "create_date", "update_date")

    def validate(self, attrs):
        """
        validate that :
            the selected company type must relate to the current company.
        """
        company_id = self.context.get("company_id", None)
        companytype = attrs.get("companytype", None)
        errors = {}
        if companytype:
            if str(companytype.company.id) != str(company_id):
                errors = set_field_errors(
                    errors, "companytype", _("Invalid company type selected.")
                )
        if errors:
            raise serializers.ValidationError(errors)

        return super().validate(attrs)


class ComponentMeSerializer(serializers.ModelSerializer):
    """Serializer for Component ME."""

    files = FileSerializer(many=True, required=False)

    class Meta:
        """Define field that we wanna show in the Json."""

        model = ComponentMe
        fields = (
            "id",
            "version",
            "revision_history",
            "component",
            "companytype",
            "files",
            "status",
            "is_active",
        )
        read_only_fields = (
            "id",
            "is_active",
            "files",
            "status",
            "create_date",
            "update_date",
        )

    def validate(self, attrs):
        """
        validate that :
            the selected company type must relate to the current company.
        """
        kwargs = self.context["request"].resolver_match.kwargs
        company_id = self.context.get("company_id", None)
        companytype = attrs.get("companytype", None)
        component = attrs.get("component", None)
        errors = {}
        if component:
            if str(component.get_company.id) != str(
                kwargs.get("company_pk", None)
            ):
                errors = set_field_errors(
                    errors, "component", _("Invalid component selected.")
                )
            if not component.productparent.is_component:
                errors = set_field_errors(
                    errors, "component", _("Selected component is a product.")
                )
        if companytype:
            if str(companytype.company.id) != str(company_id):
                errors = set_field_errors(
                    errors, "companytype", _("Invalid company type selected.")
                )
        if errors:
            raise serializers.ValidationError(errors)
        attrs["status"] = get_status("Basic", PRODUCT_STATUS_DRAFT)
        return super().validate(attrs)


class ComponentGoldenSampleSerializer(serializers.ModelSerializer):
    """Serializer for Component Golden Sample."""

    files = FileSerializer(many=True, required=False)

    class Meta:
        """Define field that we wanna show in the Json."""

        model = ComponentGoldenSample
        fields = (
            "id",
            "componentme",
            "batch_id",
            "files",
            "note",
            "status",
            "is_active",
        )
        read_only_fields = (
            "id",
            "is_active",
            "files",
            "status",
            "create_date",
            "update_date",
        )

    def validate(self, attrs):
        """
        validate that :
            company type of selected componentme must relate to the current company.
        """
        kwargs = self.context["request"].resolver_match.kwargs
        componentme = attrs.get("componentme", None)
        errors = {}
        if componentme:
            if str(componentme.companytype.company.id) != str(
                kwargs.get("company_pk", None)
            ):
                errors = set_field_errors(
                    errors, "componentme", _("Invalid Component ME.")
                )
        if errors:
            raise serializers.ValidationError(errors)
        attrs["status"] = get_status("Basic", PRODUCT_STATUS_DRAFT)
        return super().validate(attrs)


class ComponentPriceSerializer(serializers.ModelSerializer):
    """Serializer for Component Price."""

    price = MoneySerializerField()
    files = FileSerializer(many=True, required=False)

    class Meta:
        """Define field that we wanna show in the Json."""

        model = ComponentPrice
        fields = (
            "id",
            "componentgoldensample",
            "files",
            "price",
            "start_date",
            "end_date",
            "status",
            "is_active",
        )
        read_only_fields = (
            "id",
            "files",
            "is_active",
            "status",
            "create_date",
            "update_date",
        )

    def validate(self, attrs):
        """
        validate that :
            The selected component golden sample must be active and from the same company.
        """
        kwargs = self.context["request"].resolver_match.kwargs
        componentgoldensample = attrs.get("componentgoldensample", None)
        errors = {}
        if componentgoldensample:
            if str(
                componentgoldensample.componentme.companytype.company.id
            ) != str(kwargs.get("company_pk", None)):
                errors = set_field_errors(
                    errors,
                    "componentgoldensample",
                    _("Invalid Component Golden Sample."),
                )
        if errors:
            raise serializers.ValidationError(errors)
        attrs["status"] = get_status("Basic", PRODUCT_STATUS_DRAFT)
        return super().validate(attrs)


class CompanyProductSerializer(serializers.ModelSerializer):
    """Serializer for Company Product."""

    price = MoneySerializerField()
    status = StatusField(default=PRODUCT_STATUS_DRAFT)

    class Meta:
        """Define field that we wanna show in the Json."""

        model = CompanyProduct
        fields = (
            "id",
            "product",
            "companytype",
            "title",
            "sku",
            "ean",
            "asin",
            "model_number",
            "manufacturer_part_number",
            "price",
            "status",
            "is_active",
        )
        read_only_fields = (
            "id",
            "is_active",
            "status",
            "create_date",
            "update_date",
        )

    def validate(self, attrs):
        """
        validate that :
            the selected company type must relate to the current company.
        """
        kwargs = self.context["request"].resolver_match.kwargs
        company_id = self.context.get("company_id", None)
        companytype = attrs.get("companytype", None)
        product = attrs.get("product", None)
        errors = {}
        if product:
            if str(product.get_company.id) != str(
                kwargs.get("company_pk", None)
            ):
                errors = set_field_errors(
                    errors, "product", _("Invalid product selected.")
                )
            if product.productparent.is_component:
                errors = set_field_errors(
                    errors, "product", _("Selected product is a component.")
                )
        if companytype:
            if str(companytype.company.id) != str(company_id):
                errors = set_field_errors(
                    errors, "companytype", _("Invalid company type selected.")
                )
        if errors:
            raise serializers.ValidationError(errors)
        return super().validate(attrs)

    def create(self, validated_data):
        validated_data["status"] = get_status_object(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["status"] = get_status_object(validated_data)
        return super().update(instance, validated_data)


class CompanyOrderProductSerializer(serializers.ModelSerializer):
    """Serializer for Company Order Product."""
    price = MoneySerializerField(required=False)
    amount = MoneySerializerField(required=False)

    class Meta:
        """Define field that we wanna show in the Json."""

        model = CompanyOrderProduct
        fields = (
            "id",
            "companyorder",
            "companyproduct",
            "componentprice",
            "quantity",
            "shipped_quantity",
            "remaining_quantity",
            "companypaymentterms",
            "price",
            "amount",
            "is_active",
        )
        read_only_fields = (
            "id",
            "companyorder",
            "shipped_quantity",
            "remaining_quantity",
            "amount",
            "price",
            "is_active",
            "create_date",
            "update_date",
        )


class CompanyOrderSerializer(serializers.ModelSerializer):
    """Serializer for Company Order."""

    orderproducts = CompanyOrderProductSerializer(many=True, read_only=False)
    sub_amount = MoneySerializerField(default=0)
    vat_amount = MoneySerializerField(required=False)
    tax_amount = MoneySerializerField(required=False)
    total_amount = MoneySerializerField(default=0)
    return_amount = MoneySerializerField(required=False)
    deposit_amount = MoneySerializerField(default=0)
    files = FileSerializer(many=True, required=False)
    status = StatusField(default=PRODUCT_STATUS_DRAFT)

    class Meta:
        """Define field that we wanna show in the Json."""

        model = CompanyOrder
        fields = (
            "id",
            "batch_id",
            "companytype",
            "order_date",
            "delivery_date",
            "buyer_member",
            "seller_member",
            "sub_amount",
            "vat_amount",
            "tax_amount",
            "total_amount",
            "return_amount",
            "deposit_amount",
            "quantity",
            "note",
            "files",
            "status",
            "orderproducts",
        )
        read_only_fields = (
            "id",
            "status",
            "sub_amount",
            "vat_amount",
            "tax_amount",
            "total_amount",
            "return_amount",
            "deposit_amount",
            "quantity",
            "files",
            "create_date",
            "update_date",
        )

    def validate(self, attrs):
        """
        validate that :
            the selected company type must relate to the current company.
        """
        member = get_member(
            company_id=self.context.get("company_id", None),
            user_id=self.context.get("user_id", None),
        )
        company_id = self.context.get("company_id", None)
        companytype = attrs.get("companytype", None)
        orderproducts = attrs.get("orderproducts", [])
        errors = {}
        if companytype:
            if str(companytype.company.id) != str(company_id):
                errors = set_field_errors(
                    errors, "companytype", _("Invalid company type selected.")
                )
        if len(orderproducts) <= 0:
            msg = _("At Least one product required to place an order.")
            raise serializers.ValidationError({"orderproducts": msg})
        if errors:
            raise serializers.ValidationError(errors)

        attrs["vat_amount"] = attrs.get(
            'vat_amount', Money(0, member.company.currency))
        attrs["tax_amount"] = attrs.get(
            'tax_amount', Money(0, member.company.currency))
        attrs["return_amount"] = attrs.get(
            'return_amount', Money(0, member.company.currency))

        return super().validate(attrs)

    def create(self, validated_data):
        """Create function."""
        member = get_member(
            company_id=self.context.get("company_id", None),
            user_id=self.context.get("user_id", None),
        )
        with transaction.atomic():
            data = validated_data.copy()
            data['status'] = get_status_object(validated_data)
            orderproducts = data.get("orderproducts", None)
            data.pop("orderproducts")
            # save order
            companyorder = CompanyOrder.objects.create(**data)

            # save order products
            quantity = companyorder.quantity or 0
            total_amount = 0
            deposit_amount = 0
            currency = member.company.currency
            for orderproduct in orderproducts or []:
                componentprice_obj = orderproduct.get(
                    "componentprice", None
                )
                currency = componentprice_obj.price.currency
                product_quantity = orderproduct.get("quantity", 0)
                quantity += product_quantity
                amount = Decimal(
                    componentprice_obj.price.amount
                ) * Decimal(product_quantity)

                if orderproduct.get("companypaymentterms", None).deposit:
                    product_deposit_amount = (
                        Decimal(
                            orderproduct.get(
                                "companypaymentterms", None
                            ).deposit
                        )
                        * Decimal(amount)
                    ) / Decimal(100)
                else:
                    product_deposit_amount = 0
                deposit_amount += product_deposit_amount
                total_amount += amount
                orderproduct.pop("price", None)
                orderproduct.pop("amount", None)
                CompanyOrderProduct.objects.create(
                    companyorder=companyorder,
                    price=Money(componentprice_obj.price.amount, currency),
                    amount=Money(amount, currency),
                    remaining_quantity=product_quantity,
                    **orderproduct
                )
            companyorder.sub_amount = Money(total_amount, currency)
            companyorder.total_amount = Money(total_amount, currency)
            companyorder.deposit_amount = Money(deposit_amount, currency)
            companyorder.quantity = quantity
            companyorder.save()
            companyorder.save_pdf_file()
        return companyorder


class CompanyOrderDeliveryProductSerializer(serializers.ModelSerializer):
    """Serializer for Company Order Delivery Product."""

    amount = MoneySerializerField(required=False)

    class Meta:
        """Define field that we wanna show in the Json."""

        model = CompanyOrderDeliveryProduct
        fields = (
            "id",
            "companyorderdelivery",
            "companyorderproduct",
            "quantity",
            "amount",
        )
        read_only_fields = (
            "id",
            "companyorderdelivery",
            "amount",
            "create_date",
            "update_date",
        )


class CompanyOrderDeliverySerializer(serializers.ModelSerializer):
    """Serializer for Company Order Delivery."""

    orderdeliveryproducts = CompanyOrderDeliveryProductSerializer(
        many=True, read_only=False
    )
    amount = MoneySerializerField(default=0)
    quantity = serializers.IntegerField(default=0)
    status = StatusField(default=PRODUCT_STATUS_DRAFT)

    class Meta:
        """Define field that we wanna show in the Json."""

        model = CompanyOrderDelivery
        fields = (
            "id",
            "batch_id",
            "companyorder",
            "quantity",
            "amount",
            "delivery_date",
            "status",
            "extra_data",
            "orderdeliveryproducts",
        )
        read_only_fields = (
            "id",
            "amount",
            "status",
            "create_date",
            "update_date",
        )

    def validate(self, attrs):
        """
        validate that :
            the selected company type must relate to the current company.
        """

        company_id = self.context.get("company_id", None)
        companyorder = attrs.get("companyorder", None)
        orderdeliveryproducts = attrs.get("orderdeliveryproducts", [])
        errors = {}
        if companyorder:
            if str(companyorder.companytype.company.id) != str(company_id):
                errors = set_field_errors(
                    errors, "companyorder", _("Invalid order selected.")
                )
            bank = companyorder.companytype.partner.banks.filter(
                is_active=True)
            if not bank.exists():
                errors = set_field_errors(
                    errors, "companyorder", _(
                        "There is no bank registered for selected order.")
                )
        if len(orderdeliveryproducts) <= 0:
            msg = _(
                "At Least one product required to create an order delivery."
            )
            raise serializers.ValidationError({"orderdeliveryproducts": msg})

        if errors:
            raise serializers.ValidationError(errors)
        return super().validate(attrs)

    def create(self, validated_data):
        """Create function."""
        member = get_member(
            company_id=self.context.get("company_id", None),
            user_id=self.context.get("user_id", None),
        )
        with transaction.atomic():
            data = validated_data.copy()
            data['status'] = get_status_object(validated_data)
            orderdeliveryproducts = data.get("orderdeliveryproducts", None)
            data.pop("orderdeliveryproducts")

            # save order
            companyorderdelivery = CompanyOrderDelivery.objects.create(**data)

            # save order products
            quantity = companyorderdelivery.quantity or 0
            total_amount = 0
            currency = member.company.currency
            for orderdeliveryproduct in orderdeliveryproducts or []:
                orderproduct = orderdeliveryproduct.get(
                    "companyorderproduct", None
                )
                currency = orderproduct.price.currency
                orderproduct_quantity = orderdeliveryproduct.pop("quantity", 0)
                quantity += orderproduct_quantity
                remaining_quantity = (
                    orderproduct.remaining_quantity - orderproduct_quantity)
                if remaining_quantity < 0:
                    remaining_quantity = 0
                orderproduct.remaining_quantity = remaining_quantity
                shipped_quantity = (
                    orderproduct.shipped_quantity + orderproduct_quantity)
                if shipped_quantity < 0:
                    shipped_quantity = 0
                orderproduct.shipped_quantity = shipped_quantity
                orderproduct.save()
                amount = Decimal(orderproduct.price.amount) * Decimal(
                    orderproduct_quantity
                )

                total_amount += amount
                CompanyOrderDeliveryProduct.objects.create(
                    companyorderdelivery=companyorderdelivery,
                    amount=Money(amount, currency),
                    quantity=orderproduct_quantity,
                    **orderdeliveryproduct
                )
            companyorderdelivery.amount = Money(total_amount, currency)
            companyorderdelivery.quantity = quantity
            companyorderdelivery.save()
            # create company order payment object
            company_order_payment_data = {}
            company_order_payment_data['companyorderdelivery'] = companyorderdelivery
            company_order_payment_data['type'] = "type"
            # TODO how to get bank for company_order_payment_data

            companyorder = validated_data.get("companyorder", None)
            company_order_payment_data['bank'] = companyorder.companytype.partner.banks.filter(
                is_active=True).first()
            company_order_payment_data['invoice_amount'] = companyorderdelivery.amount
            company_order_payment_data['amount'] = companyorderdelivery.amount
            company_order_payment_data['paid_amount'] = 0
            company_order_payment_data['payment_date'] = companyorderdelivery.delivery_date
            company_order_payment_data['status'] = companyorderdelivery.status
            CompanyOrderPayment.objects.create(**company_order_payment_data)
        return companyorderdelivery


class CompanyOrderCaseSerializers(serializers.ModelSerializer):

    files = FileSerializer(many=True, required=False)
    status = StatusField(default=PRODUCT_STATUS_DRAFT)

    class Meta:
        model = CompanyOrderCase
        fields = ("id", "companyorder", "files", "note", "importance",
                  "units_affected", "status", "extra_data")
        read_only_fields = (
            "id",
            "files",
            "extra_data",
            "create_date",
            "update_date",
        )

    def validate(self, attrs):
        """
        validate that :
            company type of selected Company Order Case must relate to the current company.
        """
        company_id = self.context.get("company_id", None)
        companyorder = attrs.get("companyorder", None)
        errors = {}
        if companyorder:
            if str(companyorder.get_company().id) != str(company_id):
                errors = set_field_errors(
                    errors, "companyorder", _(
                        "Invalid Company order selected.")
                )
        if errors:
            raise serializers.ValidationError(errors)
        if not attrs.get("status", None):
            attrs["status"] = get_status("Basic", PRODUCT_STATUS_DRAFT)
        return super().validate(attrs)

    def create(self, validated_data):
        validated_data["status"] = get_status_object(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["status"] = get_status_object(validated_data)
        return super().update(instance, validated_data)


class CompanyOrderInspectionSerializer(serializers.ModelSerializer):

    files = FileSerializer(many=True, required=False)
    status = StatusField(default=PRODUCT_STATUS_DRAFT)

    class Meta:
        model = CompanyOrderInspection
        fields = ("id", "companyorder", "inspection_date", "note", "inspector",
                  "files", "status", "extra_data")
        read_only_fields = (
            "id",
            "inspector",
            "files",
            "extra_data",
            "create_date",
            "update_date",
        )

    def validate(self, attrs):
        """
        validate that :
            company type of selected Company Order must relate to the current company.
        """
        company_id = self.context.get("company_id", None)
        companyorder = attrs.get("companyorder", None)
        errors = {}
        if companyorder:
            if str(companyorder.get_company().id) != str(company_id):
                errors = set_field_errors(
                    errors, "companyorder", _(
                        "Invalid Company order selected.")
                )
        if errors:
            raise serializers.ValidationError(errors)
        return super().validate(attrs)

    def create(self, validated_data):
        member = get_member(
            company_id=self.context.get("company_id", None),
            user_id=self.context.get("user_id", None),
        )
        validated_data["inspector"] = member
        validated_data["status"] = get_status_object(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["status"] = get_status_object(validated_data)
        return super().update(instance, validated_data)


class CompanyOrderDeliveryTestReportSerializer(serializers.ModelSerializer):
    files = FileSerializer(many=True, required=False)
    status = StatusField(default=PRODUCT_STATUS_DRAFT)

    class Meta:
        model = CompanyOrderDeliveryTestReport
        fields = ("id", "companyorderdelivery", "inspector",
                  "files", "note", "status", "extra_data")

        read_only_fields = (
            "id",
            "inspector",
            "files",
            "extra_data",
            "create_date",
            "update_date",
        )

    def validate(self, attrs):
        """
        validate that :
            company type of selected companyorderdelivery must relate to the current company.
        """
        company_id = self.context.get("company_id", None)
        companyorderdelivery = attrs.get("companyorderdelivery", None)
        errors = {}
        if companyorderdelivery:
            if str(companyorderdelivery.get_company().id) != str(company_id):
                errors = set_field_errors(
                    errors, "companyorderdelivery", _(
                        "Invalid company order delivery selected.")
                )
        if errors:
            raise serializers.ValidationError(errors)
        return super().validate(attrs)

    def create(self, validated_data):
        member = get_member(
            company_id=self.context.get("company_id", None),
            user_id=self.context.get("user_id", None),
        )
        validated_data["inspector"] = member
        validated_data["status"] = get_status_object(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["status"] = get_status_object(validated_data)
        return super().update(instance, validated_data)


class CompanyOrderPaymentPaidSerializer(serializers.ModelSerializer):
    files = FileSerializer(many=True, required=False)
    status = StatusField(default=PRODUCT_STATUS_DRAFT)
    invoice_amount = MoneySerializerField()
    paid_amount = MoneySerializerField()

    class Meta:
        model = CompanyOrderPaymentPaid
        fields = ("id", "companyorderpayment", "payment_id", "invoice_amount", "paid_amount",
                  "files", "payment_date", "status", "extra_data")

        read_only_fields = (
            "id",
            "files",
            "extra_data",
            "create_date",
            "update_date",
        )

    def validate(self, attrs):
        """
        validate that :
            company type of selected company order payment must relate to the current company.
        """
        company_id = self.context.get("company_id", None)
        companyorderpayment = attrs.get("companyorderpayment", None)
        errors = {}
        if companyorderpayment:
            if str(companyorderpayment.get_company().id) != str(company_id):
                errors = set_field_errors(
                    errors, "companyorderpayment", _(
                        "Invalid company company order payment selected.")
                )
        invoice_amount = attrs.get("invoice_amount", None)
        paid_amount = attrs.get("paid_amount", None)
        if invoice_amount and paid_amount:
            if invoice_amount.amount < paid_amount.amount:
                errors = set_field_errors(
                    errors, "paid_amount", _(
                        "paid amount can't be more than invoice amount.")
                )
            total_paid_amount = companyorderpayment.orderpaymentpaid.aggregate(
                total_paid_amount=Sum("paid_amount"))["total_paid_amount"] + paid_amount.amount
            if total_paid_amount > invoice_amount.amount:
                errors = set_field_errors(
                    errors, "paid_amount", _(
                        "total paid amount can't be more than invoice amount.")
                )
        if errors:
            raise serializers.ValidationError(errors)
        return super().validate(attrs)

    def create(self, validated_data):
        validated_data["status"] = get_status_object(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["status"] = get_status_object(validated_data)
        return super().update(instance, validated_data)


class CompanyOrderPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyOrderPayment
        fields = ("id", "companyorderdelivery", "type", "bank", "invoice_amount", "amount", "paid_amount",
                  "adjustment_type", "adjustment_percentage", "adjustment_amount", "payment_date", "status")

        read_only_fields = (
            "id",
            "files",
            "extra_data",
            "create_date",
            "update_date",
        )

class CompanyTypeSerializerField(serializers.Field):
    def to_representation(self, value):
        return { "category": value.first().category_id if value.first() else None}

    def to_internal_value(self, data):
        category = data.get('category')
        if not Category.objects.vendor_categories().filter(pk=category).exists():
            raise serializers.ValidationError(
                    {"company_type": _("Category is not valid")}
                )
        return Category.objects.filter(pk=category).first()


class VendorCompanySerializer(serializers.ModelSerializer):
    country = CountrySerializerField()
    company_type = CompanyTypeSerializerField(source='companytype_company')

    def create(self, validated_data):
        data = validated_data.copy()
        company_type = data.pop('companytype_company', None)

        vendor = super().create(data)

        request = self.context.get('request')

        company_id = self.context.get('company_id')

        companytype = CompanyType(
            partner=vendor,
            company_id=company_id,
            category=company_type,
        )
        companytype.save()

        extra_data = {}
        extra_data["user_role"] = "vendor_admin"
        member, create = Member.objects.get_or_create(
            job_title="Admin",
            user=request.user,
            company=vendor,
            invited_by=request.user,
            is_admin=True,
            is_active=True,
            invitation_accepted=True,
            extra_data=extra_data,
        )
        
        if create:
            # fetch user role from the User and assign after signup.
            assign_role(member, member.extra_data["user_role"])

        return vendor


    class Meta:
        model = Company
        fields = (
            "id", "address1",  "address2", "zip", "city", "region", "country",
            "name", "abbreviation", "email", "logo", "phone_number", "organization_number",
            "currency", "unit_system", "weight_unit", "language", "time_zone",
            "is_active", "extra_data", 'company_type', )
        read_only_fields = ("id", "is_active", "extra_data")

