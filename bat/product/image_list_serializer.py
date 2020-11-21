
from rest_framework import serializers

from django.utils.translation import ugettext_lazy as _

from bat.product.models import Image, ProductParent, Product

CONTENT_TYPE = {
    "product": ProductParent,
    "productvariant": Product
}


class ImageListSerializer(serializers.ListSerializer):
    update_lookup_field = 'id'

    def create(self, validated_data):
        obj = CONTENT_TYPE[self.context.get("content_type", None)].objects.get(id=self.context.get(
            "object_id", None))
        images_objects = [Image(content_object=obj, **item)
                          for item in validated_data]
        images = Image.objects.bulk_create(images_objects)
        return images


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ("id", "image", "content_type",
                  "object_id", "main_image", "is_active",)
        read_only_fields = ("id", "content_type", "object_id", "is_active",)
        list_serializer_class = ImageListSerializer

    def create(self, validated_data):
        print("\n\n\nn\nn ", validated_data)
        obj = CONTENT_TYPE[self.context.get("content_type", None)].objects.get(id=self.context.get(
            "object_id", None))
        image = Image(content_object=obj, **validated_data)
        image.save()
        return image


class ImagesSerializer(serializers.Serializer):
    images = serializers.ListField(child=serializers.ImageField())
    main_image = serializers.ImageField()
