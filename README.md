# Registro-service

Servicio diario para enviar registros nuevos de un biometrico a la base de datos en la nube.

## Flujo

1. Identifica el biometrico por `sn` o `ip`; si no existe, lo crea.
2. Sincroniza empleados por `id_empleado`, insertando nuevos y actualizando los existentes.
3. Consulta registros desde `ultima_sincronizacion` hasta el momento actual.
4. Deduplica por `id_empleado` y `register_time` antes de insertar.
5. Actualiza `ultima_sincronizacion` solamente despues de confirmar toda la transaccion.
6. Si ocurre un error, hace rollback, registra el stack trace y notifica a soporte.

El cursor no avanza si falla cualquier paso. La siguiente ejecucion vuelve a intentar el mismo intervalo, por lo que el programa puede ejecutarse diariamente mediante cron, Task Scheduler o un servicio del sistema.

## Instalacion

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Variables de entorno

Configura estas variables en `.env` o en el entorno del proceso. No guardes contrasenas en el repositorio.

```dotenv
DATABASE_URL=mysql+pymysql://usuario:contrasena@host:3306/base
BIOMETRIC_API_URL=http://192.168.10.2:80/api
BIOMETRIC_PASSWORD=contrasena_del_biometrico
BIOMETRIC_DEVICE_COOKIE=cookie_de_sesion_del_dispositivo
EMAIL_USER=cuenta_remitente
EMAIL_PASSWORD=app_password
SUPPORT_EMAILS=soporte@empresa.com,desarrollo@empresa.com
INITIAL_SYNC_DAYS=1
```

Tambien se admiten `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` y `DB_NAME` para construir `DATABASE_URL`.

## Ejecucion

```bash
.venv/bin/python3 main.py
```

El proceso devuelve `0` si termina correctamente y `1` si falla despues de registrar y notificar el error.

## Pruebas

```bash
.venv/bin/python3 -m unittest discover -s tests -v
```

Las pruebas del servicio cubren identificacion, empleados, obtencion de registros, deduplicacion, commit atomico y rollback.
