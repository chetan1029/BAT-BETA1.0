from itertools import groupby

from rest_framework import serializers

from django.utils.translation import ugettext_lazy as _

from djmoney.contrib.django_rest_framework import MoneyField

from bat.product.models import (
    ProductParent,
    Product,
    ProductOption,
    ProductVariationOption,
    Image,
    ProductComponent,
    ProductRrp,
    ProductPackingBox)
from bat.serializersFields.serializers_fields import WeightField
from bat.setting.serializers import StatusSerializer
from bat.company.serializers import PackingBoxSerializer
from bat.serializersFields.serializers_fields import CountrySerializerField
from bat.globalutils.utils import set_field_errors


class TagField(serializers.Field):

    def to_representation(self, value):
        """
        Convert from tags to csv string of tag names.
        """
        if not isinstance(value, str):
            value = ",".join(list(value.names()))
        return value

    def to_internal_value(self, data):
        """
        Convert from csv string of tag names to list of tags.
        """
        return data.split(",")


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ("id", "image", "content_type",
                  "object_id", "main_image", "is_active", "company")
        read_only_fields = ("id", "content_type",
                            "object_id", "is_active", "company")


class ProductOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductOption
        fields = ("id", "productparent", "name", "value")
        read_only_fields = ("id", "productparent",)


class ProductVariationOptionSerializer(serializers.ModelSerializer):

    productoption = ProductOptionSerializer(
        read_only=False)

    class Meta:
        model = ProductVariationOption
        fields = ("id", "productoption")
        read_only_fields = ("id",)


class ProductVariationSerializer(serializers.ModelSerializer):
    weight = WeightField(required=False)
    product_variation_options = ProductVariationOptionSerializer(
        many=True, read_only=False, required=False)
    images = ImageSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = Product
        fields = ("id", "productparent", "title", "sku", "ean", "model_number",
                  "manufacturer_part_number", "length", "width", "depth",
                  "length_unit", "weight", "is_active", "extra_data", "product_variation_options", "images",)
        read_only_fields = ("id", "is_active", "extra_data",
                            "productparent", "images",)


class ProductSerializer(serializers.ModelSerializer):
    '''
    ModelSerializer to create component
    '''
    tags = TagField(required=False)
    status = StatusSerializer()
    products = ProductVariationSerializer(
        many=True, read_only=False)
    images = ImageSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = ProductParent
        fields = ("id", "company", "is_component", "title", "type", "series",
                  "hscode", "sku", "bullet_points", "description",
                  "tags", "is_active", "status", "extra_data", "products", "images")
        read_only_fields = ("id", "is_active", "extra_data",
                            "company", "images",)

    def validate(self, attrs):
        products = attrs.get("products", [])
        if len(products) <= 1:
            msg = _("At Least one child product required.")
            raise serializers.ValidationError(
                {"products": msg})
        return super().validate(attrs)


class ProductComponentSerializer(serializers.ModelSerializer):
    # TODO what about archived and draft products ?
    class Meta:
        model = ProductComponent
        fields = ("id", "product", "component",
                  "quantity", "value", "is_active",)
        read_only_fields = ("id", "is_active",)

    def validate(self, attrs):
        '''
        validate that :
            the selected product and component must relate to the current company.
            product must not be marked as a component.
            component must be marked as a component.
        '''
        kwargs = self.context["request"].resolver_match.kwargs
        product = attrs.get("product", None)
        component = attrs.get("component", None)
        errors = {}
        if product:
            if str(product.get_company.id) != str(kwargs.get("company_pk", None)):
                errors = set_field_errors(errors, "product", _(
                    "Invalid product selected."))
            if str(product.productparent.id) != str(kwargs.get("product_pk", None)):
                errors = set_field_errors(errors, "product", _(
                    "Selected product variation is not from current Product."))
            if product.productparent.is_component:
                errors = set_field_errors(errors, "product", _(
                    "Selected product is a component."))
        if component:
            if str(component.get_company.id) != str(kwargs.get("company_pk", None)):
                errors = set_field_errors(errors, "component", _(
                    "Invalid component selected."))
            if not component.productparent.is_component:
                errors = set_field_errors(errors, "component", _(
                    "Selected component is a product."))
        if errors:
            raise serializers.ValidationError(errors)
        return super().validate(attrs)


class ProductRrpSerializer(serializers.ModelSerializer):
    # TODO what about archived and draft products ?
    # TODO should use unique together validation to avoid duplication ?
    country = CountrySerializerField()
    rrp = MoneyField(max_digits=14, decimal_places=2)

    class Meta:
        model = ProductRrp
        fields = ("id", "product", "rrp",
                  "country", "is_active",)
        read_only_fields = ("id", "is_active",)

    def validate(self, attrs):
        '''
        validate that :
            the selected product must relate to the current company.
            product must not be marked as a component.
        '''
        kwargs = self.context["request"].resolver_match.kwargs
        product = attrs.get("product", None)
        errors = {}
        if product:
            if str(product.get_company.id) != str(kwargs.get("company_pk", None)):
                errors = set_field_errors(errors, "product", _(
                    "Invalid product selected."))
            if str(product.productparent.id) != str(kwargs.get("product_pk", None)):
                errors = set_field_errors(errors, "product", _(
                    "Selected product variation is not from current Product."))
            if product.productparent.is_component:
                errors = set_field_errors(errors, "product", _(
                    "Selected product is a component."))
        if errors:
            raise serializers.ValidationError(errors)
        return super().validate(attrs)


class ProductPackingBoxSerializer(serializers.ModelSerializer):
    # TODO what about archived and draft products ?
    # TODO should use unique together validation to avoid duplication ?
    # TODO components can also have packing box ?
    weight = WeightField()

    class Meta:
        model = ProductPackingBox
        fields = ("id", "product", "packingbox",
                  "weight", "units", "is_active",)
        read_only_fields = ("id", "is_active",)

    def validate(self, attrs):
        '''
        validate that :
            the selected product and packingbox must relate to the current company.
            product must not be marked as a component.
        '''
        kwargs = self.context["request"].resolver_match.kwargs
        product = attrs.get("product", None)
        packingbox = attrs.get("packingbox", None)
        errors = {}
        if product:
            if str(product.get_company.id) != str(kwargs.get("company_pk", None)):
                errors = set_field_errors(errors, "product", _(
                    "Invalid product selected."))
            if str(product.productparent.id) != str(kwargs.get("product_pk", None)):
                errors = set_field_errors(errors, "product", _(
                    "Selected product variation is not from current Product."))
            if product.productparent.is_component:
                errors = set_field_errors(errors, "product", _(
                    "Selected product is a component."))
        if packingbox:
            if str(packingbox.company.id) != str(kwargs.get("company_pk", None)):
                errors = set_field_errors(errors, "packingbox", _(
                    "Invalid packingbox selected."))
        if errors:
            raise serializers.ValidationError(errors)
        return super().validate(attrs)
