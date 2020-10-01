"""Froms related to Setting app."""
from bat.setting.models import PaymentTerms
from django import forms


class PaymentTermsForm(forms.ModelForm):
    """Payment Terms Form."""

    class Meta:
        """Defining Model and fields."""

        model = PaymentTerms
        fields = ("deposit", "on_delivery", "receiving", "payment_days")
