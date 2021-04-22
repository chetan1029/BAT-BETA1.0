# Convenience references for units for plan recurrence billing
# ----------------------------------------------------------------------------
RECURRENCE_UNIT_ONCE = "0"
RECURRENCE_UNIT_SECOND = "1"
RECURRENCE_UNIT_MINUTE = "2"
RECURRENCE_UNIT_HOUR = "3"
RECURRENCE_UNIT_DAY = "4"
RECURRENCE_UNIT_WEEK = "5"
RECURRENCE_UNIT_MONTH = "6"
RECURRENCE_UNIT_YEAR = "7"
RECURRENCE_UNIT_CHOICES = (
    (RECURRENCE_UNIT_ONCE, "once"),
    (RECURRENCE_UNIT_SECOND, "second"),
    (RECURRENCE_UNIT_MINUTE, "minute"),
    (RECURRENCE_UNIT_HOUR, "hour"),
    (RECURRENCE_UNIT_DAY, "day"),
    (RECURRENCE_UNIT_WEEK, "week"),
    (RECURRENCE_UNIT_MONTH, "month"),
    (RECURRENCE_UNIT_YEAR, "year"),
)

PARENT_PLAN_STATUS = "Plan"
PLAN_STATUS_GENERAL = "General"
PLAN_STATUS_SPECIAL = "Special"


TRANSACTION_TYPE_NET_BANKING = "net_banking"
TRANSACTION_TYPE_CHOICES = ((TRANSACTION_TYPE_NET_BANKING, "Net banking"),)


PARENT_SUBSCRIPTION_STATUS = "Subscription"
SUBSCRIPTION_STATUS_ACTIVE = "Active"
SUBSCRIPTION_STATUS_EXPIRING = "Expiring"
SUBSCRIPTION_STATUS_TERMINATED = "Terminated"
SUBSCRIPTION_STATUS_SUSPENDED = "Suspended"


QUOTA_CODE_MARKETPLACES_FREE_EMAIL = "FREE-EMAIL"
QUOTA_CODE_KEYWORD_TRACKER_EXTENSION = "KT-EXTENSION"
QUOTA_CODE_MARKETPLACES = "MARKETPLACES"
QUOTA_CODE_AMAZON_AUTOMATIC_REVIEW_REQUEST = "AMAZON-REVIEW-REQUEST"
