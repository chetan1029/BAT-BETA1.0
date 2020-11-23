from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from rolepermissions.checkers import has_permission


from bat.product import image_list_serializer
from bat.product.models import Image
from bat.company.utils import get_member


class BaseImagesViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def create(self, request, company_pk, object_pk):
        """
        Save all the images sent through form data.
        """
        images_data = []
        member = get_member(company_id=company_pk, user_id=request.user.id)
        if not (has_permission(member, "add_product") or has_permission(member, "change_product")):
            return Response({"detail": _("You do not have permission to perform this action.")}, status=status.HTTP_403_FORBIDDEN)

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
            return Response({"detail": _("Not a image to save")}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['DELETE'], detail=False)
    def destroy_bulk(self, request, company_pk, object_pk):
        """
        Delete all the images which id is specified in the list
        """
        ids = request.GET.get("ids", None).split(",")
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
    """
    View set to save images of product
    """
    content_type = ContentType.objects.get(
        app_label='product', model='productparent')


class ProductVariationImagesViewSet(BaseImagesViewSet):
    """
    View set to save images of product variation
    """
    content_type = ContentType.objects.get(
        app_label='product', model='product')
