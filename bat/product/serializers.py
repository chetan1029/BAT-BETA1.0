from rest_framework import serializers

from django.utils.translation import ugettext_lazy as _

from bat.product.models import ProductParent, Product
from bat.serializersFields.serializers_fields import WeightField


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

    class Meta:
        model = ProductParent
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    weight = WeightField(required=True)

    class Meta:
        model = Product
        fields = ("id", "productparent", "title", "sku", "ean", "model_number",
                  "manufacturer_part_number", "length", "width", "depth",
                  "length_unit", "weight", "is_active", "extra_data")
        read_only_fields = ("id", "is_active", "extra_data", "productparent")

    def validate(self, data):
        return super().validate(data)
