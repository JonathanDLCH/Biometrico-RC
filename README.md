# Registro-service

Servicio diario para enviar registros nuevos de un biometrico a la base de datos en la nube.

## Flujo

1. Lee los biométricos configurados en la base de datos e intenta hacer el flujo con cada IP registrada.
2. Solo acepta una respuesta cuyo número de serie coincida; nunca crea biométricos (evita duplicar información de biométricos).
3. Sincroniza empleados por `id_empleado`, insertando nuevos y actualizando los existentes.
4. Consulta registros desde `ultima_sincronizacion` hasta el momento actual.
5. Revisa por `id_empleado` y `register_time` antes de insertar.
6. Actualiza `ultima_sincronizacion` solamente despues de confirmar toda la transaccion.
7. Si ocurre un error, hace rollback, registra el stack trace y notifica a soporte.

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

## Ejecucion con Docker

Construye la imagen en la maquina que tenga el codigo:

```bash
docker build -t biometric-sync:latest .
```

Como el programa realiza una sincronizacion y termina, ejecutalo cuando corresponda mediante cron, Task Scheduler o el programador de tareas de la otra maquina:

```bash
docker run --rm --env-file .env \
	-v biometric-config:/app/config \
	-v biometric-logs:/app/logs \
	biometric-sync:latest
```

El volumen de logs conserva el historial entre ejecuciones. La maquina destino solo necesita Docker y una copia de la imagen. Puedes exportarla e importarla sin un registro:

```bash
docker save biometric-sync:latest | gzip > biometric-sync.tar.gz
# En la otra maquina:
gunzip -c biometric-sync.tar.gz | docker load
```

El archivo `.env` debe copiarse por separado a la maquina destino; no se incluye en la imagen.

## Pruebas

```bash
.venv/bin/python3 -m unittest discover -s tests -v
```

Las pruebas del servicio cubren identificacion, empleados, obtencion de registros, deduplicacion, commit atomico y rollback.
