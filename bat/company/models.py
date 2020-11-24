"""Model classes for company."""
import logging
import os

import pytz
from defender.models import AccessAttempt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from django_measurement.models import MeasurementField
from djmoney.models.fields import MoneyField
from djmoney.settings import CURRENCY_CHOICES
from measurement.measures import Weight
from multiselectfield import MultiSelectField
from rolepermissions.checkers import has_permission
from rolepermissions.roles import get_user_roles

from bat.company.constants import *
from bat.globalprop.validator import validator
from bat.setting.models import Category, Status

User = get_user_model()
logger = logging.getLogger(__name__)


STATUS_DRAFT = 4


def get_member_from_request(request):
    """
    get member from request bye resolving it
    """
    kwargs = request.resolver_match.kwargs
    company_pk = kwargs.get("company_pk", kwargs.get("pk", None))
    member = get_object_or_404(
        Member, company__id=company_pk, user=request.user.id
    )
    return member


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

    def __str__(self):
        """Return Value."""
        return str(self.id) + " - " + self.name

    @staticmethod
    def has_read_permission(request):
        return True

    def has_object_read_permission(self, request):
        return True

    @staticmethod
    def has_update_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "update_company_profile")

    def has_object_update_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "update_company_profile")

    @staticmethod
    def has_create_permission(request):
        return True

    def has_object_create_permission(self, request):
        return True


class CompanyType(models.Model):
    """
    Company Type Model.

    Model to store information for companies relations.
    """

    partner = models.ForeignKey(
        Company, on_delete=models.PROTECT, related_name="companytype_partner"
    )
    company = models.ForeignKey(
        Company, on_delete=models.PROTECT, related_name="companytype_company"
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="companytype_company"
    )
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Types")

    def get_absolute_url(self):
        """Set url of the page after adding/editing/deleting object."""
        # return reverse("vendor:vendor_detail", kwargs={"pk": self.pk})

    def __str__(self):
        """Return Value."""
        return self.company.name


