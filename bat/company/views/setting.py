from rest_framework import status, viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from collections import OrderedDict
from rolepermissions.roles import RolesManager
from invitations.utils import get_invitation_model
from notifications.signals import notify


from bat.company.models import Company, Member
from bat.company import serializers

Invitation = get_invitation_model()
User = get_user_model()


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


"""
input to content
{
"first_name":"fname",
"last_name":"lname",
"email":"fname@gmail.com",
"job_title":"manager",
"role":"supply_chain_manager",
"permissions":["view_product","add_product"]
}
"""


class InvitationCreate(viewsets.ViewSet):

    def create(self, request, company_pk):
        """
        create and seng invivation to given email address
        """
        company_qs = Company.objects.filter(
            member_company__user__id=request.user.id)
        company = get_object_or_404(
            company_qs, pk=company_pk)
        serializer = serializers.InvitationDataSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.data

        # User Detail
        first_name = data["first_name"]
        last_name = data["last_name"]
        job_title = data["job_title"]
        user_detail = {
            "first_name": first_name,
            "last_name": last_name,
            "job_title": job_title,
        }
        email = data["email"].lower()

        # Company Detail
        company_detail = {
            "company_id": company.id,
            "company_name": company.name,
        }

        # User Roles
        user_roles = {"roles": data["role"],
                      "perms": list(data["permissions"])}

        extra_data = {}
        extra_data["type"] = "Member Invitation"

        inviter = User.objects.get(pk=request.user.id)

        invite = Invitation.create(
            email,
            inviter=inviter,
            user_detail=user_detail,
            company_detail=company_detail,
            user_roles=user_roles,
            extra_data=extra_data,
        )
        invite.send_invitation(request)

        user = User.objects.filter(email=email).first()
        # url to accept invitation
        print("accept url : ", reverse("api:users:invitationdetail-accept",
                                       kwargs={"pk": invite.id}))
        if user:
            actions = [
                {
                    "href": reverse("api:users:invitationdetail-accept", kwargs={"pk": invite.id}),
                    "title": _("View invitation"),
                }
            ]
            notify.send(
                request.user,
                recipient=user,
                verb=_("sent you an staff member invitation"),
                action_object=invite,
                target=company,
                description=_(
                    "{} has invited you to access {} as a staff \
                    member."
                ).format(request.user.username, company.name),
                actions=actions,
            )
        return Response(status=status.HTTP_200_OK)
