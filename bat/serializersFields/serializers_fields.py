from decimal import Decimal

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Field, ChoiceField

from django_countries import countries
from measurement.measures import Weight

from bat.company import constants


class WeightField(Field):
    def to_representation(self, value):
        ret = {"weight": value.value, "unit": value.unit}
        return ret

    def to_internal_value(self, data):
        try:
            if not isinstance(data, dict):
                raise Exception
            # data = eval(data)
            unit = data["unit"]
            value = data["weight"]
            kwargs = {unit: value}
            if unit in constants.WEIGHT_UNIT_TYPE_LIST:
                return Weight(**kwargs)
            else:
                raise ValidationError("%s is not a valid %s" % (data, "Unit"))
        except Exception:
            if data:
                raise ValidationError(
                    "%s is not a valid %s" % (data, "format")
                )
            else:
                if self.required:
                    raise ValidationError("%s is %s" % ("weight", "required"))
                else:
                    # TODO
                    return data


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
