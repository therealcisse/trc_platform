release: cd backend && python manage.py migrate --noinput
web: cd backend && gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker --workers $WEB_CONCURRENCY --preload --threads 1 --timeout 90 --log-file -
