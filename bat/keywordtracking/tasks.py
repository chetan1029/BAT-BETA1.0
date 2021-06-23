"""Task that can run by celery will be placed here."""
from itertools import islice

from celery.utils.log import get_task_logger

from bat.keywordtracking.constants import KEYWORD_PARENT_STATUS, KEYWORD_STATUS_ACTIVE
from bat.keywordtracking.models import ProductKeyword, ProductKeywordRank
from bat.setting.utils import get_status
from config.celery import app

logger = get_task_logger(__name__)


@app.task
def add_product_keyword_to_rank_for_today():
    product_keywords_status = get_status(
        KEYWORD_PARENT_STATUS, KEYWORD_STATUS_ACTIVE
    )
    productkeywords = ProductKeyword.objects.all().values(
        "id", "keyword__frequency", "amazonproduct__amazonaccounts__company_id"
    )

    product_keywords = [
        ProductKeywordRank(
            company_id=values["amazonproduct__amazonaccounts__company_id"],
            productkeyword_id=values["id"],
            frequency=values["keyword__frequency"],
        )
        for values in productkeywords
    ]

    batch_size = 1000

    ProductKeywordRank.objects.bulk_create(
        product_keywords, batch_size, ignore_conflicts=True
    )
    logger.info("Product Keywords Rank Added")
