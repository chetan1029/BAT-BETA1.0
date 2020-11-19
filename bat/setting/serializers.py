from rest_framework import serializers

from bat.setting.models import Status


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
