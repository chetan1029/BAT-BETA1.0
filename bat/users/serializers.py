from rest_framework import serializers

from django.contrib.auth import get_user_model

from rest_auth.registration.serializers import RegisterSerializer
from rest_auth.serializers import PasswordResetSerializer
from invitations.utils import get_invitation_model
from django.conf import settings

from bat.users.models import InvitationDetail

Invitation = get_invitation_model()
User = get_user_model()


class RestAuthRegisterSerializer(RegisterSerializer):

    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', '')
        }

    def custom_signup(self, request, user):
        '''
        save extra_data to user
        '''
        extra_data = {}
        # Check if this user has accpeted invitations or even have
        # any invitation. we will signup and forward user.
        invitations = Invitation.objects.filter(email=user.email)
        if invitations.exists():
            extra_data["step"] = "2"
            extra_data["step_detail"] = "account setup"
        else:
            extra_data["step"] = "1"
            extra_data["step_detail"] = "user signup"
        user.extra_data = extra_data

        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
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


class PasswordSerializer(PasswordResetSerializer):
    def get_email_options(self):
        return {
            'subject_template_name': 'account/email/password_reset_key_subject.txt',
            'email_template_name': 'account/email/password_reset_key_message.txt',
            'extra_email_context': {
                'reset_link': settings.FORGET_PASSWORD_PAGE_LINK
            }
        }

