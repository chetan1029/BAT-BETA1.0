EMAIL_LANG_ENGLISH = "English"
EMAIL_LANG_GERMAN = "German"
EMAIL_LANG_ITALIAN = "Italian"

EMAIL_LANG_CHOICES = (
    (EMAIL_LANG_ENGLISH, "English"),
    (EMAIL_LANG_GERMAN, "German"),
    (EMAIL_LANG_ITALIAN, "Italian"),
)

FBA = "FBA"
FBM = "FBM"
CHANNEL_CHOICES = ((FBA, "FBA"), (FBM, "FBM"))

DAILY = "Daily"
AS_SOON_AS = "As soon as possible"
AS_SOON_SHIPPED = "As soon as order shipped"
SCHEDULE_CHOICES = (
    (DAILY, "Daily"),
    (AS_SOON_AS, "As soon as possible"),
    (AS_SOON_SHIPPED, "As soon as order shipped"),
)

PURCHASE_1ST = "1st Purchase"
PURCHASE_2ND = "2nd Purchase"
PURCHASE_3RD = "3rd Purchase"
PURCHASE_4TH = "4th Purchase"
BUYER_PURCHASE_CHOICES = (
    (PURCHASE_1ST, "1st Purchase"),
    (PURCHASE_2ND, "2nd Purchase"),
    (PURCHASE_3RD, "3rd Purchase"),
    (PURCHASE_4TH, "4th Purchase"),
)

FEEDBACK_1_STAR = "Negative Feedback(1 star)"
FEEDBACK_2_STAR = "Negative Feedback(2 star)"
FEEDBACK_3_STAR = "Neutral Feedback(3 star)"
FEEDBACK_4_STAR = "Positive Feedback(4 star)"
FEEDBACK_5_STAR = "Positive Feedback(5 star)"
WITH_RETURNS = "With Returns"
WITH_REFUNDS = "With Refunds"
ITEM_DISCOUNT = "Item Discount"
SHIPPING_DISCOUNT = "Shipping Discount"
EXCLUDE_ORDERS_CHOICES = (
    (FEEDBACK_1_STAR, "Negative Feedback(1 star)"),
    (FEEDBACK_2_STAR, "Negative Feedback(2 star)"),
    (FEEDBACK_3_STAR, "Neutral Feedback(3 star)"),
    (FEEDBACK_4_STAR, "Positive Feedback(4 star)"),
    (FEEDBACK_5_STAR, "Positive Feedback(5 star)"),
    (WITH_RETURNS, "With Returns"),
    (WITH_REFUNDS, "With Refunds"),
    (ITEM_DISCOUNT, "Item Discount"),
    (SHIPPING_DISCOUNT, "Shipping Discount"),
)

ORDER_EMAIL_PARENT_STATUS = "order_email_status"
ORDER_EMAIL_STATUS_QUEUED = "queued"
ORDER_EMAIL_STATUS_SCHEDULED = "scheduled"
ORDER_EMAIL_STATUS_SEND = "send"
ORDER_EMAIL_STATUS_OPTOUT = "opt-out"

ORDER_EMAIL_STATUS_CHOICES = (
    (ORDER_EMAIL_STATUS_QUEUED, "Queued"),
    (ORDER_EMAIL_STATUS_SCHEDULED, "Scheduled"),
    (ORDER_EMAIL_STATUS_SEND, "Send"),
    (ORDER_EMAIL_STATUS_OPTOUT, "Opt-out"),
)


PER_EMAIL_CHARGED_POINTS = 1
PER_EMAIL_CHARGED_POINTS_FOR_INVOICE = 1


EMAIL_CAMPAIGN_PARENT_STATUS = "Basic"
EMAIL_CAMPAIGN_STATUS_ACTIVE = "Active"
EMAIL_CAMPAIGN_STATUS_ARCHIVE = "Archive"
EMAIL_CAMPAIGN_STATUS_DRAFT = "Draft"
EMAIL_CAMPAIGN_STATUS_INACTIVE = "Inactive"


EMAIL_CAMPAIGN_STATUS_CHOICE = [
    EMAIL_CAMPAIGN_STATUS_ACTIVE,
    EMAIL_CAMPAIGN_STATUS_ARCHIVE,
    EMAIL_CAMPAIGN_STATUS_DRAFT,
    EMAIL_CAMPAIGN_STATUS_INACTIVE,
]
