from rest_framework import serializers

from bat.setting.models import Category, DeliveryTermName, DeliveryTerms, Status


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
