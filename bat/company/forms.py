"""Froms related to Company app."""
import logging
from decimal import Decimal

from bat.company.models import (Bank, Company, CompanyPaymentTerms, HsCode,
                                Location, Member, PackingBox, Tax)
from bat.setting.models import Category
from bat.users.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Column, Layout, Row, Submit
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from invitations.utils import get_invitation_model

logger = logging.getLogger(__name__)
Invitation = get_invitation_model()


class CompanyForm(forms.ModelForm):
    """Company Form."""

    class Meta:
        """Defining Model and fields."""

        model = Company
        fields = (
            "name",
            "address1",
            "address2",
            "zip",
            "city",
            "region",
            "country",
            "abbreviation",
            "email",
            "logo",
            "phone_number",
            "organization_number",
            "currency",
            "unit_system",
            "weight_unit",
            "language",
            "time_zone",
        )


class CompanyUpdateForm(forms.ModelForm):
    """Company Update Form."""

    class Meta:
        """Defining Model and fields."""

        model = Company
        fields = (
            "name",
            "abbreviation",
            "address1",
            "address2",
            "zip",
            "city",
            "region",
            "country",
            "email",
            "logo",
            "phone_number",
            "organization_number",
            "currency",
            "unit_system",
            "weight_unit",
            "language",
            "time_zone",
        )

    def __init__(self, *args, **kwargs):
        """Init basic fields."""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {"novalidate": ""}
        self.helper.layout = Layout(
            HTML("<h5 class='mb-4'>Company Detail</h5>"),
            Row(
                Column("name", css_class="col-md-8"),
                Column("abbreviation", css_class="col-md-4"),
                css_class="form-row",
            ),
            Row(
                Column("logo", css_class="col-md-3"),
                Column("email", css_class="col-md-3"),
                Column("phone_number", css_class="col-md-3"),
                Column("organization_number", css_class="col-md-3"),
                css_class="form-row",
            ),
            HTML("<h5 class='mb-4'>Company Address</h5>"),
            Row(
                Column("address1", css_class="col-md-6"),
                Column("address2", css_class="col-md-6"),
                css_class="form-row",
            ),
            Row(
                Column("zip", css_class="col-md-3"),
                Column("city", css_class="col-md-3"),
                Column("region", css_class="col-md-3"),
                Column("country", css_class="col-md-3"),
                css_class="form-row",
            ),
            HTML("<h5 class='mb-4'>Standards and formats</h5>"),
            Row(
                Column("time_zone", css_class="col-md-3"),
                Column("language", css_class="col-md-3"),
                Column("unit_system", css_class="col-md-3"),
                Column("weight_unit", css_class="col-md-3"),
                css_class="form-row",
            ),
            HTML("<h5 class='mb-4'>Currency</h5>"),
            Row(
                Column("currency", css_class="col-md-6"), css_class="form-row"
            ),
            Submit("submit", _("Update Profile")),
        )


class MemberForm(forms.ModelForm):
    """Member Form."""

    job_title = forms.CharField(
        label=_("Job Title"), max_length=100, required=True
    )
    roles = forms.CharField(widget=forms.HiddenInput)
    permissions = forms.CharField(widget=forms.HiddenInput)
    company_id = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        """Defining Model and fields."""

        model = User
        fields = (
            "job_title",
            "first_name",
            "last_name",
            "email",
            "roles",
            "permissions",
            "company_id",
        )

    def __init__(self, *args, **kwargs):
        """
        Call the __inti__ method before assigning.

        override form field properties and same thing we will use when we
        need to create two form like create and update
        """
        super().__init__(*args, **kwargs)
        self.fields["email"].label = _("Email address")
        self.fields["email"].required = True
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    def clean(self):
        """
        Perform validation on Email and company.

        Fetch email field and perform validation like unique email in database
        or some other custom validation. you can raise error for perticular
        field from here that will be display as error on the formself.
        """
        cleaned_data = super().clean()
        company_id = cleaned_data.get("company_id")
        email = cleaned_data.get("email")
        if company_id and email:
            if Member.objects.filter(
                company_id=int(company_id), user__email=email
            ).exists():
                msg = _("User already is your staff member.")
                raise ValidationError(msg)
            else:
                invitations = Invitation.objects.filter(
                    email=email, company_detail__company_id=int(company_id)
                )
                if invitations.exists():
                    msg = _("Invitation already sent for this email.")
                    raise ValidationError(msg)


