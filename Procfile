release: cd backend && python manage.py migrate --noinput
web: cd backend && gunicorn config.wsgi --workers 2 --threads 4 --timeout 90 --log-file -
