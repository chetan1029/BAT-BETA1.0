from rest_framework import serializers

from bat.setting.models import Status, Category


class StatusSerializer(serializers.ModelSerializer):
    """Serializer for Status."""

    class Meta:
        """Define field that we wanna show in the Json."""

        model = Status
        fields = (
            "id",
            "name",
            "parent",
            "user",
            "is_active",
        )
        read_only_fields = (
            "id",
            "name",
            "parent",
            "user",
            "is_active",
        )

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "rule",
            "parent",
            "user",
            "is_active",
        )
        read_only_fields = (
            "id",
            "is_active",
        )
