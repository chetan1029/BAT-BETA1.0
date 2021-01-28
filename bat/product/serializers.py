from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from djmoney.contrib.django_rest_framework import MoneyField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from bat.company.models import HsCode, PackingBox
from bat.company.serializers import PackingBoxSerializer
from bat.company.utils import get_member
from bat.globalutils.utils import get_status_object, set_field_errors
from bat.product.constants import PRODUCT_STATUS_DRAFT
from bat.product.models import (
    Image,
    Product,
    ProductComponent,
    ProductOption,
    ProductPackingBox,
    ProductParent,
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
        fields = ("id", "productparent", "name", "value")
        read_only_fields = ("id", "productparent")


class ProductVariationOptionSerializer(serializers.ModelSerializer):

    productoption = ProductOptionSerializer(read_only=False)

    class Meta:
        model = ProductVariationOption
        fields = ("id", "productoption")
        read_only_fields = ("id",)


class ProductVariationSerializer(serializers.ModelSerializer):
    weight = WeightField(required=False)
    product_variation_options = ProductVariationOptionSerializer(
        many=True, read_only=False, required=False
    )
    images = ImageSerializer(many=True, read_only=True, required=False)
    tags = TagField(required=False)

    class Meta:
        model = Product
        fields = (
            "id",
            "productparent",
            "title",
            "sku",
            "ean",
            "model_number",
            "manufacturer_part_number",
            "length",
            "tags",
            "width",
            "type",
            "depth",
            "length_unit",
            "weight",
            "is_active",
            "extra_data",
            "product_variation_options",
            "images",
        )
        read_only_fields = (
            "id",
            "is_active",
            "extra_data",
            "productparent",
            "images",
        )


class UpdateProductVariationSerializer(serializers.ModelSerializer):
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
            "productparent",
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
            "length_unit",
            "weight",
            "is_active",
            "extra_data",
            "product_variation_options",
            "images",
        )
        read_only_fields = (
            "id",
            "productparent",
            "is_active",
            "extra_data",
            "model_number",
            "manufacturer_part_number",
            "product_variation_options" "images",
        )

    def update(self, instance, validated_data):
        data = validated_data.copy()
        tags = data.pop("tags", None)
        instance = super().update(instance, data)
        if tags:
            # set tags
            instance.tags.set(*tags)
        return instance


class ProductSerializer(serializers.ModelSerializer):
    """
    ModelSerializer to create component
    """

    tags = TagField(required=False)
    status = StatusField(default=PRODUCT_STATUS_DRAFT)
    products = ProductVariationSerializer(many=True, read_only=False)
    images = ImageSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = ProductParent
        fields = (
            "id",
            "company",
            "is_component",
            "title",
            "type",
            "series",
            "hscode",
            "sku",
            "model_number",
            "bullet_points",
            "description",
            "tags",
            "is_active",
            "status",
            "extra_data",
            "products",
            "images",
        )
        read_only_fields = (
            "id",
            "is_active",
            "extra_data",
            "company",
            "images",
        )

    def validate(self, attrs):
        products = attrs.get("products", [])
        if len(products) < 1:
            msg = _("At Least one child product required.")
            raise serializers.ValidationError({"products": msg})
        return super().validate(attrs)

    def create(self, validated_data):
        """
        save product parent with all children products and related objects.
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
                hscode, _c = HsCode.objects.get_or_create(
                    hscode=hscode, company=member.company
                )
            data.pop("images", None)
            tags = data.get("tags", None)
            data.pop("tags", None)
            products = data.get("products", None)
            data.pop("products")
            product_parent = ProductParent.objects.create(
                company=member.company, **data
            )
            if tags:
                # set tags
                product_parent.tags.set(*tags)
            # save variations
            for product in products or []:
                product_variation_options = product.get(
                    "product_variation_options", None
                )
                product.pop("product_variation_options", None)

                tags = product.pop("tags", None)

                new_product = Product.objects.create(
                    productparent=product_parent, **product
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
                            name=name,
                            value=value,
                            productparent=product_parent,
                        )
                        ProductVariationOption.objects.create(
                            product=new_product, productoption=productoption
                        )
        return product_parent


class ProductComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductComponent
        fields = (
            "id",
            "product",
            "component",
            "quantity",
            "value",
            "is_active",
        )
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
            if str(product.productparent.id) != str(
                kwargs.get("product_pk", None)
            ):
                errors = set_field_errors(
                    errors,
                    "product",
                    _(
                        "Selected product variation is not from current Product."
                    ),
                )
            if product.productparent.is_component:
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
            if not component.productparent.is_component:
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
            if str(product.productparent.id) != str(
                kwargs.get("product_pk", None)
            ):
                errors = set_field_errors(
                    errors,
                    "product",
                    _(
                        "Selected product variation is not from current Product."
                    ),
                )
            if product.productparent.is_component:
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
            if str(product.productparent.id) != str(
                kwargs.get("product_pk", None)
            ):
                errors = set_field_errors(
                    errors,
                    "product",
                    _(
                        "Selected product variation is not from current Product."
                    ),
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
