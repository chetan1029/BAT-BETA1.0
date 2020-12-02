from decimal import Decimal

from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Field, ChoiceField, JSONField

from django_countries import countries
from measurement.measures import Weight
from djmoney.money import Money

from bat.company import constants

from bat.globalconstants.constants import CURRENCY_CODE_CHOICES


class WeightField(JSONField):
    def to_representation(self, value):
        '''
        represent weight object to json data
        '''
        ret = {"value": value.value, "unit": value.unit}
        return ret

    def to_internal_value(self, data):
        '''
        generate weight object from json data
        '''
        if not isinstance(data, dict):
            raise ValidationError(
                "%s is not a valid %s" % (data, "format")
            )
        value = data.get("value", None)
        unit = data.get("unit", None)
        if value is None:
            raise ValidationError(
                {"value": _("value is required")})
        try:
            Decimal(value)
        except Exception:
            raise ValidationError(
                {"value": _("value is not a valid decimal")})

        if unit is None:
            raise ValidationError(
                {"unit": _("unit is required")})

        kwargs = {unit: value}
        if unit in constants.WEIGHT_UNIT_TYPE_LIST:
            return Weight(**kwargs)
        else:
            raise ValidationError(
                {"unit": _(f"{unit} is not a valid unit")})


class CountrySerializerField(ChoiceField):
    def __init__(self, **kwargs):
        choices = list(countries)
        super().__init__(choices=choices, **kwargs)

    def to_representation(self, value):
        """
        give code and name of Country.
        """
        if isinstance(value, str):
            return value
        return value.code + " - " + value.name


class TagField(Field):
    def to_representation(self, value):
        """
        Convert from tags to csv string of tag names.
        """
        if not isinstance(value, str):
            value = ",".join(list(value.names()))
        return value

    def to_internal_value(self, data):
        """
        Convert from csv string of tag names to list of tags.
        """
        return data.split(",")


class MoneySerializerField(JSONField):

    def to_representation(self, value):
        '''
        represent money object to json data
        '''
        ret = {"amount": value.amount, "currency": value.currency.code}
        return ret

    def to_internal_value(self, data):
        '''
        generate money object from json data
        '''
        if not isinstance(data, dict):
            raise ValidationError(
                "%s is not a valid %s" % (data, "format")
            )
        amount = data.get("amount", None)
        currency = data.get("currency", None)
        if amount is None:
            raise ValidationError(
                {"amount": _("amount is required")})
        try:
            Decimal(amount)
        except Exception:
            raise ValidationError(
                {"amount": _("amount is not a valid decimal")})

        if currency is None:
            raise ValidationError(
                {"currency": _("currency is required")})

        if currency in CURRENCY_CODE_CHOICES:
            return Money(amount, currency)
        else:
            raise ValidationError(
                {"currency": _(f"{currency} is not a valid currency")})
