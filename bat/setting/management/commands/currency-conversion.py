"""Class to setup cronjob."""

from decimal import Decimal
from time import sleep

import requests

from bat.setting.models import Currency, CurrencyConversion
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    """Command to execute."""

    help = "currency conversion api"

    def handle(self, *args, **options):
        """Sync Old Order to BAT."""
        currencies = Currency.objects.all()
        for currency in currencies:
            from_currency = currency.name
            if from_currency == "RMB":
                from_currency = "CNY"
            currencies1 = Currency.objects.all()
            for currency1 in currencies1:
                to_currency = currency1.name
                if to_currency == "RMB":
                    to_currency = "CNY"
                currency_str = from_currency + "_" + to_currency
                currency_convert = requests.get(
                    "https://free.currconv.com/api/v7/convert?q="
                    + currency_str
                    + "&compact=ultra&apiKey=c75ed41ea704bacf4889"
                )
                sleep(5)
                currency_convert = currency_convert.json()
                conversion_ratio = round(
                    Decimal(currency_convert[currency_str]), 3
                )
                if conversion_ratio:
                    currencyconversion, created = CurrencyConversion.objects.update_or_create(
                        from_currency=currency,
                        to_currency=currency1,
                        defaults={
                            "conversion_ratio": conversion_ratio,
                            "update_date": timezone.now(),
                        },
                    )
        self.stdout.write(
            self.style.SUCCESS(
                "Successfully Updated data " + str(timezone.now())
            )
        )
