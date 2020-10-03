"""Froms related to Company app."""
from bat.company.models import Company, Member
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit
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
