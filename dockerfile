FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DJANGO_SETTINGS_MODULE=server.settings

RUN python manage.py collectstatic --noinput

CMD ["bash", "-c", "gunicorn server.wsgi:application -b 0.0.0.0:${PORT:-8000} --workers 3"]
