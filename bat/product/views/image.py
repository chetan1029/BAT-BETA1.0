from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.contenttypes.models import ContentType
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import viewsets, mixins, generics, status
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from bat.product import image_list_serializer, serializers
from bat.product.models import Image, Product, ProductParent


class BaseImagesViewSet(viewsets.ViewSet):

    def create(self, request, company_pk, object_pk):
        images_data = []
        for file_name, f in request.data.items():
            images_data.append({
                'content_type': self.content_type.id,
                'object_id': object_pk,
                'image': f,
                'main_image': file_name == 'main_image',
            })
        if images_data:
            serializer = image_list_serializer.ImageSerializer(
                data=images_data, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)


class ProductImagesViewSet(BaseImagesViewSet):

    content_type = ContentType.objects.get(
        app_label='product', model='productparent')


class ProductVariationImagesViewSet(BaseImagesViewSet):

    content_type = ContentType.objects.get(
        app_label='product', model='product')
