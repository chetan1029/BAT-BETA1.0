
from rest_framework import serializers

from bat.company.models import File



class FileSerializer(serializers.ModelSerializer):
    """
    Serializer to support list of file objects.
    """
    class Meta:
        model = File
        fields = ("id", "title", "version", "company",
                  "file", "note", "content_type", "object_id", "is_active",)
        read_only_fields = ("id", "is_active",
                            "content_type", "object_id", "company")
