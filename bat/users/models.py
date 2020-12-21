import datetime
import os

import pytz
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import HStoreField
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import CharField, DateTimeField, EmailField, ImageField, JSONField
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from invitations import signals
from invitations.adapters import get_invitations_adapter
from invitations.app_settings import app_settings
from invitations.base_invitation import AbstractBaseInvitation
from rolepermissions.roles import get_user_roles

from bat.globalprop.validator import validator


def profilepic_name(instance, filename):
    """Change name of profile pic with username."""
    name, extension = os.path.splitext(filename)
    return "user/images/{0}.{1}".format(instance.username, extension)


class User(AbstractUser):
    """
    Extending User class to User Profile.

    To add additional profile pic and other info.
    """

    profile_picture = ImageField(
        upload_to=profilepic_name,
        blank=True,
        verbose_name=_("Profile Picture"),
    )
    phone_validator = validator.phone_validator()
    phone_number = CharField(
        validators=[phone_validator],
        max_length=17,
        blank=True,
        verbose_name=_("Phone Number"),
    )
    language = CharField(
        max_length=50,
        verbose_name=_("Language"),
        choices=settings.LANGUAGES,
        default='en',
    )
    timezone = CharField(
        max_length=50,
        verbose_name=_("Time Zone"),
        choices=[(x, x) for x in pytz.common_timezones],
        default=settings.TIME_ZONE,
    )
    extra_data = HStoreField(null=True, blank=True)

    def __str__(self):
        """Return Value."""
        return self.username

    @property
    def roles(self):
        """User roles."""
        return get_user_roles(self)

    def is_memberprofile(self):
        """User have an active member profile or not."""
        from bat.company.models import Member

        if Member.objects.filter(user=self, is_active=True).exists():
            return True
        else:
            return False

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})

    def get_recent_logged_in_activities(self, no_of_activities=5):
        return UserLoginActivity.objects.filter(user=self).order_by(
            "-logged_in_at"
        )[:no_of_activities]


class InvitationDetail(AbstractBaseInvitation):
    """
    Extending Django Invitation Model.

    We will use this model to save detail about invitation like user detail or
    company detail and their roles so we once they signup we will fetch those
    detail and allot them respective values.
    """

    email = EmailField(verbose_name=_("e-mail address"), max_length=200)
    created = DateTimeField(verbose_name=_("created"), default=timezone.now)
    user_detail = JSONField(null=True, blank=True)
    company_detail = JSONField(null=True, blank=True)
    user_roles = JSONField(null=True, blank=True)
    extra_data = HStoreField(null=True, blank=True)

    @classmethod
    def create(
        cls,
        email,
        inviter=None,
        user_detail=None,
        company_detail=None,
        user_roles=None,
        extra_data=None,
        **kwargs
    ):
        """Create Models."""
        key = get_random_string(64).lower()

        instance = cls._default_manager.create(
            email=email,
            key=key,
            inviter=inviter,
            user_detail=user_detail,
            company_detail=company_detail,
            user_roles=user_roles,
            extra_data=extra_data,
            **kwargs
        )
        return instance

    def key_expired(self):
        """Expired key function."""
        expiration_date = self.sent + datetime.timedelta(
            days=app_settings.INVITATION_EXPIRY
        )
        return expiration_date <= timezone.now()

    def send_invitation(self, request, **kwargs):
        """Send invitation."""

        extra_data = self.extra_data

        current_site = kwargs.pop("site", Site.objects.get_current())
        existing_user = User.objects.filter(email=self.email).first()

        company_name = self.company_detail.get("company_name")

        invite_url_root = settings.INVITE_LINK + "?"

        if existing_user:
            invite_url_root = (settings.EXISTING_INVITE_LINK + "?") if extra_data and extra_data.get(
                'type') == 'Member Invitation' else settings.VENDOR_EXISTING_INVITE_LINK + str(self.company_detail['company_id']) + '?selectedView=invitations'

        invite_url = invite_url_root + "&inviteKey=" + self.key + "&e=" + self.email

        ctx = kwargs
        ctx.update(
            {
                "invite_url": invite_url,
                "site_name": current_site.name,
                "email": self.email,
                "key": self.key,
                "inviter": self.inviter,
                "company_name": company_name,
                "inviter_name": self.inviter.get_full_name()
                or self.inviter.username,
            }
        )

        email_template = "invitations/email/email_invite"

        get_invitations_adapter().send_mail(email_template, self.email, ctx)
        self.sent = timezone.now()
        self.save()

        signals.invite_url_sent.send(
            sender=self.__class__,
            instance=self,
            invite_url_sent=invite_url,
            inviter=self.inviter,
        )

    def __str__(self):
        """Return Value."""
        return "Invite: {0}".format(self.email) + str(self.id)


class UserLoginActivity(models.Model):
    ip = models.GenericIPAddressField(
        verbose_name=_("IP address"), null=True, blank=True
    )
    logged_in_at = models.DateTimeField(
        verbose_name=_("logged in date"), auto_now=True
    )
    user = models.ForeignKey(
        User, verbose_name=_("User"), on_delete=models.CASCADE
    )
    agent_info = models.CharField(
        verbose_name=_("Agent info"), max_length=2096, null=True, blank=True
    )
    location = models.CharField(
        verbose_name=_("location"), max_length=2096, null=True, blank=True
    )

    def __str__(self):
        return str(self.user.id) + " = " + str(self.ip)
