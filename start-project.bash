#!/bin/bash
cd /Volumes/My/BAT/projectbat/bat-beta;
python manage.py test;
celery -A config worker -l INFO &
celery -A config beat -l INFO &
#gulp;
