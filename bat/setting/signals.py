"""File to receive signals from model or actions."""
from bat.setting.tasks import clear_versions
from django.db import transaction
from django.dispatch import receiver
from reversion.signals import post_revision_commit


@receiver(post_revision_commit)
def post_revision_commit_receiver(sender, revision, versions, **kwargs):
    """Call Celery task after receiving signal."""
    transaction.on_commit(
        lambda: clear_versions.delay(revision.id, [v.id for v in versions])
    )
