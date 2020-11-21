from itertools import groupby

from rest_framework import serializers

from django.utils.translation import ugettext_lazy as _

from bat.product.models import ProductParent, Product, ProductOption, ProductVariationOption, Image
from bat.serializersFields.serializers_fields import WeightField
from bat.setting.serializers import StatusSerializer


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