class MemberUpdateForm(forms.ModelForm):
    """Member Update Form."""

    roles = forms.CharField(widget=forms.HiddenInput)
    permissions = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        """Defining Model and fields."""

        model = Member
        fields = ("job_title", "roles", "permissions")


class AccountSetupForm(forms.ModelForm):
    """Member Form."""

    class Meta:
        """Defining Model and fields."""

        model = Company
        fields = (
            "name",
            "address1",
            "address2",
            "zip",
            "city",
            "region",
            "country",
            "abbreviation",
            "email",
            "phone_number",
        )

    def __init__(self, *args, **kwargs):
        """Init basic fields."""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {"novalidate": ""}
        self.helper.layout = Layout(
            Row(
                Column("name", css_class="col-md-8"),
                Column("abbreviation", css_class="col-md-4"),
                css_class="form-row",
            ),
            "address1",
            "address2",
            Row(
                Column("zip", css_class="col-md-4"),
                Column("city", css_class="col-md-4"),
                Column("region", css_class="col-md-4"),
                css_class="form-row",
            ),
            "country",
            Row(
                Column("email", css_class="col-md-6"),
                Column("phone_number", css_class="col-md-6"),
                css_class="form-row",
            ),
            Submit("submit", _("COMPLETE REGISTERATION")),
        )


class VendorInviteForm(forms.ModelForm):
    """Vendor Invitation Form."""

    vendor_type = forms.ChoiceField(label=_("Vendor Type"), required=True)
    vendor_name = forms.CharField(
        label=_("Vendor Name"), max_length=100, required=True
    )
    job_title = forms.CharField(
        label=_("Job Title"), max_length=100, required=True
    )

    class Meta:
        """Defining Model and fields."""

        model = User
        fields = (
            "vendor_type",
            "vendor_name",
            "job_title",
            "first_name",
            "last_name",
            "email",
        )

    def __init__(self, *args, **kwargs):
        """
        Call the __inti__ method before assigning.

        override form field properties and same thing we will use when we
        need to create two form like create and update
        """
        super().__init__(*args, **kwargs)
        categories = Category.objects.filter(parent__name__exact=_("Vendors"))
        self.fields["email"].label = _("Email address")
        self.fields["email"].required = True
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["vendor_type"].choices = (
            (category.pk, category.name) for category in categories
        )

    def clean(self):
        """
        Perform validation on Email and company.

        Fetch email field and perform validation like unique email in database
        or some other custom validation. you can raise error for perticular
        field from here that will be display as error on the formself.
        """
        cleaned_data = super().clean()
        vendor_type = cleaned_data.get("vendor_type")
        vendor_name = cleaned_data.get("vendor_name")
        email = cleaned_data.get("email")
        if vendor_type and vendor_name and email:
            invitations = Invitation.objects.filter(
                email=email, company_detail__company_name__iexact=vendor_name
            )
            if invitations.exists():
                msg = _("Invitation already sent for this vendor and email.")
                raise ValidationError(msg)


class CompanyPaymentTermsForm(forms.ModelForm):
    """Payment Terms Form."""

    class Meta:
        """Defining Model and fields."""

        model = CompanyPaymentTerms
        fields = ("deposit", "on_delivery", "receiving", "payment_days")

    def __init__(self, *args, **kwargs):
        """Init basic fields."""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {"novalidate": ""}
        self.helper.layout = Layout(
            "deposit",
            "on_delivery",
            "receiving",
            "payment_days",
            Submit("submit", _("Save PaymentTerms")),
        )

    def clean(self):
        """
        Perform validation on Email and company.

        Fetch email field and perform validation like unique email in database
        or some other custom validation. you can raise error for perticular
        field from here that will be display as error on the formself.
        """
        cleaned_data = super().clean()
        deposit = cleaned_data.get("deposit")
        on_delivery = cleaned_data.get("on_delivery")
        receiving = cleaned_data.get("receiving")
        if deposit and on_delivery and receiving:
            total = (
                Decimal(deposit) + Decimal(on_delivery) + Decimal(receiving)
            )
            if total > 100:
                msg = _(
                    "Total amount can't be more than 100%. Please check again."
                )
                raise ValidationError(msg)


