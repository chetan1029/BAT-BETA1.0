IMPERIAL = "Imperial"
METRIC = "Metric"
UNIT_SYSTEM_TYPE = ((IMPERIAL, "Imperial"), (METRIC, "Metric"))

KG = "kg"
GM = "g"
LB = "lb"
OZ = "oz"
WEIGHT_UNIT_TYPE = ((KG, "kg"), (GM, "g"), (LB, "lb"), (OZ, "oz"))
WEIGHT_UNIT_TYPE_LIST = [KG, GM, LB, OZ]

CM = "cm"
IN = "in"
M = "m"
LENGTH_UNIT_TYPE = ((CM, "cm"), (IN, "in"), (M, "m"))

DEFAULT_CURRENCY = "USD"

BASIC = "1"
SLIGHTLY_IMPORTANT = "2"
IMPORTANT = "3"
VERY_IMPORTANT = "4"
CRITICAL = "5"
IMPORTANCE_CHOICES = (
    (BASIC, "Basic"),
    (SLIGHTLY_IMPORTANT, "Slightly Important"),
    (IMPORTANT, "Important"),
    (VERY_IMPORTANT, "Very Important"),
    (CRITICAL, "Critical"),
)

DAILY = "Daily"
WEEKLY = "Weekly"
MONTHLY = "Monthly"
QUARTERLY = "Quarterly"
YEARLY = "Yearly"
INVENTORY_PREDICATION_TYPE = (
    (DAILY, "Daily"),
    (WEEKLY, "Weekly"),
    (MONTHLY, "Monthly"),
    (QUARTERLY, "Quarterly"),
    (YEARLY, "Yearly"),
)
