#!/bin/bash
cd /Volumes/Volutz/Development/BMAB/projectbat-beta1.0;
python manage.py test;
celery -A config worker -l INFO &
celery -A config beat -l INFO &
gulp;
