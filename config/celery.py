"""Celery setup for scheduled tasks."""
from __future__ import absolute_import

import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
app = Celery(
    "bat",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["bat.users.tasks", "bat.setting.tasks"],
)

app.conf.update(
    CELERY_TASK_SERIALIZER="json",
    CELERY_RESULT_SERIALIZER="json",
    CELERY_TASK_RESULT_EXPIRES=3600,
    CELERY_TIMEZONE="UTC",
    CELERYBEAT_SCHEDULE={
        "task1": {
            "task": "bat.users.tasks.task1",
            "schedule": crontab(minute="*/30"),
        }
    },
)

if __name__ == "__main__":
    app.start()
