
from rest_framework import serializers

from django.utils.translation import ugettext_lazy as _

from bat.product.models import Image, ProductParent, Product


class ImageListSerializer(serializers.ListSerializer):
    update_lookup_field = 'id'

    def create(self, validated_data):
        images_objects = [Image(**item)
                          for item in validated_data]
        images = Image.objects.bulk_create(images_objects)
        return images


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ("id", "image", "content_type",
                  "object_id", "main_image", "is_active",)
        read_only_fields = ("id", "is_active",)
        list_serializer_class = ImageListSerializer