class MemberPermissionsMixin(models.Model):
    """
    Permissions mixing.

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
        """Meta detail."""

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
    last_login = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Members")

    def get_absolute_url(self):
        """Set url of the page after adding/editing/deleting object."""
        return reverse("company:member_detail", kwargs={"pk": self.pk})

    def get_member_roles(self):
        """Get Member for the company from roles and permisions."""
        return get_user_roles(self)

    def update_member_last_login(self):
        """Update member last login for his profile."""
        self.last_login = timezone.now()
        self.save()
        return ""

    def access_attempts(self):
        """Get Member last 10 login attempts."""
        access_attempts = AccessAttempt.objects.filter(
            username=self.user.username
        ).order_by("-attempt_time")[:10]
        return access_attempts

    def __str__(self):
        """Return Value."""
        return (
            self.user.username
            + " - "
            + self.company.name
            + " - "
            + str(self.company.id)
        )

    @staticmethod
    def has_read_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_staff_member")

    def has_object_read_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_staff_member")

    @staticmethod
    def has_list_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_staff_member")

    def has_object_list_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_staff_member")

    @staticmethod
    def has_destroy_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_staff_member")

    def has_object_destroy_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_staff_member")

    @staticmethod
    def has_update_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "change_staff_member")

    def has_object_update_permission(self, request):
        member = get_member_from_request(request)
        if not self.is_active:
            return False
        return has_permission(member, "change_staff_member")

    @staticmethod
    def has_archive_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_staff_member")

    def has_object_archive_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_staff_member")

    @staticmethod
    def has_restore_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_staff_member")

    def has_object_restore_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_staff_member")


class CompanyPaymentTerms(models.Model):
    """
    Company Payment Terms Model.

    Model for Vendor Payment Terms.
    """

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    title = models.CharField(
        max_length=200, verbose_name=_("PaymentTerms Title")
    )
    deposit = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Deposit (in %)"),
        default=0,
    )
    on_delivery = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Payment on delivery (in %)"),
        default=0,
    )
    receiving = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Receiving (in %)"),
        default=0,
    )
    remaining = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("Remaining (in %)")
    )
    payment_days = models.PositiveIntegerField(
        verbose_name=_("Payment Days (in days)"), default=0
    )
    is_active = models.BooleanField(default=True)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("PaymentTerms")

    def get_absolute_url(self):
        """Set url of the page after adding/editing/deleting object."""
        return reverse("company:settingspaymentterms_list")

    def __str__(self):
        """Return Value."""
        return self.title

    @staticmethod
    def has_read_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_payment_terms")

    def has_object_read_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_payment_terms")

    @staticmethod
    def has_list_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_payment_terms")

    def has_object_list_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_payment_terms")

    @staticmethod
    def has_create_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "add_payment_terms")

    def has_object_create_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "add_payment_terms")

    @staticmethod
    def has_destroy_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_payment_terms")

    def has_object_destroy_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_payment_terms")

    @staticmethod
    def has_update_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "change_payment_terms")

    def has_object_update_permission(self, request):
        member = get_member_from_request(request)
        if not self.is_active:
            return False
        return has_permission(member, "change_payment_terms")

    @staticmethod
    def has_archive_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_payment_terms")

    def has_object_archive_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_payment_terms")

    @staticmethod
    def has_restore_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_payment_terms")

    def has_object_restore_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_payment_terms")


class Bank(Address):
    """
    Bank Model.

    Model to store information for bank detail.
    """

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, verbose_name=_("Bank Name"))
    benificary = models.CharField(
        max_length=100, verbose_name=_("Benificary Name")
    )
    account_number = models.CharField(
        max_length=100, verbose_name=_("Account Number")
    )
    iban = models.CharField(max_length=100, verbose_name=_("Iban number"))
    swift_code = models.CharField(max_length=100, verbose_name=_("Swift Code"))
    currency = MultiSelectField(
        max_length=200, choices=CURRENCY_CHOICES, verbose_name=_("Currency")
    )
    is_active = models.BooleanField(default=True)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Banks")

    def get_absolute_url(self):
        """Set url of the page after adding/editing/deleting object."""
        return reverse("company:settingsbank_detail", kwargs={"pk": self.pk})

    def __str__(self):
        """Return Value."""
        return self.name

    @staticmethod
    def has_read_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_company_banks")

    def has_object_read_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_company_banks")

    @staticmethod
    def has_list_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_company_banks")

    def has_object_list_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_company_banks")

    @staticmethod
    def has_create_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "add_company_banks")

    def has_object_create_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "add_company_banks")

    @staticmethod
    def has_destroy_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_company_banks")

    def has_object_destroy_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_company_banks")

    @staticmethod
    def has_update_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "change_company_banks")

    def has_object_update_permission(self, request):
        member = get_member_from_request(request)
        if not self.is_active:
            return False
        return has_permission(member, "change_company_banks")

    @staticmethod
    def has_archive_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_company_banks")

    def has_object_archive_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_company_banks")

    @staticmethod
    def has_restore_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_company_banks")

    def has_object_restore_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_company_banks")


class Location(Address):
    """
    Location Model.

    Model to store information for Warehouse Location detail.
    """

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, verbose_name=_("Location Name"))
    is_active = models.BooleanField(default=True)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Locations")

    def get_absolute_url(self):
        """Set url of the page after adding/editing/deleting object."""
        return reverse("company:settingslocation_list")

    def __str__(self):
        """Return Value."""
        return self.name

    @staticmethod
    def has_read_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_company_locations")

    def has_object_read_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_company_locations")

    @staticmethod
    def has_list_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_company_locations")

    def has_object_list_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_company_locations")

    @staticmethod
    def has_create_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "add_company_locations")

    def has_object_create_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "add_company_locations")

    @staticmethod
    def has_destroy_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_company_locations")

    def has_object_destroy_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_company_locations")

    @staticmethod
    def has_update_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "change_company_locations")

    def has_object_update_permission(self, request):
        member = get_member_from_request(request)
        if not self.is_active:
            return False
        return has_permission(member, "change_company_locations")

    @staticmethod
    def has_archive_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_company_locations")

    def has_object_archive_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_company_locations")

    @staticmethod
    def has_restore_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_company_locations")

    def has_object_restore_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_company_locations")


class PackingBox(models.Model):
    """
    Packing Box Model.

    Model to store information for Packing Box Details.
    """

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, verbose_name=_("Packing Name"))
    length = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("Length")
    )
    width = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("Width")
    )
    depth = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("Depth")
    )
    cbm = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("Cubic Metres")
    )
    length_unit = models.CharField(
        max_length=20,
        choices=LENGTH_UNIT_TYPE,
        default=CM,
        verbose_name=_("Length Unit"),
    )
    weight = MeasurementField(
        measurement=Weight,
        unit_choices=(("g", "g"), ("kg", "kg"), ("oz", "oz"), ("lb", "lb")),
    )
    is_active = models.BooleanField(default=True)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Packing Boxes")

    def get_absolute_url(self):
        """Set url of the page after adding/editing/deleting object."""
        return reverse("company:settingspackingbox_list")

    def __str__(self):
        """Return Value."""
        return self.name

    @staticmethod
    def has_read_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_packing_box")

    def has_object_read_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_packing_box")

    @staticmethod
    def has_list_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_packing_box")

    def has_object_list_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_packing_box")

    @staticmethod
    def has_create_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "add_packing_box")

    def has_object_create_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "add_packing_box")

    @staticmethod
    def has_destroy_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_packing_box")

    def has_object_destroy_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_packing_box")

    @staticmethod
    def has_update_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "change_packing_box")

    def has_object_update_permission(self, request):
        member = get_member_from_request(request)
        if not self.is_active:
            return False
        return has_permission(member, "change_packing_box")

    @staticmethod
    def has_archive_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_packing_box")

    def has_object_archive_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_packing_box")

    @staticmethod
    def has_restore_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_packing_box")

    def has_object_restore_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_packing_box")


class HsCode(models.Model):
    """
    HS Code for products.

    Mainly use for the custom clearance.
    """

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    hscode = models.CharField(max_length=200, verbose_name=_("HS Code"))
    material = models.CharField(
        max_length=500, verbose_name=_("Product Material"), blank=True
    )
    use = models.CharField(
        max_length=500, verbose_name=_("Product Use"), blank=True
    )
    is_active = models.BooleanField(default=True)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company HSCodes")

    def get_absolute_url(self):
        """Set url of the page after adding/editing/deleting object."""
        return reverse("company:settingshscode_list")

    def __str__(self):
        """Return Value."""
        return self.hscode

    @staticmethod
    def has_read_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_hscode")

    def has_object_read_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_hscode")

    @staticmethod
    def has_list_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_hscode")

    def has_object_list_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_hscode")

    @staticmethod
    def has_create_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "add_hscode")

    def has_object_create_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "add_hscode")

    @staticmethod
    def has_destroy_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_hscode")

    def has_object_destroy_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_hscode")

    @staticmethod
    def has_update_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "change_hscode")

    def has_object_update_permission(self, request):
        member = get_member_from_request(request)
        if not self.is_active:
            return False
        return has_permission(member, "change_hscode")

    @staticmethod
    def has_archive_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_hscode")

    def has_object_archive_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_hscode")

    @staticmethod
    def has_restore_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_hscode")

    def has_object_restore_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_hscode")


class Tax(models.Model):
    """
    Tax Detail for company.

    Using this table to store tax/vat detail between countries so we can use
    them while calculations and price list.
    """

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    from_country = CountryField()
    to_country = CountryField()
    custom_duty = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("Custom Duty")
    )
    vat = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("VAT")
    )
    is_active = models.BooleanField(default=True)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Taxes")

    def get_absolute_url(self):
        """Set url of the page after adding/editing/deleting object."""
        return reverse("company:settingstax_list")

    def __str__(self):
        """Return Value."""
        return str(self.from_country) + "-" + str(self.to_country)

    @staticmethod
    def has_read_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_taxes")

    def has_object_read_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_taxes")

    @staticmethod
    def has_list_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_taxes")

    def has_object_list_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_taxes")

    @staticmethod
    def has_create_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "add_taxes")

    def has_object_create_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "add_taxes")

    @staticmethod
    def has_destroy_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_taxes")

    def has_object_destroy_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_taxes")

    @staticmethod
    def has_update_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "change_taxes")

    def has_object_update_permission(self, request):
        member = get_member_from_request(request)
        if not self.is_active:
            return False
        return has_permission(member, "change_taxes")

    @staticmethod
    def has_archive_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_taxes")

    def has_object_archive_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_taxes")

    @staticmethod
    def has_restore_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_taxes")

    def has_object_restore_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_taxes")


class CompanyContract(models.Model):
    """
    Company Contract.

    Agreement contract between two companies signed by their members. including
    company -> vendor, company -> saleschannel, company -> logistics etc.
    It can be multiple step contracts that first intiated by the company
    followed by vendor to make some updates and sign the generated file and
    upload it again for approval from the company.
    We also have to use a plugin to generate PDF contract file when contract is
    intiated and updated.
    """

    companytype = models.ForeignKey(CompanyType, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, verbose_name=_("Contract Title"))
    file = models.CharField(max_length=500, verbose_name=_("Contract File"))
    note = models.TextField(blank=True)
    partner_member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="partner_member"
    )
    company_member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="company_member"
    )
    paymentterms = models.ForeignKey(
        CompanyPaymentTerms, on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=False)
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, default=STATUS_DRAFT
    )
    # We will add status Contract as parent then add other status for draft and approved etc then make it active.
    extra_data = HStoreField(null=True, blank=True)
    # this is a golbal contract that have golbal data field but we are going to have some custom fields
    # like inventory rotations, margins etc for the sales channels that we will save in extra_data.
    # Extra field for Sales Channel contracts :
    # (inventory_rotation, rotation_percentage, retail_margin, distributor_margin, air_freight, sea_freight, air_misc, sea_misc)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Contracts")

    def __str__(self):
        """Return Value."""
        return (
            str(self.company_member.company.name)
            + "-"
            + str(self.partner_member.company.name)
        )


class CompanyCredential(models.Model):
    """
    Company Credential.

    We are going to use this option for the API Credentials for Amazon and
    shopify like stores.
    """

    companytype = models.ForeignKey(CompanyType, on_delete=models.CASCADE)
    region = models.CharField(max_length=300, blank=True)
    seller_id = models.CharField(max_length=300, blank=True)
    auth_token = models.CharField(max_length=300, blank=True)
    access_key = models.CharField(max_length=300, blank=True)
    secret_key = models.CharField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Credentials")

    def __str__(self):
        """Return Value."""
        return str(self.region)


class ComponentMe(models.Model):
    """
    Component Manufacturer Expectation.

    Component manufacturer expectation for the components.
    """

    from bat.product.models import Product

    version = models.DecimalField(max_digits=5, decimal_places=1)
    revision_history = models.TextField(blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    companytype = models.ForeignKey(CompanyType, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Component MEs")

    def __str__(self):
        """Return Value."""
        return self.product.title


class ComponentMeFile(models.Model):
    """
    Component Manufacturer Expectation Files.

    Component manufacturer expectation file for the components.
    """

    componentme = models.ForeignKey(ComponentMe, on_delete=models.CASCADE)
    type = models.CharField(max_length=100)
    # for type we will show typeahead with suggestion and new input accept. values will be AQL,SOP,MD,BOM,IPQC
    version = models.DecimalField(max_digits=5, decimal_places=1)
    revision_history = models.TextField(blank=True)
    file = models.CharField(max_length=500, verbose_name=_("ME File"))
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, default=STATUS_DRAFT
    )
    # We will add status Contract as parent then add other status for draft and approved etc then make it active.
    is_active = models.BooleanField(default=False)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Component ME Files")

    def __str__(self):
        """Return Value."""
        return self.type


class ComponentGoldenSample(models.Model):
    """
    Component Golden Sample.

    Component Golden sample will be for the final component ME and sign by both
    company and vendor before finalize.
    """

    componentme = models.ForeignKey(ComponentMe, on_delete=models.CASCADE)
    batch_id = models.CharField(max_length=100)
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, default=STATUS_DRAFT
    )
    is_active = models.BooleanField(default=False)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Component Golden Samples")

    def __str__(self):
        """Return Value."""
        return self.batch_id


class ComponentGoldenSampleFiles(models.Model):
    """
    Component Golden Sample Files.

    Component Golden sample files.
    """

    componentgoldensample = models.ForeignKey(
        ComponentGoldenSample, on_delete=models.CASCADE
    )
    file = models.CharField(max_length=500)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Component Golden Sample Files")

    def __str__(self):
        """Return Value."""
        return self.componentgoldensample.batch_id


class ComponentPrice(models.Model):
    """
    Component Golden Sample.

    Component Golden sample will be for the final component ME and sign by both
    company and vendor before finalize.
    """

    componentgoldensample = models.ForeignKey(
        ComponentGoldenSample, on_delete=models.CASCADE
    )
    price = MoneyField(max_digits=14, decimal_places=2, default_currency="USD")
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=False)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Component Golden Samples")

    def __str__(self):
        """Return Value."""
        return self.batch_id


class CompanyProduct(models.Model):
    """
    COmpany Product Model.

    We will use this model to save all the products related to company like
    vendor and sales channel products.
    """

    from bat.product.models import Product

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    companytype = models.ForeignKey(CompanyType, on_delete=models.CASCADE)
    title = models.CharField(verbose_name=_("Title"), max_length=500)
    sku = models.CharField(verbose_name=_("SKU"), max_length=200, blank=True)
    ean = models.CharField(verbose_name=_("EAN"), max_length=200, blank=True)
    asin = models.CharField(verbose_name=_("ASIN"), max_length=200, blank=True)
    model_number = models.CharField(
        max_length=200, blank=True, verbose_name=_("Model Number")
    )
    manufacturer_part_number = models.CharField(
        max_length=200, blank=True, verbose_name=_("Manufacturer Part Number")
    )
    price = MoneyField(max_digits=14, decimal_places=2, default_currency="USD")
    is_active = models.BooleanField(default=True)
    extra_data = HStoreField(null=True, blank=True)
    # we add image urls, parent_id, variation_type and parentage etc
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Component Products")

    def __str__(self):
        """Return Value."""
        return self.title


class CompanyOrder(models.Model):
    """
    Company order Model.

    Order place for vendors and by sales channel will be display here.
    """

    batch_id = models.CharField(max_length=100)
    order_date = models.DateTimeField(default=timezone.now)
    delivery_date = models.DateTimeField(blank=True, null=True)
    companytype = models.ForeignKey(CompanyType, on_delete=models.CASCADE)
    buyer_member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="buyer_member"
    )
    seller_member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="seller_member"
    )
    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        verbose_name="Select Status",
        default=STATUS_DRAFT,
    )
    sub_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    vat_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    tax_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    total_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    return_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    deposit_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    quantity = models.PositiveIntegerField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    extra_data = HStoreField(null=True, blank=True)
    # we will add is_reverse_charged, is_return, refer_order_id(if return) etc
    # to extra_data
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Component Orders")

    def __str__(self):
        """Return Value."""
        return self.batch_id


class CompanyOrderProduct(models.Model):
    """
    Company order product Model.

    Order place for vendors and by sales channel will be display here.
    """

    companyorder = models.ForeignKey(CompanyOrder, on_delete=models.CASCADE)
    companyproduct = models.ForeignKey(
        CompanyProduct, on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField()
    shipped_quantity = models.PositiveIntegerField(default=0)
    remaining_quantity = models.PositiveIntegerField(default=0)
    price = MoneyField(max_digits=14, decimal_places=2, default_currency="USD")
    amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    companypaymentterms = models.ForeignKey(
        CompanyPaymentTerms, on_delete=models.CASCADE
    )
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Component Order Products")

    def __str__(self):
        """Return Value."""
        return self.batch_id


class CompanyOrderFile(models.Model):
    """
    Company Order Files.

    Company Order file for the orders.
    """

    companyorder = models.ForeignKey(CompanyOrder, on_delete=models.CASCADE)
    type = models.CharField(max_length=100)
    # for type we will show typeahead with suggestion and new input accept. values will be AQL,SOP,MD,BOM,IPQC
    file = models.CharField(max_length=500, verbose_name=_("Order File"))
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, default=STATUS_DRAFT
    )
    # We will add status Contract as parent then add other status for draft and approved etc then make it active.
    note = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Order Files")

    def __str__(self):
        """Return Value."""
        return self.type


class CompanyOrderDelivery(models.Model):
    """
    Company Order Delivery.

    Company Order Delivery for the orders.
    """

    batch_id = models.CharField(max_length=100)
    companyorder = models.ForeignKey(CompanyOrder, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    delivery_date = models.DateTimeField(default=timezone.now)
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, default=STATUS_DRAFT
    )
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Order Delivery")

    def __str__(self):
        """Return Value."""
        return self.batch_id


class CompanyOrderDeliveryProduct(models.Model):
    """
    Company Order Delivery Products.

    Company Order Delivery Products for the orders.
    """

    companyorderdelivery = models.ForeignKey(
        CompanyOrderDelivery, on_delete=models.CASCADE
    )
    companyorderproduct = models.ForeignKey(
        CompanyOrderProduct, on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField()
    amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Order Delivery Products")

    def __str__(self):
        """Return Value."""
        return self.companyorderdelivery.batch_id


class CompanyOrderDeliveryTestReport(models.Model):
    """
    Company Order Delivery Test Report.

    Company Order Delivery test report by the inspector member.
    """

    companyorderdelivery = models.ForeignKey(
        CompanyOrderDelivery, on_delete=models.CASCADE
    )
    inspector = models.ForeignKey(Member, on_delete=models.CASCADE)
    file = models.CharField(max_length=500, verbose_name=_("Test Report File"))
    note = models.TextField(blank=True, null=True)
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, default=STATUS_DRAFT
    )
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Order Delivery Test reports")

    def __str__(self):
        """Return Value."""
        return self.companyorderdelivery.batch_id


class CompanyOrderPayment(models.Model):
    """
    Company Order Payment.

    Company Order Payment that we will save via Order delivery.
    """

    companyorderdelivery = models.ForeignKey(
        CompanyOrderDelivery, on_delete=models.CASCADE
    )
    type = models.CharField(max_length=100)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    invoice_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    paid_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", default=0
    )
    adjustment_type = models.CharField(max_length=100, blank=True)
    adjustment_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    adjustment_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", default=0
    )
    payment_date = models.DateTimeField(blank=True, null=True)
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, default=STATUS_DRAFT
    )
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Order Payments")

    def __str__(self):
        """Return Value."""
        return self.companyorderdelivery.batch_id


class CompanyOrderPaymentPaid(models.Model):
    """
    Company Order Payment Paid.

    Company Order Payment paid that we will save via Order delivery.
    """

    companyorderpayment = models.ForeignKey(
        CompanyOrderPayment, on_delete=models.CASCADE
    )
    payment_id = models.CharField(max_length=200, blank=True)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    invoice_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    paid_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", default=0
    )
    pi_file = models.CharField(max_length=200, blank=True)
    receipt_file = models.CharField(max_length=200, blank=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, default=STATUS_DRAFT
    )
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Order Payments")

    def __str__(self):
        """Return Value."""
        return self.companyorderpayment.companyorderdelivery.batch_id


class CompanyOrderCase(models.Model):
    """
    Company Order Case.

    Company Order Case to report any defected or lost units by vendors.
    """

    companyorder = models.ForeignKey(CompanyOrder, on_delete=models.CASCADE)
    file = models.CharField(max_length=500, verbose_name=_("Test Report File"))
    note = models.TextField(blank=True, null=True)
    importance = models.CharField(
        max_length=50,
        choices=IMPORTANCE_CHOICES,
        verbose_name=_("Importance"),
        default=BASIC,
    )
    units_affected = models.PositiveIntegerField()
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, default=STATUS_DRAFT
    )
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Order Cases")

    def __str__(self):
        """Return Value."""
        return self.companyorder.batch_id


class CompanyOrderInspection(models.Model):
    """
    Company Order Inspection.

    An Inspector can do inspect on order and report it on the main order.
    """

    companyorder = models.ForeignKey(CompanyOrder, on_delete=models.CASCADE)
    inspector = models.ForeignKey(Member, on_delete=models.CASCADE)
    inspection_date = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True, null=True)
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, default=STATUS_DRAFT
    )
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Order Inspection")

    def __str__(self):
        """Return Value."""
        return self.companyorder.batch_id


class CompanyOrderInspectionFile(models.Model):
    """
    Company Order Inspection File.

    Inspection Files.
    """

    companyorderinspection = models.ForeignKey(
        CompanyOrderInspection, on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200, blank=True)
    inspection_date = models.DateTimeField(default=timezone.now)
    file = models.CharField(max_length=500, verbose_name=_("Inspection File"))
    is_active = models.BooleanField(default=False)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Order Inspection Files")

    def __str__(self):
        """Return Value."""
        return self.companyorderinspection.companyorder.batch_id


class CompanyInventory(models.Model):
    """
    Company Inventory.

    Inventory tracking for vendors, sales channel and online plus warehouses.
    """

    companyproduct = models.ForeignKey(
        CompanyProduct, on_delete=models.CASCADE
    )
    date = models.DateField(default=timezone.now)
    quantity = models.IntegerField(default=0)
    weeks_of_supply = models.IntegerField(default=0)
    ytd_quantity_sold = models.IntegerField(default=0)
    week_average_quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=False)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Inventory")

    def __str__(self):
        """Return Value."""
        return self.companyproduct.title


class CompanyInventoryDetail(models.Model):
    """
    Company Inventory Detail.

    Detail about inventory like available, in stock, picked up etc.
    """

    companyinventory = models.ForeignKey(
        CompanyInventory, on_delete=models.CASCADE
    )
    type = models.CharField(max_length=100)
    # Suggestion for the type will be In stock, Picked up, In transit, Ready to ship,
    # Shipped, Trasnfer, Lost , Damaged, Total.
    quantity = models.IntegerField(default=0)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Inventory Details")

    def __str__(self):
        """Return Value."""
        return self.companyinventory.companyproduct.title


class CompanyInventoryPrediction(models.Model):
    """
    Company Inventory Predicationa.

    Inventory Predication for products and components. we will use this model
    to crunch numbers and store data directly. so no need to create forms like
    add/edit etc
    """

    companyproduct = models.ForeignKey(
        CompanyProduct, on_delete=models.CASCADE
    )
    week = models.PositiveIntegerField()
    date_start = models.DateField()
    date_end = models.DateField()
    year = models.PositiveIntegerField()
    instock = models.PositiveIntegerField(default=0)
    quantity_required = models.PositiveIntegerField(default=0)
    adjusted_quantity = models.PositiveIntegerField(default=0)
    total_quantity_required = models.PositiveIntegerField(default=0)
    incoming_quantity = models.PositiveIntegerField(default=0)
    outgoing_quantity = models.PositiveIntegerField(default=0)
    weeks_of_supply = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=False)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Company Inventory")

    def __str__(self):
        """Return Value."""
        return self.companyproduct.title
