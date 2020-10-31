import pytz
import os


from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, ImageField
from django.urls import reverse
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import HStoreField


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
        default=settings.LANGUAGE_CODE,
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

    # @property
    # def roles(self):
    #     """User roles."""
    #     return get_user_roles(self)

    # def is_memberprofile(self):
    #     """User have an active member profile or not."""
    #     from bat.company.models import Member

    #     if Member.objects.filter(user=self, is_active=True).exists():
    #         return True
    #     else:
    #         return False

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})
