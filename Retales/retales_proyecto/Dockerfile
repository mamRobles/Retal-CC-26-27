# syntax=docker/dockerfile:1

# ============================================================
# Etapa "css": compilar Tailwind SIN Node.
# django-tailwind (modo standalone) usa pytailwindcss, que descarga el binario
# de Tailwind desde GitHub (la versión se fija en settings.py).
# ============================================================
FROM python:3.13-slim AS css

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SECRET_KEY=build-only

WORKDIR /app

COPY requirements.txt requirements-build.txt ./
RUN pip install --no-cache-dir -r requirements-build.txt

# Tailwind escanea templates/, users/ y core/ buscando clases (ver theme/static_src/src/styles.css)
COPY . .
RUN python manage.py tailwind install && python manage.py tailwind build

# ============================================================
# Etapa "dev": entorno de desarrollo (la usa compose.override.yaml).
# Parte de "css" (ya trae el binario de Tailwind) y añade las herramientas de
# desarrollo: honcho (runserver + watcher) y django-browser-reload.
# El código NO se queda en la imagen: compose lo monta desde tu disco.
# ============================================================
FROM css AS dev

RUN pip install --no-cache-dir -r requirements-dev.txt \
    && useradd --create-home --uid 1000 app

USER app
EXPOSE 8000

ENTRYPOINT ["sh", "entrypoint.sh"]
CMD ["python", "manage.py", "tailwind", "dev"]

# ============================================================
# Etapa final (la que se construye por defecto): imagen de Django solo con
# dependencias de ejecución. Recibe el CSS compilado, no el binario de Tailwind.
# ============================================================
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --uid 1000 app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=css /app/theme/static/css/dist/styles.css theme/static/css/dist/styles.css

# Recoge estáticos (admin + CSS de Tailwind) en STATIC_ROOT para que WhiteNoise los sirva.
# Debe ir DESPUÉS de copiar el CSS compilado.
RUN SECRET_KEY=build-only python manage.py collectstatic --noinput

USER app
EXPOSE 8000

# Forma "exec" (JSON): exige comillas DOBLES (ver Dockerfile de materiales).
ENTRYPOINT ["sh", "entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
