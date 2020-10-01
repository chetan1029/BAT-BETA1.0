"""Task that can run by celery will be placed here."""
from celery.utils.log import get_task_logger
from config.celery import app
from reversion.models import Revision, Version

logger = get_task_logger(__name__)


@app.task
def clear_versions(revision_id, versions_ids):
    """User task just to test and check."""
    count = 0
    if versions_ids:
        for version in Version.objects.filter(id__in=versions_ids):
            previous_version = Version.objects.filter(
                object_id=version.object_id,
                content_type_id=version.content_type_id,
                db=version.db,
                id__lt=version.id,
            ).first()
            if not previous_version:
                continue
            if previous_version._local_field_dict == version._local_field_dict:
                version.delete()
                count += 1
    if len(versions_ids) == count:
        Revision.objects.only("id").get(id=revision_id).delete()
    logger.info("revision checking ....")
