"""Task that can run by celery will be placed here."""
from celery.utils.log import get_task_logger
from config.celery import app

logger = get_task_logger(__name__)


@app.task
def task1():
    """Demo task."""
    logger.info("celery MC work na")
