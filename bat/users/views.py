from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from invitations.utils import get_invitation_model
from notifications.signals import notify
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from bat.company.utils import get_list_of_roles_permissions
from bat.users import serializers

from bat.users.models import UserLoginActivity

User = get_user_model()
Invitation = get_invitation_model()


class UserViewSet(
    RetrieveModelMixin, UpdateModelMixin, viewsets.GenericViewSet
):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "username"

    def get_queryset(self, *args, **kwargs):
        """
        filter query for current user
        """
        # return self.queryset.filter(username=self.kwargs.get("username"))
        return self.queryset.filter(username=self.request.user.username)


class RolesandPermissionsViewSet(viewsets.ViewSet):
    def list(self, request):
        """
        list available Roles and Permissions for user
        """
        all_roles = get_list_of_roles_permissions()
        return Response(all_roles, status=status.HTTP_200_OK)


class InvitationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = serializers.InvitationSerializer

    def filter_queryset(self, queryset):
        """
        filter invitations for current user.
        return pending invitations
        """
        queryset = queryset.filter(
            accepted=False, email=self.request.user.email
        )

        invite_key = self.request.GET.get('inviteKey', None)
        if invite_key:
            queryset = queryset.filter(key=invite_key)
        return queryset

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """
        accept invitation
        and perform signals to complete tasks
        """
        instance = self.get_object()
        instance.accepted = True
        instance.save()
        post_save.send(
            User, instance=self.request.user, created=False, using=None
        )
        return Response(
            {"detail": _("Accepted successfully")}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """
        reject invitation
        and notify sender
        """
        instance = self.get_object()
        notify.send(
            self.request.user,
            recipient=instance.inviter,
            verb=_("Rejected your invitation"),
            target_id=instance.company_detail["company_id"],
        )
        instance.delete()
        return Response(
            {"detail": _("Rejected successfully")}, status=status.HTTP_200_OK
        )


class UserLoginActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserLoginActivity.objects.all()
    serializer_class = serializers.UserLoginActivitySerializer

    def get_queryset(self, *args, **kwargs):
        """
        filter query for current user
        """
        return self.queryset.filter(user=self.request.user)