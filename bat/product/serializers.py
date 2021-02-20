from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from djmoney.contrib.django_rest_framework import MoneyField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from bat.company.file_serializers import FileSerializer
from bat.company.models import HsCode, PackingBox
from bat.company.serializers import PackingBoxSerializer
from bat.company.utils import get_member
from bat.globalutils.utils import get_status_object, set_field_errors
from bat.product.constants import PRODUCT_STATUS_DRAFT
from bat.product.models import (
    ComponentMe,
    Image,
    Product,
    ProductComponent,
    ProductOption,
    ProductPackingBox,
    ProductRrp,
    ProductVariationOption,
)
from bat.serializersFields.serializers_fields import (
    CountrySerializerField,
    MoneySerializerField,
    StatusField,
    TagField,
    WeightField,
)
from bat.setting.utils import get_status


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = (
            "id",
            "image",
            "content_type",
            "object_id",
            "main_image",
            "is_active",
            "company",
        )
        read_only_fields = (
            "id",
            "content_type",
            "object_id",
            "is_active",
            "company",
        )


class ProductOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductOption
        fields = ("id", "company", "name", "value")
        read_only_fields = ("id", "company")


class ProductVariationOptionSerializer(serializers.ModelSerializer):

    productoption = ProductOptionSerializer(read_only=False)

    class Meta:
        model = ProductVariationOption
        fields = ("id", "productoption")
        read_only_fields = ("id",)


class SingleProductSerializer(serializers.ModelSerializer):
    weight = WeightField(required=False)
    product_variation_options = ProductVariationOptionSerializer(
        many=True, read_only=False, required=False
    )
    status = StatusField(default=PRODUCT_STATUS_DRAFT)
    images = ImageSerializer(many=True, read_only=True, required=False)
    tags = TagField(required=False)

    class Meta:
        model = Product
        fields = (
            "id",
            "title",
            "sku",
            "ean",
            "model_number",
            "manufacturer_part_number",
            "length",
            "width",
            "depth",
            "length_unit",
            "tags",
            "type",
            "series",
            "hscode",
            "weight",
            "bullet_points",
            "description",
            "extra_data",
            "status",
            "product_variation_options",
            "images",
            "parent",
            "create_date",
            "update_date",
        )
        read_only_fields = (
            "id",
            "extra_data",
            "images",
            "parent",
            "status",
            "create_date",
            "update_date",
        )


class ProductSerializer(serializers.ModelSerializer):

    status = StatusField(default=PRODUCT_STATUS_DRAFT)
    images = ImageSerializer(many=True, read_only=True, required=False)
    tags = TagField(required=False)
    weight = WeightField(required=False)
    products = SingleProductSerializer(many=True, read_only=False)

    class Meta:
        model = Product
        fields = (
            "id",
            "is_component",
            "title",
            "tags",
            "type",
            "series",
            "hscode",
            "bullet_points",
            "description",
            "extra_data",
            "sku",
            "ean",
            "model_number",
            "manufacturer_part_number",
            "length",
            "width",
            "depth",
            "length_unit",
            "status",
            "images",
            "parent",
            "products",
            "weight",
            "create_date",
            "update_date",
        )
        read_only_fields = (
            "id",
            "extra_data",
            "images",
            "parent",
            "weight",
            "sku",
            "ean",
            "model_number",
            "manufacturer_part_number",
            "length",
            "width",
            "depth",
            "length_unit",
            "create_date",
            "update_date",
        )

    def create(self, validated_data):
        """
        save product from the variations.
        """
        member = get_member(
            company_id=self.context.get("company_id", None),
            user_id=self.context.get("user_id", None),
        )
        data = validated_data.copy()
        data["status"] = get_status_object(validated_data)
        data["model_number"] = get_random_string(length=10).upper()
        with transaction.atomic():
            hscode = data.get("hscode", None)
            if hscode:
                hscode_d, _c = HsCode.objects.get_or_create(
                    hscode=hscode, company=member.company
                )
            data.pop("images", None)
            tags = data.get("tags", None)
            data.pop("tags", None)
            is_component = data.get("is_component", None)
            description = data.get("description", None)
            products = data.get("products", None)
            data.pop("products")

            # save variations
            for product in products or []:
                product_variation_options = product.get(
                    "product_variation_options", None
                )
                product.pop("product_variation_options", None)

                tags = product.pop("tags", None)

                product["status"] = data["status"]
                product["is_component"] = is_component
                product["description"] = description
                if hscode:
                    product["hscode"] = hscode


                new_product = Product.objects.create(
                    company=member.company, **product
                )

                if tags:
                    # set tags
                    new_product.tags.set(*tags)
                # save options
                for variation_option in product_variation_options or []:
                    name = variation_option.get("productoption", None).get(
                        "name", None
                    )
                    value = variation_option.get("productoption", None).get(
                        "value", None
                    )
                    if name and value:
                        productoption, _c = ProductOption.objects.get_or_create(
                            name=name, value=value, company=member.company
                        )
                        ProductVariationOption.objects.create(
                            product=new_product, productoption=productoption
                        )
        return new_product


