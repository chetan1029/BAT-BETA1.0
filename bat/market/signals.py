from celery.utils.log import get_task_logger
from django.db.models.signals import post_save
from django.dispatch import receiver

from bat.market.models import AmazonOrderItem, AmazonProductSessions

logger = get_task_logger(__name__)


@receiver(post_save, sender=AmazonProductSessions)
def when_amazonproductsessions_created_or_updated(
    sender, instance, created, **kwargs
):
    logger.info(
        "Product Sessions " + str(instance.id) + " --- " + str(created)
    )
    orders = AmazonOrderItem.objects.filter(
        amazonproduct=instance.amazonproduct,
        amazonorder__purchase_date__date=instance.date,
    ).count()
    conversion_rate = 0
    if orders and instance.sessions:
        conversion_rate = round((orders / instance.sessions) * 100)
    instance.conversion_rate = conversion_rate
    logger.info("Product Sessions " + str(conversion_rate))
    instance.save()
