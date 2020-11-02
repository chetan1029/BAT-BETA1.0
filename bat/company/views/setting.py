from rest_framework import status, viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404

from collections import OrderedDict
from rolepermissions.roles import RolesManager


from bat.company.models import Company, Member
from bat.company import serializers


class CompanyViewset(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):  # TODO perform delete
    queryset = Company.objects.all()
    serializer_class = serializers.CompanySerializer
    permission_classes = (IsAuthenticated, )

    def perform_create(self, serializer):
        company = serializer.save()
        request = self.request

        extra_data = {}
        extra_data["user_role"] = "company_admin"
        member, _c = Member.objects.get_or_create(
            job_title="Admin",
            user=self.request.user,
            company=company,
            invited_by=self.request.user,
            is_admin=True,
            is_active=True,
            invitation_accepted=True,
            extra_data=extra_data,
        )
        # we have a signal that will allot that role to this user.
        # TODO if current user is allready company_admin of one of the company then skip "step"
        self.request.user.extra_data["step"] = 2
        self.request.user.extra_data["step_detail"] = "account setup"
        self.request.user.save()

    def filter_queryset(self, queryset):
        request = self.request
        queryset = queryset.filter(member_company__user__id=request.user.id)
        return queryset


class MemberViewset(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    queryset = Member.objects.all()
    serializer_class = serializers.MemberSerializer
    permission_classes = (IsAuthenticated, )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        all_roles = OrderedDict()
        for role in RolesManager.get_roles():
            role_name = role.get_name()
            all_roles[role_name] = {
                "display_name": "".join(
                    x.capitalize() + " " or "_" for x in role_name.split("_")
                ),
                "permissions": {
                    perm: "".join(
                        x.capitalize() + " " or "_" for x in perm.split("_")
                    )
                    for perm in role.permission_names_list()
                },
            }

        context["available_roles"] = all_roles
        return context

    def perform_create(self, serializer):
        Member = serializer.save()
        # company = get_object_or_404(
        #     Company, pk=self.kwargs.get("company_pk", None))
