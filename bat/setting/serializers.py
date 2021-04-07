from rest_framework import serializers

from bat.serializersFields.serializers_fields import get_status_json
from bat.setting.models import (
    Category,
    DeliveryTermName,
    DeliveryTerms,
    LogisticLeadTime,
    Status,
)


class StatusSerializer(serializers.ModelSerializer):
    """Serializer for Status."""

    parent = serializers.SerializerMethodField()

    def get_parent(self, obj):
        return obj.parent.name if obj.parent else None

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


class DeliveryTermsSerializer(serializers.ModelSerializer):
    """Delivery Terms serializer."""

    class Meta:
        model = DeliveryTerms
        fields = ("id", "deliverytermname", "service_name", "who_pays")
        read_only_fields = ("id",)


class DeliveryTermNameSerializer(serializers.ModelSerializer):
    """Delivery Term name serializer."""

    deliveryterms = DeliveryTermsSerializer(many=True, read_only=True)

    class Meta:
        model = DeliveryTermName
        fields = (
            "id",
            "name",
            "code",
            "detail",
            "is_active",
            "extra_data",
            "deliveryterms",
        )
        read_only_fields = ("id", "is_active", "deliveryterms")


class LogisticLeadTimeSerializer(serializers.ModelSerializer):
    """Logistic Lead Time serializer."""

    class Meta:
        model = LogisticLeadTime
        fields = (
            "id",
            "title",
            "from_country",
            "to_country",
            "ship_type",
            "shipping_time",
            "misc_time",
            "estimated_avg_rate",
            "rate_type",
            "is_active",
            "extra_data",
        )
        read_only_fields = ("id", "title", "is_active")
