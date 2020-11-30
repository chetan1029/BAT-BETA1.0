
from rest_framework import serializers

from bat.company.models import File
from bat.company.serializers import CompanySerializer


class FileListSerializer(serializers.ListSerializer):
    """
    Serializer to accept list of File objects.
    """

    def create(self, validated_data):
        files_objects = [File(**item)
                         for item in validated_data]
        files = File.objects.bulk_create(files_objects)
        return files


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
        ref_name = "file_serializer_2"
