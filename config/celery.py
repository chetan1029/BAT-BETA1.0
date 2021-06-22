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
    include=[
        "bat.users.tasks",
        "bat.setting.tasks",
        "bat.market.tasks",
        "bat.autoemail.tasks",
        "bat.keywordtracking.tasks",
    ],
)

app.conf.update(
    CELERY_TASK_SERIALIZER="json",
    CELERY_RESULT_SERIALIZER="json",
    CELERY_TASK_RESULT_EXPIRES=3600,
    CELERY_TIMEZONE="UTC",
    CELERYBEAT_SCHEDULER="django_celery_beat.schedulers:DatabaseScheduler"
    # CELERYBEAT_SCHEDULE={
    #     "task1": {
    #         "task": "bat.users.tasks.task1",
    #         "schedule": crontab(minute="*/30"),
    #     }
    # },
)


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))


if __name__ == "__main__":
    app.start()
