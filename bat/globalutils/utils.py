from decimal import Decimal


def set_field_errors(list_of_errors, field, error_msg):
    errors = list_of_errors.copy()
    if field in list_of_errors:
        errors[field].append(error_msg)
    else:
        errors[field] = [error_msg]
    return errors


def get_cbm(length, width, depth, unit):
    """Convert measurement into CBM."""
    if length and width and depth and unit:
        cbm = Decimal(0.0)
        if unit == "cm":
            cbm = round(
                (
                    (Decimal(length) * Decimal(width) * Decimal(depth))
                    / 1000000
                ),
                2,
            )
        elif unit == "in":
            cbm = round(
                (
                    (
                        Decimal(length)
                        * Decimal(2.54)
                        * Decimal(width)
                        * Decimal(2.54)
                        * Decimal(depth)
                        * Decimal(2.54)
                    )
                    / 1000000
                ),
                2,
            )

        elif unit == "m":
            cbm = round(
                (

                    Decimal(length)
                    * Decimal(width)
                    * Decimal(depth)

                ),
                2,
            )
        return cbm
