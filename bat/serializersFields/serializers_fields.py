from measurement.measures import Weight
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Field

from bat.company import constants


class WeightField(Field):
    def to_representation(self, value):
        ret = {"weight": value.value, "unit": value.unit}
        return ret

    def to_internal_value(self, data):
        print("\n\n\n data: ", type(data))
        try:
            if not isinstance(data, dict):
                raise Exception
            # data = eval(data)
            print("\n\n\n data: ", data)
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
