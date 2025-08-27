release: cd backend && python manage.py migrate --noinput
web: cd backend && gunicorn config.wsgi --log-file -
