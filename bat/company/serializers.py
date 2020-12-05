from decimal import Decimal

from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from djmoney.contrib.django_rest_framework import MoneyField
from djmoney.settings import CURRENCY_CHOICES
from invitations.utils import get_invitation_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rolepermissions.roles import get_user_roles


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
)
from bat.company.utils import get_list_of_permissions, get_list_of_roles, get_member
from bat.globalutils.utils import get_cbm, set_field_errors
from bat.product.constants import PRODUCT_STATUS_DRAFT
from bat.serializersFields.serializers_fields import (
    CountrySerializerField,
    MoneySerializerField,
    QueryFieldsMixin,
    WeightField,
)
from bat.setting.models import Category
from bat.setting.utils import get_status
from bat.users.serializers import UserLoginActivitySerializer, UserSerializer

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

    class Meta:
        """Define field that we wanna show in the Json."""

        model = ComponentPrice
        fields = (
            "id",
            "componentgoldensample",
            "price",
            "start_date",
            "end_date",
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
        attrs["status"] = get_status("Basic", PRODUCT_STATUS_DRAFT)
        return super().validate(attrs)


class CompanyOrderProductSerializer(serializers.ModelSerializer):
    """Serializer for Company Order Product."""

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
    vat_amount = MoneySerializerField(default=0)
    tax_amount = MoneySerializerField(default=0)
    total_amount = MoneySerializerField(default=0)
    return_amount = MoneySerializerField(default=0)
    deposit_amount = MoneySerializerField(default=0)
    files = FileSerializer(many=True, required=False)

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
        attrs["status"] = get_status("Basic", PRODUCT_STATUS_DRAFT)
        return super().validate(attrs)

    def create(self, validated_data):
        """Create function."""
        with transaction.atomic():
            data = validated_data.copy()
            orderproducts = data.get("orderproducts", None)
            data.pop("orderproducts")

            # save order
            companyorder = CompanyOrder.objects.create(**data)

            # save order products
            quantity = companyorder.quantity or 0
            total_amount = 0
            deposit_amount = 0
            for orderproduct in orderproducts or []:
                product_quantity = orderproduct.get("quantity", 0)
                quantity += product_quantity
                amount = Decimal(
                    orderproduct.get("componentprice", None).price.amount
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
                CompanyOrderProduct.objects.create(
                    companyorder=companyorder,
                    price=orderproduct.get(
                        "componentprice", None
                    ).price.amount,
                    amount=amount,
                    remaining_quantity=product_quantity,
                    **orderproduct
                )
            companyorder.sub_amount = total_amount
            companyorder.total_amount = total_amount
            companyorder.deposit_amount = deposit_amount
            companyorder.quantity = quantity
            companyorder.save()
            companyorder.save_pdf_file()
        return companyorder


class CompanyOrderDeliveryProductSerializer(serializers.ModelSerializer):
    """Serializer for Company Order Delivery Product."""

    amount = MoneySerializerField(default=0)

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
        if len(orderdeliveryproducts) <= 0:
            msg = _(
                "At Least one product required to create an order delivery."
            )
            raise serializers.ValidationError({"orderdeliveryproducts": msg})
        if errors:
            raise serializers.ValidationError(errors)
        attrs["status"] = get_status("Basic", PRODUCT_STATUS_DRAFT)
        return super().validate(attrs)

    def create(self, validated_data):
        """Create function."""
        with transaction.atomic():
            data = validated_data.copy()
            orderdeliveryproducts = data.get("orderdeliveryproducts", None)
            data.pop("orderdeliveryproducts")

            # save order
            companyorderdelivery = CompanyOrderDelivery.objects.create(**data)

            # save order products
            quantity = companyorderdelivery.quantity or 0
            total_amount = 0
            for orderdeliveryproduct in orderdeliveryproducts or []:
                orderproduct = orderdeliveryproduct.get(
                    "companyorderproduct", None
                )
                orderproduct_quantity = orderdeliveryproduct.get("quantity", 0)
                quantity += orderproduct_quantity
                orderproduct.remaining_quantity = (
                    orderproduct.remaining_quantity - orderproduct_quantity
                )
                orderproduct.shipped_quantity = (
                    orderproduct.shipped_quantity + orderproduct_quantity
                )
                orderproduct.save()
                amount = Decimal(orderproduct.price) * Decimal(
                    orderproduct_quantity
                )

                total_amount += amount
                CompanyOrderDeliveryProduct.objects.create(
                    companyorderdelivery=companyorderdelivery,
                    amount=amount,
                    quantity=orderproduct_quantity,
                    **orderdeliveryproduct
                )
            companyorderdelivery.amount = total_amount
            companyorderdelivery.quantity = quantity
            companyorderdelivery.save()
        return companyorderdelivery
