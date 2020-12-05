from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from rest_framework import viewsets, status, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from django_filters.rest_framework import DjangoFilterBackend

from bat.company import file_serializers
from bat.company.models import File
from bat.company.utils import get_member
from bat.globalutils.utils import has_any_permission


class BaseFilesViewSet(mixins.DestroyModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):

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

    def destroy(self, request, *args, **kwargs):
        company_pk = kwargs.get("company_pk", None)
        member = get_member(company_id=company_pk, user_id=request.user.id)
        if not (has_any_permission(member, self.permission_list)):
            return Response({"detail": _("You do not have permission to perform this action.")}, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


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


class CompanyOrderCaseFilesViewSet(BaseFilesViewSet):
    """
    View set to save files of CompanyOrderCase
    """
    permission_list = ["add_order_case", "change_order_case"]

    def get_content_type(self):
        return ContentType.objects.get(
            app_label='company', model='companyordercase')


class CompanyOrderInspectionFilesViewSet(BaseFilesViewSet):
    """
    View set to save files of CompanyOrderInspection
    """
    permission_list = ["add_order_inspection", "change_order_inspection"]

    def get_content_type(self):
        return ContentType.objects.get(
            app_label='company', model='companyorderinspection')
