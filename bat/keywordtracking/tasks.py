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
    productkeywords = ProductKeyword.objects.filter(
        status=product_keywords_status
    ).values(
        "id", "keyword__frequency", "amazonproduct__amazonaccounts__company_id"
    )

    print(productkeywords.count())

    batch_size = 1000
    new_objects = [
        ProductKeywordRank(
            company_id=values["amazonproduct__amazonaccounts__company_id"],
            productkeyword_id=values["id"],
            frequency=values["keyword__frequency"],
        )
        for values in productkeywords
    ]
    print("objects")
    print(len(list(new_objects)))
    i = 0
    # while True:
    #     batch = list(islice(new_objects, batch_size))
    #     if not batch:
    #         break
    #     ProductKeywordRank.objects.bulk_create(
    #         batch, batch_size, ignore_conflicts=True
    #     )
    #     i = i + 1
    #     print(i)
    #     print(len(batch))
    #     logger.info("product keyword rank creation")
