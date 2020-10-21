"""Custom made Utils file to create some useful functions."""
from decimal import Decimal


def get_cbm(length, width, depth, unit):
    """Convert measurement into CBM."""
    if length and width and depth and unit:
        if unit == "cm":
            cbm = round(
                (
                    (Decimal(length) * Decimal(width) * Decimal(depth))
                    / 1000000
                ),
                3,
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
                3,
            )
        return cbm
