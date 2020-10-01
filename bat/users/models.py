"""Model classes for user."""

import os

import pytz

from bat.globalprop.validator import validator
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.utils.translation import ugettext_lazy as _
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
