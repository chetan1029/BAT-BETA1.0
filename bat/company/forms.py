"""Froms related to Company app."""
from bat.company.models import Company, Member
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Column, Layout, Row, Submit
from django import forms
from django.utils.translation import ugettext_lazy as _


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

    class Meta:
        """Defining Model and fields."""

        model = Member
        fields = ("job_title",)


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
