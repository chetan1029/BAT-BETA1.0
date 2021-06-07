from django.contrib.postgres.fields import HStoreField
from django.db import models, transaction
from django.utils import timezone
from postgres_copy import CopyManager

from bat.company.models import Company
from bat.keywordtracking.constants import KEYWORD_STATUS_ACTIVE
from bat.keywordtracking.utils import get_visibility_score
from bat.market.models import AmazonMarketplace, AmazonProduct
from bat.setting.models import Status


# Create your models here.
class GlobalKeyword(models.Model):
    """Global Keyword Search Frequency From Amazon."""

    department = models.CharField(max_length=256)
    name = models.CharField(max_length=512)
    frequency = models.PositiveIntegerField(default=0)
    asin_1 = models.CharField(max_length=50, blank=True, null=True)
    asin_2 = models.CharField(max_length=50, blank=True, null=True)
    asin_3 = models.CharField(max_length=50, blank=True, null=True)
    create_date = models.DateTimeField(default=timezone.now)
    objects = CopyManager()

    def __str__(self):
        """Return Value."""
        return str(self.name) + " - " + str(self.department)


class Keyword(models.Model):
    """Search Keywords."""

    amazonmarketplace = models.ForeignKey(
        AmazonMarketplace, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=512)
    frequency = models.PositiveIntegerField(default=0)
    create_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Keywords Meta."""

        unique_together = ("amazonmarketplace", "name")

    def __str__(self):
        """Return Value."""
        return str(self.name) + " - " + str(self.amazonmarketplace.country)


class ProductKeyword(models.Model):
    """Product Keywords."""

    amazonproduct = models.ForeignKey(
        AmazonProduct,
        on_delete=models.CASCADE,
        verbose_name="Select Amazon Product",
    )
    keyword = models.ForeignKey(
        Keyword, on_delete=models.CASCADE, verbose_name="Select Keyword"
    )
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    create_date = models.DateField(default=timezone.now)

    class Meta:
        """Product Keyword Meta."""

        unique_together = ("amazonproduct", "keyword")

    def __str__(self):
        """Return Value."""
        return str(self.amazonproduct.asin) + " - " + str(self.keyword.name)


class ProductKeywordRankManager(models.Manager):
    def bulk_delete(self, id_list):
        with transaction.atomic():
            keywords = ProductKeywordRank.objects.filter(
                id__in=id_list
            ).delete()
        return ""


class ProductKeywordRank(models.Model):
    """Keyword rank for amazon product."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    productkeyword = models.ForeignKey(
        ProductKeyword,
        on_delete=models.CASCADE,
        verbose_name="Select Product Keyword",
    )
    index = models.BooleanField(default=False)
    rank = models.PositiveIntegerField(default=0)
    page = models.PositiveIntegerField(default=0)
    frequency = models.PositiveIntegerField(default=0)
    visibility_score = models.DecimalField(
        max_digits=5, decimal_places=2, default="0.0"
    )
    date = models.DateField(default=timezone.now)
    scrap_status = models.PositiveIntegerField(default=0)
    extra_data = HStoreField(null=True, blank=True)

    objects = ProductKeywordRankManager()

    class Meta:
        """Product Keyword Meta."""

        unique_together = ("productkeyword", "date")

    def __str__(self):
        """Return Value."""
        return (
            str(self.productkeyword.keyword.name)
            + " - "
            + str(self.productkeyword.amazonproduct.asin)
            + " - Rank: "
            + str(self.rank)
            + " - Date: "
            + str(self.date)
        )

    # def save(self, *args, **kwargs):
    #     visibility_score = get_visibility_score(
    #         self.frequency, self.rank, self.page
    #     )
    #     self.visibility_score = visibility_score
    #     return super().save(*args, **kwargs)
