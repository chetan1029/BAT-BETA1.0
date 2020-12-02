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


class CompanyContractFilesViewSet(BaseFilesViewSet):
    """
    View set to save files of CompanyContract
    """
    permission_list = ["add_company_contract", "change_company_contract"]

    def get_content_type(self):
        return ContentType.objects.get(
            app_label='company', model='companycontract')


class ComponentMeFilesViewSet(BaseFilesViewSet):
    """
    View set to save files of ComponentMe
    """
    permission_list = ["add_component_me", "change_component_me"]

    def get_content_type(self):
        return ContentType.objects.get(
            app_label='company', model='componentme')
