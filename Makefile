mig:
	python manage.py makemigrations
	python manage.py migrate

super:
	python manage.py createsuperuser

celery:
	celery -A root worker --loglevel=info
