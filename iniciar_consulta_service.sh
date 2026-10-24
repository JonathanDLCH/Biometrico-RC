#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)" || exit 1
cd "$SCRIPT_DIR" || exit 1

PYTHON=""
for candidate in \
    "$SCRIPT_DIR/.venv/bin/python" \
    "$SCRIPT_DIR/venv/bin/python" \
    "$SCRIPT_DIR/env/bin/python"
do
    if [ -x "$candidate" ]; then
        PYTHON="$candidate"
        break
    fi
done

LOGIN_URL="http://127.0.0.1:8000/accounts/login/"

if [ -z "$PYTHON" ]; then
    echo "No se encontro Python en .venv, venv o env."
    echo "Crea el entorno virtual e instala requirements.txt antes de continuar."
    exit 1
fi

export DJANGO_DEBUG=true
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

if ! "$PYTHON" manage.py check; then
    echo "Django encontro errores de configuracion."
    exit 1
fi

nohup "$PYTHON" manage.py runserver 127.0.0.1:8000 \
    >/dev/null 2>&1 </dev/null &
SERVER_PID=$!

i=1
while [ "$i" -le 30 ]; do
    if curl --silent --fail --max-time 1 --output /dev/null "$LOGIN_URL"; then
        if ! open "$LOGIN_URL"; then
            echo "No se pudo abrir el navegador. Accede manualmente a: $LOGIN_URL"
            exit 1
        fi
        exit 0
    fi

    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "El servidor no pudo iniciar."
        exit 1
    fi

    sleep 1
    i=$((i + 1))
done

echo "El servidor no respondio despues de 30 segundos."
kill "$SERVER_PID" 2>/dev/null
exit 1
