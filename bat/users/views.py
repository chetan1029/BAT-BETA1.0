from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from invitations.utils import get_invitation_model
from notifications.signals import notify

from bat.users import serializers
from bat.company.utils import get_list_of_roles_permissions

User = get_user_model()
Invitation = get_invitation_model()


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
        '''
        filter invitations for current user.
        return pending invitations
        '''
        queryset = queryset.filter(
            accepted=False, email=self.request.user.email)
        return queryset

    @action(detail=True, methods=['post'])
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
        return Response({"message": _("Accepted successfully")},
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
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
        return Response({"message": _("Rejected successfully")},
                        status=status.HTTP_200_OK)


# class UserDetailView(LoginRequiredMixin, DetailView):
#     model = User
#     slug_field = "username"
#     slug_url_kwarg = "username"
# user_detail_view = UserDetailView.as_view()
# class UserUpdateView(LoginRequiredMixin, UpdateView):
#     model = User
#     fields = ["name"]
#     def get_success_url(self):
#         return reverse("users:detail", kwargs={"username": self.request.user.username})
#     def get_object(self):
#         return User.objects.get(username=self.request.user.username)
#     def form_valid(self, form):
#         messages.add_message(
#             self.request, messages.INFO, _("Infos successfully updated")
#         )
#         return super().form_valid(form)
# user_update_view = UserUpdateView.as_view()
# class UserRedirectView(LoginRequiredMixin, RedirectView):
#     permanent = False
#     def get_redirect_url(self):
#         return reverse("users:detail", kwargs={"username": self.request.user.username})
# user_redirect_view = UserRedirectView.as_view()
