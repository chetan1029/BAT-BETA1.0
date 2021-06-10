from celery.utils.log import get_task_logger
from django.db.models.signals import post_save
from django.dispatch import receiver

from bat.autoemail.constants import EMAIL_CAMPAIGN_STATUS_ACTIVE
from bat.autoemail.models import EmailCampaign
from bat.autoemail.tasks import email_queue_create_for_new_campaign

logger = get_task_logger(__name__)


@receiver(post_save, sender=EmailCampaign)
def when_emailcampaign_created_or_updated(sender, instance, created, **kwargs):
    logger.info("Email Campaign " + str(instance.id) + " --- " + str(created))
    if created:
        if instance.status.name == EMAIL_CAMPAIGN_STATUS_ACTIVE:
            email_queue_create_for_new_campaign.delay(instance.id)
    else:
        old_status = instance.get_dirty_fields(check_relationship=True).get(
            "status", None
        )
        if old_status:
            if (
                old_status != instance.status.id
                and instance.status.name == EMAIL_CAMPAIGN_STATUS_ACTIVE
            ):
                email_queue_create_for_new_campaign.delay(instance.id)
