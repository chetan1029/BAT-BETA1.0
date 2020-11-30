from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from django_filters.rest_framework import DjangoFilterBackend

from bat.company import file_serializers
from bat.company.models import File
from bat.company.utils import get_member
from bat.globalutils.utils import has_any_permission


# class BaseFilesViewSet(viewsets.ViewSet):
#     permission_classes = (IsAuthenticated,)

#     def create(self, request, company_pk, object_pk):
#         """
#         Save all the files sent through form data.
#         """
#         files_data = []
#         member = get_member(company_id=company_pk, user_id=request.user.id)
#         if not (has_any_permission(member, self.permission_list)):
#             return Response({"detail": _("You do not have permission to perform this action.")}, status=status.HTTP_403_FORBIDDEN)

#         for file_name, f in request.data.items():
#             files_data.append({
#                 'company': company_pk,
#                 'title': file_name,
#                 'content_type': self.get_content_type().id,
#                 'object_id': object_pk,
#                 'file': f,
#             })
#         if files_data:
#             serializer = file_serializers.FileSerializer(
#                 data=files_data, many=True)
#             serializer.is_valid(raise_exception=True)
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         else:
#             return Response({"detail": _("Not a file to save")}, status=status.HTTP_400_BAD_REQUEST)

#     @action(methods=['DELETE'], detail=False)
#     def destroy_bulk(self, request, company_pk, object_pk):
#         """
#         Delete all the images which id is specified in the list
#         """
#         ids = request.GET.get("ids", None).split(",")
#         images = Image.objects.filter(
#             company__id=company_pk, object_id=object_pk, id__in=ids)
#         if not images.exists():
#             return Response({_("images not found")}, status=status.HTTP_404_NOT_FOUND)
#         try:
#             images.delete()
#             return Response({_("deleted successfully")}, status=status.HTTP_204_NO_CONTENT)
#         except Exception:
#             return Response({_("can't deleted")}, status=status.HTTP_400_BAD_REQUEST)


class BaseFilesViewSet(viewsets.ModelViewSet):

    serializer_class = file_serializers.FileSerializer
    queryset = File.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

    def create(self, request, company_pk, object_pk):
        member = get_member(company_id=company_pk, user_id=request.user.id)
        if not (has_any_permission(member, self.permission_list)):
            return Response({"detail": _("You do not have permission to perform this action.")}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        content_type = self.get_content_type()
        serializer.save(company=member.company,
                        object_id=object_pk, content_type=content_type)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ComponentMeFilesViewSet(BaseFilesViewSet):
    """
    View set to save files of ComponentMe
    """
    permission_list = ["add_product", "change_product"]

    def get_content_type(self):
        return ContentType.objects.get(
            app_label='company', model='componentme')
