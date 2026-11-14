# syntax=docker/dockerfile:1

# ---- Etapa 1: builder (instala dependencias en un venv) ----
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

WORKDIR /app
# Solo requirements primero: la capa de pip se cachea mientras no cambien las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Etapa 2: runtime (imagen final, solo lo necesario para ejecutar) ----
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH

WORKDIR /app

RUN useradd --create-home --uid 1000 app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app . .

USER app
EXPOSE 8000

# Forma "exec" (JSON): exige comillas DOBLES.
# "sh entrypoint.sh" evita depender del permiso de ejecución del archivo.
ENTRYPOINT ["sh", "entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]