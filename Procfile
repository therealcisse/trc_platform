release: cd backend && python manage.py migrate --noinput
web: cd backend && gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker --workers 2 --threads 1 --timeout 90 --log-file -
worker: cd backend && celery -A config worker --loglevel=info