class UpdateProductSerializer(serializers.ModelSerializer):
    weight = WeightField(required=False)
    product_variation_options = ProductVariationOptionSerializer(
        many=True, read_only=True, required=False
    )
    images = ImageSerializer(many=True, read_only=True, required=False)
    tags = TagField(required=False)

    class Meta:
        model = Product
        fields = (
            "id",
            "title",
            "sku",
            "ean",
            "model_number",
            "manufacturer_part_number",
            "length",
            "width",
            "depth",
            "tags",
            "type",
            "series",
            "hscode",
            "length_unit",
            "weight",
            "bullet_points",
            "description",
            "status",
            "extra_data",
            "product_variation_options",
            "images",
            "parent",
        )
        read_only_fields = (
            "id",
            "extra_data",
            "model_number",
            "manufacturer_part_number",
            "product_variation_options",
            "images",
            "parent",
        )

    def update(self, instance, validated_data):
        data = validated_data.copy()
        tags = data.pop("tags", None)
        instance = super().update(instance, data)
        if tags:
            # set tags
            instance.tags.set(*tags)
        return instance


class ProductComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductComponent
        fields = ("id", "product", "component", "quantity", "is_active")
        read_only_fields = ("id", "is_active")

    def validate(self, attrs):
        """
        validate that :
            the selected product and component must relate to the current company.
            product must not be marked as a component.
            component must be marked as a component.
        """
        kwargs = self.context["request"].resolver_match.kwargs
        product = attrs.get("product", None)
        component = attrs.get("component", None)
        errors = {}
        if product:
            if str(product.get_company.id) != str(
                kwargs.get("company_pk", None)
            ):
                errors = set_field_errors(
                    errors, "product", _("Invalid product selected.")
                )
            if product.is_component:
                errors = set_field_errors(
                    errors, "product", _("Selected product is a component.")
                )
        if component:
            if str(component.get_company.id) != str(
                kwargs.get("company_pk", None)
            ):
                errors = set_field_errors(
                    errors, "component", _("Invalid component selected.")
                )
            if not component.is_component:
                errors = set_field_errors(
                    errors, "component", _("Selected component is a product.")
                )
        if errors:
            raise serializers.ValidationError(errors)
        return super().validate(attrs)


class ProductRrpSerializer(serializers.ModelSerializer):
    country = CountrySerializerField()
    rrp = MoneySerializerField()

    class Meta:
        model = ProductRrp
        fields = ("id", "product", "rrp", "country", "is_active")
        read_only_fields = ("id", "is_active")

    def validate(self, attrs):
        """
        validate that :
            the selected product must relate to the current company.
            product must not be marked as a component.
        """
        kwargs = self.context["request"].resolver_match.kwargs
        product = attrs.get("product", None)
        errors = {}
        if product:
            if str(product.get_company.id) != str(
                kwargs.get("company_pk", None)
            ):
                errors = set_field_errors(
                    errors, "product", _("Invalid product selected.")
                )
            if product.is_component:
                errors = set_field_errors(
                    errors, "product", _("Selected product is a component.")
                )
        if errors:
            raise serializers.ValidationError(errors)
        return super().validate(attrs)


class PackingBoxSerializerField(serializers.Field):
    def to_representation(self, value):
        """
        give json of PackingBox .
        """
        if isinstance(value, PackingBox):
            return PackingBoxSerializer(value).data
        return value

    def to_internal_value(self, data):
        try:
            obj = PackingBox.objects.get(pk=data)
            return obj
        except ObjectDoesNotExist:
            raise ValidationError(
                {"current_location": _(f"{data} is not a valid location.")}
            )


class ProductPackingBoxSerializer(serializers.ModelSerializer):
    weight = WeightField()
    packingbox = PackingBoxSerializerField()

    class Meta:
        model = ProductPackingBox
        fields = (
            "id",
            "product",
            "packingbox",
            "weight",
            "units",
            "is_active",
        )
        read_only_fields = ("id", "is_active")

    def validate(self, attrs):
        """
        validate that :
            the selected product and packingbox must relate to the current company.
            product must not be marked as a component.
        """
        kwargs = self.context["request"].resolver_match.kwargs
        product = attrs.get("product", None)
        packingbox = attrs.get("packingbox", None)
        errors = {}
        if product:
            if str(product.get_company.id) != str(
                kwargs.get("company_pk", None)
            ):
                errors = set_field_errors(
                    errors, "product", _("Invalid product selected.")
                )
        if packingbox:
            if str(packingbox.company.id) != str(
                kwargs.get("company_pk", None)
            ):
                errors = set_field_errors(
                    errors, "packingbox", _("Invalid packingbox selected.")
                )
        if errors:
            raise serializers.ValidationError(errors)
        return super().validate(attrs)


class ComponentMeSerializer(serializers.ModelSerializer):
    """Serializer for Component ME."""

    files = FileSerializer(many=True, required=False)
    status = StatusField(default=PRODUCT_STATUS_DRAFT)

    class Meta:
        """Define field that we wanna show in the Json."""

        model = ComponentMe
        fields = (
            "id",
            "version",
            "revision_history",
            "component",
            "files",
            "status",
            "is_active",
            "create_date",
            "update_date",
        )
        read_only_fields = (
            "id",
            "is_active",
            "files",
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
        component = attrs.get("component", None)
        errors = {}
        if component:
            if str(component.get_company.id) != str(
                kwargs.get("company_pk", None)
            ):
                errors = set_field_errors(
                    errors, "component", _("Invalid component selected.")
                )
            if not component.is_component:
                errors = set_field_errors(
                    errors, "component", _("Selected component is a product.")
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

class IdListSerializer(serializers.Serializer):
    ids = serializers.ListField(required=True)

    def validate(self, attrs):
        data = super().validate(attrs)
        ids = list(filter(None, data.get("ids")))
        if not ids:
            raise ValidationError({"ids" : "Id list should not empty."})
        data = data.copy()
        data["ids"] = ids
        return data

class UpdateStatusSerializer(IdListSerializer):
    status = StatusField(required=True)