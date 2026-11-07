# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --uid 1000 app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER app
EXPOSE 8000

# Forma "exec" (JSON): exige comillas DOBLES. Con comillas simples Docker lo trata
# como texto para el shell y el contenedor no arranca.
# "sh entrypoint.sh" evita depender del permiso de ejecución del archivo
# (en desarrollo el código se monta desde tu disco y ese permiso puede perderse).
ENTRYPOINT ["sh", "entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
