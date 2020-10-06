"""Model classes for company."""
import logging
import os

import pytz

from bat.globalprop.validator import validator
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from djmoney.models.fields import MoneyField
from djmoney.settings import CURRENCY_CHOICES
from rolepermissions.roles import get_user_roles

User = get_user_model()
logger = logging.getLogger(__name__)
# Variables
IMPERIAL = "Imperial"
METRIC = "Metric"
UNIT_SYSTEM_TYPE = ((IMPERIAL, "Imperial"), (METRIC, "Metric"))

KG = "kg"
GM = "gm"
LB = "lb"
OZ = "oz"
WEIGHT_UNIT_TYPE = ((KG, "kg"), (GM, "gm"), (LB, "lb"), (OZ, "oz"))

DEFAULT_CURRENCY = "USD"
# Create your models here.
def companylogo_name(instance, filename):
    """Manage path and name for vendor logo."""
    name, extension = os.path.splitext(filename)
    return "company/{0}/logo/logo{1}".format(instance.id, extension)


class Address(models.Model):
    """
    Address Model.

    We use address model as abstract model so it only inherited to other models
    and can't create any database table or manager etc.
    """

    address1 = models.CharField(
        max_length=200, blank=True, verbose_name=_("Address")
    )
    address2 = models.CharField(
        max_length=200, blank=True, verbose_name=_("Apartment, suite, etc.")
    )
    zip = models.CharField(
        max_length=200, blank=True, verbose_name=_("Postal/zip code")
    )
    city = models.CharField(
        max_length=200, blank=True, verbose_name=_("City/town")
    )
    region = models.CharField(
        max_length=200, blank=True, verbose_name=_("Region/province")
    )
    country = CountryField()

    class Meta:
        """Meta class to make abstract true."""

        abstract = True

    def get_formatted_address(self):
        """Get formatted address."""
        address = ""
        if (
            self.address1 is None
            and self.address2 is None
            and self.city is None
            and self.region is None
            and self.country is None
            and self.zip is None
        ):
            address = ""
        else:
            if self.address1:
                address += self.address1
            if self.address2:
                address += ", " + self.address2
            if self.city:
                address += "<br />" + self.city
            if self.region:
                address += ", " + self.region
            if self.country:
                address += "<br />" + self.country.name
            if self.country.code:
                address += " (" + self.country.code + ")"
            if self.zip:
                address += ", " + self.zip
        return address.strip(",")


class Company(Address):
    """
    Company Model.

    Model to store information for companies.
    """

    phone_validator = validator.phone_validator()

    name = models.CharField(max_length=200, verbose_name=_("Name"))
    abbreviation = models.CharField(
        verbose_name=_("Abbreviation"), max_length=30, blank=True
    )
    email = models.EmailField(max_length=100, verbose_name=_("Email"))
    logo = models.ImageField(
        upload_to=companylogo_name, blank=True, verbose_name=_("Logo")
    )
    phone_number = models.CharField(
        validators=[phone_validator],
        max_length=17,
        blank=True,
        verbose_name=_("Phone Number"),
    )
    organization_number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Organization number"),
        help_text=_("Company register number from head office country."),
    )
    currency = models.CharField(
        max_length=50,
        choices=CURRENCY_CHOICES,
        verbose_name=_("Currency"),
        default=DEFAULT_CURRENCY,
    )
    unit_system = models.CharField(
        max_length=20,
        choices=UNIT_SYSTEM_TYPE,
        default=METRIC,
        verbose_name=_("Unit System"),
    )
    weight_unit = models.CharField(
        max_length=20,
        choices=WEIGHT_UNIT_TYPE,
        default=GM,
        verbose_name=_("Weight Unit"),
    )
    language = models.CharField(
        max_length=50,
        verbose_name=_("Language"),
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
    )
    time_zone = models.CharField(
        max_length=50,
        verbose_name=_("Time Zone"),
        choices=[(x, x) for x in pytz.common_timezones],
        default=settings.TIME_ZONE,
    )
    is_active = models.BooleanField(default=True)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Companies")

    def get_absolute_url(self):
        """Set url of the page after adding/editing/deleting object."""
        # return reverse("vendor:vendor_detail", kwargs={"pk": self.pk})

    def __str__(self):
        """Return Value."""
        return self.name


class MemberPermissionsMixin(models.Model):
    """
    Add the fields and methods necessary to support the Group and Permission
    models using the ModelBackend.
    """

    is_superuser = models.BooleanField(
        _("supermember status"),
        default=False,
        help_text=_(
            "Designates that this user has all permissions without "
            "explicitly assigning them."
        ),
    )
    groups = models.ManyToManyField(
        Group,
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="member_set",
        related_query_name="member",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="member_set",
        related_query_name="member",
    )

    class Meta:
        abstract = True


class Member(MemberPermissionsMixin):
    """
    Member Model.

    Connection between company and user with roles for perticular company.
    """

    job_title = models.CharField(max_length=200, verbose_name=_("Job title"))
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="member_user"
    )
    company = models.ForeignKey(
        Company, on_delete=models.PROTECT, related_name="member_company"
    )
    invited_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="member_invited_by"
    )
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    invitation_accepted = models.BooleanField(default=False)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Members")

    def get_absolute_url(self):
        """Set url of the page after adding/editing/deleting object."""
        return reverse("vendor:vendor_detail", kwargs={"pk": self.pk})

    def get_member_roles(self):
        """Get Member for the company from roles and permisions."""
        return get_user_roles(self)

    def __str__(self):
        """Return Value."""
        return self.user.username
