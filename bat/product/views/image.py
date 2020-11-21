from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from dry_rest_permissions.generics import DRYPermissions
from rest_framework import viewsets, mixins, generics, status
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action


from bat.product import image_list_serializer, serializers
from bat.product.models import Image, Product, ProductParent
from bat.company.utils import get_member


class BaseImagesViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def create(self, request, company_pk, object_pk):
        images_data = []
        member = get_member(company_id=company_pk, user_id=request.user.id)
        for file_name, f in request.data.items():
            images_data.append({
                'company': company_pk,
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

    @action(methods=['DELETE'], detail=False)
    def destroy_bulk(self, request, company_pk, object_pk):
        ids = list(eval(request.GET.get("ids", None)))
        images = Image.objects.filter(
            company__id=company_pk, object_id=object_pk, id__in=ids)
        if not images.exists():
            return Response({_("images not found")}, status=status.HTTP_404_NOT_FOUND)
        try:
            images.delete()
            return Response({_("deleted successfully")}, status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response({_("can't deleted")}, status=status.HTTP_400_BAD_REQUEST)


class ProductImagesViewSet(BaseImagesViewSet):

    content_type = ContentType.objects.get(
        app_label='product', model='productparent')


class ProductVariationImagesViewSet(BaseImagesViewSet):

    content_type = ContentType.objects.get(
        app_label='product', model='product')
