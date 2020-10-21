"""Model classes for user."""

import datetime
import os

import pytz

from bat.globalprop.validator import validator
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import HStoreField
from django.contrib.sites.models import Site
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from invitations import signals
from invitations.adapters import get_invitations_adapter
from invitations.app_settings import app_settings
from invitations.base_invitation import AbstractBaseInvitation
from rolepermissions.roles import get_user_roles

# Create your models here.


def profilepic_name(instance, filename):
    """Change name of profile pic with username."""
    name, extension = os.path.splitext(filename)
    return "user/images/{0}.{1}".format(instance.username, extension)


class User(AbstractUser):
    """
    Extending User class to User Profile.

    To add additional profile pic and other info.
    """

    profile_picture = models.ImageField(
        upload_to=profilepic_name,
        blank=True,
        verbose_name=_("Profile Picture"),
    )
    phone_validator = validator.phone_validator()
    phone_number = models.CharField(
        validators=[phone_validator],
        max_length=17,
        blank=True,
        verbose_name=_("Phone Number"),
    )
    language = models.CharField(
        max_length=50,
        verbose_name=_("Language"),
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
    )
    timezone = models.CharField(
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


class InvitationDetail(AbstractBaseInvitation):
    """
    Extending Django Invitation Model.

    We will use this model to save detail about invitation like user detail or
    company detail and their roles so we once they signup we will fetch those
    detail and allot them respective values.
    """

    email = models.EmailField(verbose_name=_("e-mail address"), max_length=200)
    created = models.DateTimeField(
        verbose_name=_("created"), default=timezone.now
    )
    user_detail = models.JSONField(null=True, blank=True)
    company_detail = models.JSONField(null=True, blank=True)
    user_roles = models.JSONField(null=True, blank=True)
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
        current_site = kwargs.pop("site", Site.objects.get_current())
        invite_url = reverse("invitations:accept-invite", args=[self.key])
        invite_url = request.build_absolute_uri(invite_url)
        ctx = kwargs
        ctx.update(
            {
                "invite_url": invite_url,
                "site_name": current_site.name,
                "email": self.email,
                "key": self.key,
                "inviter": self.inviter,
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
        return "Invite: {0}".format(self.email)
