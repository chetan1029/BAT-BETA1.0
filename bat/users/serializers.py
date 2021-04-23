from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from invitations.utils import get_invitation_model
from rest_auth.registration.serializers import RegisterSerializer
from rest_auth.serializers import PasswordResetSerializer
from rest_framework import serializers
from rolepermissions.roles import assign_role


from bat.users.models import InvitationDetail, UserLoginActivity
from bat.company.models import Company, Member
from bat.company.utils import set_default_company_payment_terms
from bat.subscription.utils import set_default_subscription_plan_on_company


Invitation = get_invitation_model()
User = get_user_model()


class RestAuthRegisterSerializer(RegisterSerializer):

    company_name = serializers.CharField(required=False)
    invite_key = serializers.CharField(allow_blank=True, required=False)

    def validate(self, data):
        validate_data = super().validate(data)
        invite_key = validate_data.get("invite_key", None)
        company_name = validate_data.get("company_name", None)

        if not invite_key and not company_name:
            raise serializers.ValidationError(
                _("The company_name is required."))

        return validate_data

    def get_cleaned_data(self):
        return {
            "company_name": self.validated_data.get("company_name", ""),
            "username": self.validated_data.get("username", ""),
            "password1": self.validated_data.get("password1", ""),
            "email": self.validated_data.get("email", ""),
            "invite_key": self.validated_data.get("invite_key"),
        }

    def custom_signup(self, request, user):
        """
        save extra_data to user
        """
        extra_data = {}
        # Check if this user has accpeted invitations or even have
        # any invitation. we will signup and forward user.
        invite_key = self.cleaned_data.get("invite_key")
        invite = Invitation.objects.filter(
            key=invite_key, accepted=False
        ).first()
        if invite:
            invite.accepted = True
            invite.save()

        invitations = Invitation.objects.filter(
            email=user.email, accepted=True
        )
        if invitations.exists():
            extra_data["step"] = 2
            extra_data["step_detail"] = "account setup"
        else:
            extra_data["step"] = 1
            extra_data["step_detail"] = "user signup"
        user.extra_data = extra_data
        user.save()

        # create company
        if user.extra_data["step"] == 1:
            company_name = self.cleaned_data.get("company_name")
            company = Company.objects.create(name=company_name, email=user.email)

            extra_data = {}
            extra_data["user_role"] = "company_admin"
            member, create = Member.objects.get_or_create(
                job_title="Admin",
                user=user,
                company=company,
                invited_by=user,
                is_admin=True,
                is_active=True,
                invitation_accepted=True,
                extra_data=extra_data,
            )
            if create:
                # fetch user role from the User and assign after signup.
                assign_role(member, member.extra_data["user_role"])

            set_default_company_payment_terms(company=company)
            if not company.companytype_company.exists():
                set_default_subscription_plan_on_company(company=company)

            user.extra_data["step"] = 2
            user.extra_data["step_detail"] = "account setup"
            user.save()


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = (
            "id",
            "email",
            "created",
            "user_detail",
            "company_detail",
            "user_roles",
            "extra_data",
        )
        read_only_fields = (
            "id",
            "email",
            "user_detail",
            "company_detail",
            "user_roles",
            "extra_data",
        )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "first_login",
            "last_login",
            "date_joined",
            "username",
            "email",
            "first_name",
            "last_name",
            "profile_picture",
            "phone_number",
        )
        read_only_fields = (
            "first_login",
            "last_login",
            "date_joined",
            "username",
            "email",
        )


class PasswordSerializer(PasswordResetSerializer):
    def get_email_options(self):
        return {
            "subject_template_name": "account/email/password_reset_key_subject.txt",
            "email_template_name": "account/email/password_reset_key_message.txt",
            "extra_email_context": {
                "reset_link": settings.FORGET_PASSWORD_PAGE_LINK
            },
        }


class UserLoginActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLoginActivity
        fields = ("ip", "logged_in_at", "agent_info", "location")
