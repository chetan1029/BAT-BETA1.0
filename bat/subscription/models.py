from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator
from django.contrib.postgres.fields import HStoreField

from djmoney.models.fields import MoneyField

from bat.setting.models import Status
from bat.company.models import Member
from bat.subscription import constants


class Plan(models.Model):
    """
    model to represent available subscription plan for the system.
    """
    name = models.CharField(verbose_name=_("Name"), max_length=200,
                            help_text=_('the name of the subscription plan'),)
    description = models.TextField(verbose_name=_("Description"), blank=True)
    recurrence_period = models.PositiveSmallIntegerField(
        default=1,
        help_text=_('how often the plan is billed (per recurrence unit)'),
        validators=[MinValueValidator(1)],
    )
    recurrence_unit = models.CharField(
        choices=constants.RECURRENCE_UNIT_CHOICES,
        default=constants.RECURRENCE_UNIT_MONTH,
        max_length=1,
    )
    cost = MoneyField(max_digits=14, decimal_places=2, default_currency="USD",
                      null=True, blank=True,
                      help_text=_('the cost per recurrence of the plan'))
    permission_list = models.JSONField(verbose_name=_("Permission List"))
    extra_data = HStoreField(null=True, blank=True)
    meta_data = HStoreField(null=True, blank=True)
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        """Return Value."""
        return self.name + " - " + str(self.id)

    @property
    def display_recurrent_unit_text(self):
        """Converts recurrence_unit integer to text."""
        conversion = {
            constants.RECURRENCE_UNIT_ONCE: 'one-time',
            constants.RECURRENCE_UNIT_SECOND: 'per second',
            constants.RECURRENCE_UNIT_MINUTE: 'per minute',
            constants.RECURRENCE_UNIT_HOUR: 'per hour',
            constants.RECURRENCE_UNIT_DAY: 'per day',
            constants.RECURRENCE_UNIT_WEEK: 'per week',
            constants.RECURRENCE_UNIT_MONTH: 'per month',
            constants.RECURRENCE_UNIT_YEAR: 'per year',
        }

        return conversion[self.recurrence_unit]

    def next_billing_datetime(self, current=None):
        """Calculates next billing date for provided datetime.
            Parameters:
                current (datetime): The current datetime to compare
                    against.
            Returns:
                datetime: The next time billing will be due.
        """
        if current is None:
            current = timezone.now
            print("\ncurrent : ", current, "\n")

        if self.recurrence_unit == constants.RECURRENCE_UNIT_SECOND:
            delta = timedelta(seconds=self.recurrence_period)
        elif self.recurrence_unit == constants.RECURRENCE_UNIT_MINUTE:
            delta = timedelta(minutes=self.recurrence_period)
        elif self.recurrence_unit == constants.RECURRENCE_UNIT_HOUR:
            delta = timedelta(hours=self.recurrence_period)
        elif self.recurrence_unit == constants.RECURRENCE_UNIT_DAY:
            delta = timedelta(days=self.recurrence_period)
        elif self.recurrence_unit == constants.RECURRENCE_UNIT_WEEK:
            delta = timedelta(weeks=self.recurrence_period)
        elif self.recurrence_unit == constants.RECURRENCE_UNIT_MONTH:
            # Adds the average number of days per month as per:
            # http://en.wikipedia.org/wiki/Month#Julian_and_Gregorian_calendars
            # This handle any issues with months < 31 days and leap years
            delta = timedelta(
                days=30.4368 * self.recurrence_period
            )
        elif self.recurrence_unit == constants.RECURRENCE_UNIT_YEAR:
            # Adds the average number of days per year as per:
            # http://en.wikipedia.org/wiki/Year#Calendar_year
            # This handle any issues with leap years
            delta = timedelta(
                days=365.2425 * self.recurrence_period
            )
        else:
            # If no recurrence period, no next billing datetime
            return None

        return current + delta


class Subscription(models.Model):
    """
    Model to represent plans subscribe by the member.
    """
    member = models.ForeignKey(
        Member, on_delete=models.PROTECT, related_name="subscriptions")
    plan = models.ForeignKey(
        Plan, on_delete=models.PROTECT, related_name="subscriptions")
    billing_start_date = models.DateTimeField()
    billing_end_date = models.DateTimeField()
    last_billing_date = models.DateTimeField()
    next_billing_date = models.DateTimeField()
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        """Return Value."""
        return str(self.id)


class SubscriptionTransaction(models.Model):
    """
    Model to represent plans subscribe bill transaction by the member.
    """
    member = models.ForeignKey(
        Member, on_delete=models.PROTECT, related_name="subscription_transactions")
    subscription = models.ForeignKey(
        Subscription, on_delete=models.PROTECT, related_name="subscription_transactions")
    date_of_transaction = models.DateTimeField()
    billing_end_date = models.DateTimeField()
    amount = models.DateTimeField()
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    transaction_type = models.CharField(
        choices=constants.TRANSACTION_TYPE_CHOICES, max_length=200)

    def __str__(self):
        """Return Value."""
        return str(self.subscription.id) + " - " + str(self.id)
