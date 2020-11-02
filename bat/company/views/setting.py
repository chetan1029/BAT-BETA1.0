from rest_framework import status, viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from bat.company.models import Company, Member
from bat.company import serializers


class AccountSetupViewset(mixins.CreateModelMixin,
                          viewsets.GenericViewSet):
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
        self.request.user.extra_data["step"] = 2
        self.request.user.extra_data["step_detail"] = "account setup"
        self.request.user.save()
