from rest_framework import serializers

from bat.setting.models import (
    Category,
    DeliveryTermName,
    DeliveryTerms,
    DeliveryTermService,
    Status,
)


class StatusSerializer(serializers.ModelSerializer):
    """Serializer for Status."""

    class Meta:
        """Define field that we wanna show in the Json."""

        model = Status
        fields = ("id", "name", "parent", "user", "is_active")
        read_only_fields = ("id", "name", "parent", "user", "is_active")


class CategorySerializer(serializers.ModelSerializer):
    """Global category serializer."""

    parent_details = serializers.SerializerMethodField()

    def get_parent_details(self, obj):
        return CategorySerializer(obj.parent).data if obj.parent else {}

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "rule",
            "parent",
            "user",
            "is_active",
            "parent_details",
        )
        read_only_fields = ("id", "is_active")


class DeliveryTermNameSerializer(serializers.ModelSerializer):
    """Delivery Term name serializer."""

    class Meta:
        model = DeliveryTermName
        fields = ("id", "name", "code", "detail", "is_active", "extra_data")
        read_only_fields = ("id", "is_active")


class DeliveryTermServiceSerializer(serializers.ModelSerializer):
    """Delivery Term Services serializer."""

    class Meta:
        model = DeliveryTermService
        fields = ("id", "name", "detail")
        read_only_fields = "id"


class DeliveryTermsSerializer(serializers.ModelSerializer):
    """Delivery Terms serializer."""

    term_name = DeliveryTermNameSerializer(read_only=True)
    service = DeliveryTermServiceSerializer(read_only=True)

    class Meta:
        model = DeliveryTerms
        fields = (
            "id",
            "term_name",
            "service",
            "who_pays",
            "create_date",
            "update_date",
        )
        read_only_fields = ("id", "create_date", "update_date")
