from rest_framework import status
from bat.market.amazon_ad_api import keywords
import csv
from io import StringIO

from django.contrib.postgres.fields import HStoreField
from django.contrib.postgres.indexes import BTreeIndex
from django.db import connection, models, transaction
from django.utils import timezone
from postgres_copy import CopyManager

from bat.company.models import Company
from bat.keywordtracking.constants import KEYWORD_STATUS_ACTIVE, KEYWORD_PARENT_STATUS
from bat.keywordtracking.utils import StringIteratorIO, get_visibility_score
from bat.market.models import AmazonMarketplace, AmazonProduct
from bat.setting.models import Status

from bat.setting.utils import get_status


class GlobalKeywordManager(models.Manager):
    def bulk_copy(self, csv_file):
        copy_query = (
            "COPY keywordtracking_globalkeyword(department,name,frequency,asin_1,asin_2,asin_3,create_date) FROM '"
            + csv_file
            + "' CSV HEADER;"
        )
        with connection.cursor() as cursor:
            cursor.execute(copy_query)


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
    # objects = GlobalKeywordManager()
    objects = CopyManager()

    class Meta:
        indexes = (BTreeIndex(fields=("department", "name")),)

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
        indexes = (BTreeIndex(fields=("name",)),)

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
    create_date = models.DateTimeField(default=timezone.now)

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
    
    def create_bulk(self, data, company_pk):
        product_ids = [ sub['product_id'] for sub in data ]
        product_keywords_status = get_status(KEYWORD_PARENT_STATUS, KEYWORD_STATUS_ACTIVE)
        amazon_products = AmazonProduct.objects.filter(amazonaccounts__company_id = company_pk, pk__in=product_ids).values_list("id", "amazonaccounts__marketplace")
        amazon_products_map = dict(amazon_products)

        keywords = Keyword.objects.all().values_list("name", "amazonmarketplace", "id")
        keywords_map = {str(k1)+str(k2):str(v) for k1, k2, v in keywords}

        product_keywords = ProductKeyword.objects.filter(amazonproduct__in=amazon_products_map.keys()).values_list("amazonproduct", "keyword", "id" )
        product_keywords_map = {str(k1)+str(k2):str(v) for k1, k2, v in product_keywords}

        product_keyword_ranks = ProductKeywordRank.objects.filter(company__id = company_pk).values_list("productkeyword", "date", "id")
        product_keywords_ranks_map = {str(k1)+str(k2):str(v) for k1, k2, v in product_keyword_ranks}

        

        new_keyword_objects = []
        new_productkeyword_objects = []
        new_productkeywordranks_objects = []
        update_productkeywordranks_objects = []

        data2 = []

        for row in data:
            row_copy = row.copy()
            amazonmarketplace = amazon_products_map.get(int(row.get("product_id", None)), None)
            if amazonmarketplace:
                keyword_id = keywords_map.get(str(row.get("keyword_name", None))+str(amazonmarketplace), None)
                if keyword_id:
                    product_keyword_id = product_keywords_map.get(str(row.get("product_id", None))+str(keyword_id),None)
                    if product_keyword_id:
                       
                        product_keyword_rank_id = product_keywords_ranks_map.get(str(product_keyword_id)+str(row.get("date")), None)
                        if product_keyword_rank_id:
                           update_productkeywordranks_objects.append(ProductKeywordRank(
                            id=product_keyword_rank_id, 
                            productkeyword_id = product_keyword_id,
                            company_id = company_pk, 
                            date=row.get("date"), 
                            index=row.get("index"), 
                            rank=row.get("rank"), 
                            page=row.get("page"), 
                            scrap_status=1
                            ))
                        else:
                            new_productkeywordranks_objects.append(ProductKeywordRank(
                            productkeyword_id = product_keyword_id,
                            company_id = company_pk,
                            date=row.get("date"), 
                            index=row.get("index"), 
                            rank=row.get("rank"), 
                            page=row.get("page"), 
                            scrap_status=1
                            ))
                    else:
                        data2.append(row_copy)
                        new_productkeyword_objects.append(ProductKeyword(
                            keyword_id=keyword_id, amazonproduct_id=row.get("product_id", None),
                            status_id = product_keywords_status.id
                        ))
                else:
                    data2.append(row_copy)
                    new_keyword_objects.append(Keyword(
                        amazonmarketplace_id = amazonmarketplace,
                        name=row.get("keyword_name", None)
                    ))
            else:
                pass
        
        
        with transaction.atomic():
            new_keywords = Keyword.objects.bulk_create(new_keyword_objects)
            new_productkeyword = ProductKeyword.objects.bulk_create(new_productkeyword_objects)
            updated_productkeywordranks = ProductKeywordRank.objects.bulk_update(update_productkeywordranks_objects, ["date", "index", "rank", "page"])
            new_productkeywordranks = ProductKeywordRank.objects.bulk_create(new_productkeywordranks_objects)
            
            keywords_map = { str(sub.name) + str(sub.amazonmarketplace.id) : str(sub.id) for sub in new_keywords }
            while data2 :
                product_keywords_map = {str(sub.amazonproduct.id)+str(sub.keyword.id):str(sub.id) for sub in new_productkeyword}
                product_keywords_ranks_map = {str(sub.productkeyword.id)+str(sub.date):str(sub.id) for sub in new_productkeywordranks}
                
                new_keyword_objects = []
                new_productkeyword_objects = []
                new_productkeywordranks_objects = []
                update_productkeywordranks_objects = []

                data3 = []

                for row in data2:
                    row_copy = row.copy()
                    amazonmarketplace = amazon_products_map.get(int(row.get("product_id", None)), None)
                    
                    if amazonmarketplace:
                        keyword_id = keywords_map.get(str(row.get("keyword_name", None))+str(amazonmarketplace), None)
                        if keyword_id:
                            
                            product_keyword_id = product_keywords_map.get(str(row.get("product_id", None))+str(keyword_id),None)
                            if product_keyword_id:
                               
                                product_keyword_rank_id = product_keywords_ranks_map.get(str(product_keyword_id)+str(row.get("date")), None)
                                if product_keyword_rank_id:
                                    update_productkeywordranks_objects.append(ProductKeywordRank(
                                        id=product_keyword_rank_id, 
                                        productkeyword_id = product_keyword_id,
                                        company_id = company_pk, 
                                        date=row.get("date"), 
                                        index=row.get("index"), 
                                        rank=row.get("rank"), 
                                        page=row.get("page"), 
                                        scrap_status=1
                                        ))
                                else:
                                    new_productkeywordranks_objects.append(ProductKeywordRank(
                                    productkeyword_id = product_keyword_id,
                                    company_id = company_pk,
                                    date=row.get("date"), 
                                    index=row.get("index"), 
                                    rank=row.get("rank"), 
                                    page=row.get("page"), 
                                    scrap_status=1
                                    ))
                            else:
                                data3.append(row_copy)
                                new_productkeyword_objects.append(ProductKeyword(
                                    keyword_id=keyword_id, amazonproduct_id=row.get("product_id", None),
                                    status_id = product_keywords_status.id
                                ))
                        else:
                            data3.append(row_copy)
                            new_keyword_objects.append(Keyword(
                                amazonmarketplace_id = amazonmarketplace,
                                name=row.get("keyword_name", None)
                            ))
                    else:
                        pass

               
                new_keywords = Keyword.objects.bulk_create(new_keyword_objects)
                new_productkeyword = ProductKeyword.objects.bulk_create(new_productkeyword_objects)
                updated_productkeywordranks = ProductKeywordRank.objects.bulk_update(update_productkeywordranks_objects, ["date", "index", "rank", "page"])
                new_productkeywordranks = ProductKeywordRank.objects.bulk_create(new_productkeywordranks_objects)

                data2 = data3


    def create_bulk2(self, data, amazonproduct, company_pk=None):
        if not company_pk:
           company_pk=amazonproduct.get_company 
        amazonmarket = amazonproduct.amazonaccounts.amazonmarket
        keywords_map = dict(Keyword.objects.filter(amazonmarketplace=amazonmarket).values_list("name", id))
        productkeywords_map = dict(ProductKeyword.objects.filter(amazonproduct=amazonproduct).values_list("keyword_id", "id"))
        productkeywordranks = ProductKeywordRank.objects.filter(company_id=company_pk).values_list("productkeyword_id", "date", "id")
        productkeywordranks_map = {str(k1)+str(k2):str(v) for k1, k2, v in productkeywordranks}

        new_keyword_objects = []
        new_productkeyword_objects = []
        new_productkeywordranks_objects = []
        update_productkeywordranks_objects = []
        for row in data:
            keyword_name = row.get("keyword_name")
            keyword_id = keywords_map.get(keyword_name, None)
            if keyword_id:
                productkeywords_id = productkeywords_map.get(keyword_id, None)
                if productkeywords_id:
                    productkeywordranks_id = productkeywordranks_map.get(str(productkeywords_id)+str(row.get("date")))
                    if productkeywordranks_id :
                        update_productkeywordranks_objects.append(ProductKeywordRank(
                            id=productkeywordranks_id, 
                            productkeyword_id = productkeywords_id, 
                            date=row.get("date"), 
                            index=row.get("index"), 
                            rank=row.get("rank"), 
                            page=row.get("page"), 
                            scrap_status=1
                            ))
                    else :
                        new_productkeywordranks_objects.append(ProductKeywordRank(
                            productkeyword_id = productkeywords_id, 
                            date=row.get("date"), 
                            index=row.get("index"), 
                            rank=row.get("rank"), 
                            page=row.get("page"), 
                            scrap_status=1
                        ))
                else :
                    new_productkeyword_objects.append(ProductKeyword(
                        keyword_id=keyword_id, amazonproduct_id=amazonproduct.id
                    ))
                    pass
            else :
                pass
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
    frequency = models.PositiveIntegerField(null=True)
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

    def save(self, *args, **kwargs):
        visibility_score = get_visibility_score(
            self.frequency, self.rank, self.page
        )
        self.visibility_score = visibility_score
        return super().save(*args, **kwargs)