class BankForm(forms.ModelForm):
    """Bank Form."""

    class Meta:
        """Defining Model and fields."""

        model = Bank
        fields = (
            "name",
            "benificary",
            "account_number",
            "iban",
            "swift_code",
            "address1",
            "address2",
            "zip",
            "city",
            "region",
            "country",
            "currency",
        )

    def __init__(self, *args, **kwargs):
        """Init basic fields."""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {"novalidate": ""}
        self.helper.layout = Layout(
            Row(
                Column("name", css_class="col-md-6"),
                Column("benificary", css_class="col-md-6"),
                css_class="form-row",
            ),
            Row(
                Column("account_number", css_class="col-md-6"),
                Column("iban", css_class="col-md-3"),
                Column("swift_code", css_class="col-md-3"),
                css_class="form-row",
            ),
            "address1",
            "address2",
            Row(
                Column("zip", css_class="col-md-4"),
                Column("city", css_class="col-md-4"),
                Column("region", css_class="col-md-4"),
                css_class="form-row",
            ),
            "country",
            "currency",
            Submit("submit", _("Add Bank")),
        )


class LocationForm(forms.ModelForm):
    """Location Form."""

    class Meta:
        """Defining Model and fields."""

        model = Location
        fields = (
            "name",
            "address1",
            "address2",
            "zip",
            "city",
            "region",
            "country",
        )

    def __init__(self, *args, **kwargs):
        """Init basic fields."""
        super().__init__(*args, **kwargs)
        self.fields["address1"].required = True
        self.fields["zip"].required = True
        self.fields["city"].required = True
        self.helper = FormHelper()
        self.helper.attrs = {"novalidate": ""}
        self.helper.layout = Layout(
            "name",
            "address1",
            "address2",
            Row(
                Column("zip", css_class="col-md-4"),
                Column("city", css_class="col-md-4"),
                Column("region", css_class="col-md-4"),
                css_class="form-row",
            ),
            "country",
            Submit("submit", _("Add Location")),
        )


class PackingBoxForm(forms.ModelForm):
    """Packing Box Form."""

    class Meta:
        """Defining Model and fields."""

        model = PackingBox
        fields = ("name", "length", "width", "depth", "length_unit", "weight")

    def __init__(self, *args, **kwargs):
        """Init basic fields."""
        super().__init__(*args, **kwargs)
        self.fields["weight"].widget.attrs = {"class": "form-control"}
        self.helper = FormHelper()
        self.helper.attrs = {"novalidate": ""}
        self.helper.layout = Layout(
            "name",
            Row(
                Column("length", css_class="col-md-3"),
                Column("width", css_class="col-md-3"),
                Column("depth", css_class="col-md-3"),
                Column("length_unit", css_class="col-md-3"),
            ),
            "weight",
            Submit("submit", _("Add Packing Box")),
        )


class HsCodeForm(forms.ModelForm):
    """HS Code Form."""

    class Meta:
        """Defining Model and fields."""

        model = HsCode
        fields = ("hscode", "material", "use")

    def __init__(self, *args, **kwargs):
        """Init basic fields."""
        super().__init__(*args, **kwargs)
        self.fields["material"].required = True
        self.fields["use"].required = True
        self.helper = FormHelper()
        self.helper.attrs = {"novalidate": ""}
        self.helper.layout = Layout(
            "hscode", "material", "use", Submit("submit", _("Add HS Code"))
        )


class TaxForm(forms.ModelForm):
    """Tax Form."""

    class Meta:
        """Defining Model and fields."""

        model = Tax
        fields = ("from_country", "to_country", "custom_duty", "vat")

    def __init__(self, *args, **kwargs):
        """Init basic fields."""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {"novalidate": ""}
        self.helper.layout = Layout(
            Row(
                Column("from_country", css_class="col-md-6"),
                Column("to_country", css_class="col-md-6"),
            ),
            Row(
                Column("custom_duty", css_class="col-md-6"),
                Column("vat", css_class="col-md-6"),
            ),
            Submit("submit", _("Add Tax")),
        )
