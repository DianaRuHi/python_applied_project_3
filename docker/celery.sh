#!/bin/bash

cd /project_3

if [ "$1" = "celery" ]; then
    echo "Starting Celery worker..."
    cd src
    celery -A tasks.tasks:celery worker --loglevel=info
elif [ "$1" = "flower" ]; then
    echo "Starting Flower monitoring..."
    cd src
    celery -A tasks.tasks:celery flower --port=5555
fi