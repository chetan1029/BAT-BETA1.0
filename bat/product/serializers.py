from itertools import groupby

from rest_framework import serializers

from django.utils.translation import ugettext_lazy as _

from bat.product.models import ProductParent, Product
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


class ProductParentSerializer(serializers.ModelSerializer):
    tags = TagField(required=False)
    status = StatusSerializer()

    class Meta:
        model = ProductParent
        fields = ("id", "company", "is_component", "title", "type", "series",
                  "hscode", "sku", "bullet_points", "description",
                  "tags", "is_active", "status", "extra_data")
        read_only_fields = ("id", "is_active", "extra_data", "company")


class ProductVariationSerializer(serializers.ModelSerializer):
    weight = WeightField(required=True)

    class Meta:
        model = Product
        fields = ("id", "productparent", "title", "sku", "ean", "model_number",
                  "manufacturer_part_number", "length", "width", "depth",
                  "length_unit", "weight", "is_active", "extra_data")
        read_only_fields = ("id", "is_active", "extra_data", "productparent")

    def validate(self, data):
        # TODO
        return super().validate(data)


class ProductSerializer(serializers.ModelSerializer):
    tags = TagField(required=False)
    status = StatusSerializer()
    products = ProductVariationSerializer(
        many=True, read_only=False)

    class Meta:
        model = ProductParent
        fields = ("id", "company", "is_component", "title", "type", "series",
                  "hscode", "sku", "bullet_points", "description",
                  "tags", "is_active", "status", "extra_data", "products")
        read_only_fields = ("id", "is_active", "extra_data", "company")

    def validate(self, data):
        # TODO
        print("\n\n\n data :", data)
        products = data.get("products", None)
        # define a fuction for key

        def _model_number_func(k):
            return k['model_number']

        def _manufacturer_part_number_func(k):
            return k['manufacturer_part_number']
        if products:
            group_by_model_number = groupby(products, _model_number_func)
            if len(list(group_by_model_number)) != len(products):
                msg = _("model_number should be unique.")
                raise serializers.ValidationError(
                    {"products": {"model_number": msg}})

            group_by_manufacturer_part_number = groupby(
                products, _manufacturer_part_number_func)
            if len(list(group_by_manufacturer_part_number)) != len(products):
                msg = _("manufacturer_part_number should be unique.")
                raise serializers.ValidationError(
                    {"products": {"manufacturer_part_number": msg}})

        return super().validate(data)
