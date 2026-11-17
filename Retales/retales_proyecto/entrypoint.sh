#!/bin/sh
set -e

# Sin migraciones iniciales de "users", Django falla con un error poco claro
# ("dependency on app with no migrations"). Mejor avisar con instrucciones.
if ! ls users/migrations/0*.py >/dev/null 2>&1; then
  echo "✗ Faltan las migraciones de 'users'. Genéralas una vez con: python manage.py makemigrations users" >&2
  exit 1
fi

echo "→ Aplicando migraciones..."
python manage.py migrate --noinput

# Superusuario opcional: solo si defines las variables en .env
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput || echo "(el superusuario ya existía)"
fi

echo "→ Arrancando: $*"
exec "$@"
