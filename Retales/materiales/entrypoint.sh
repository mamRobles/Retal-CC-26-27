#!/bin/sh
set -e

# Sin migraciones, 'migrate' no crea la tabla de 'items' y la API fallaría en cada petición.
if ! ls items/migrations/0*.py >/dev/null 2>&1; then
  echo '✗ Faltan las migraciones de 'items'. Genéralas una vez (ver README.md, paso 2).' >&2
  exit 1
fi

echo '→ Aplicando migraciones...'
python manage.py migrate --noinput

echo '→ Arrancando: $*'
exec '$@'
