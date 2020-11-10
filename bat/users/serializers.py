from rest_framework import serializers

from django.contrib.auth import get_user_model

from rest_auth.registration.serializers import RegisterSerializer
from invitations.utils import get_invitation_model

from bat.users.models import InvitationDetail

Invitation = get_invitation_model()
User = get_user_model()


class RestAuthRegisterSerializer(RegisterSerializer):

    def custom_signup(self, request, user):
        '''
        save extra_data to user
        '''
        extra_data = {}
        # # Check if this user has accpeted invitations or even have
        # # any invitation. we will signup and forward user.
        invitations = Invitation.objects.filter(email=user.email)
        if invitations.exists():
            extra_data["step"] = "2"
            extra_data["step_detail"] = "account setup"
        else:
            extra_data["step"] = "1"
            extra_data["step_detail"] = "user signup"
        user.extra_data = extra_data
        user.save()


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ('email', 'created', 'user_detail',
                  'company_detail', 'user_roles', 'extra_data',)
        read_only_fields = ('email', 'user_detail',
                            'company_detail', 'user_roles', 'extra_data')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('last_login', 'date_joined', 'username', 'email',
                  'first_name', 'last_name', 'profile_picture', 'phone_number',
                  'language', 'timezone',)
        read_only_fields = ('last_login', 'date_joined', 'username', 'email',)
