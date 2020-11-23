
from rest_framework import serializers

from bat.product.models import Image
from bat.company.serializers import CompanySerializer


class ImageListSerializer(serializers.ListSerializer):
    """
    Serializer to accept list of Image objects.
    """

    def create(self, validated_data):
        images_objects = [Image(**item)
                          for item in validated_data]
        images = Image.objects.bulk_create(images_objects)
        return images


class ImageSerializer(serializers.ModelSerializer):
    """
    Serializer to support list of Image objects.
    """
    class Meta:
        model = Image
        fields = ("id", "image", "content_type",
                  "object_id", "main_image", "is_active", "company")
        read_only_fields = ("id", "is_active",)
        list_serializer_class = ImageListSerializer
