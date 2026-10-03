# Consulta-service: gestión de asistencias biométricas

Aplicación Django para consultar biométricos y registros de asistencia existentes. Las pantallas son HTML funcional sin estilos añadidos.

## Aplicación web Django

La aplicación ofrece inicio de sesión, consulta del estado y última sincronización de los biométricos, y consulta de registros por fecha, periodo y empleado. Las tablas `biometricos`, `empleados` y `registros` están mapeadas como no administradas por Django, por lo que las migraciones no las crean ni alteran.

### Configuración

Instala las dependencias y configura las variables de `.env.example` en el `.env` local existente. No reemplaces credenciales reales con los valores de ejemplo.

```bash
pip install -r requirements.txt
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Guarda la clave generada como `DJANGO_SECRET_KEY`. En desarrollo local, define también `DJANGO_DEBUG=true`; para producción usa `DJANGO_DEBUG=false` y configura `DJANGO_ALLOWED_HOSTS` con los dominios permitidos.

### Inicialización y ejecución

Después de verificar que `DATABASE_URL` apunta a la base correcta y contar con un respaldo, ejecuta las migraciones de Django. Estas crean las tablas de autenticación, sesión y administración; las tablas biométricas existentes permanecen intactas.

```bash
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

La aplicación queda en `http://127.0.0.1:8000/`. El usuario inicial se crea con `createsuperuser` y posteriormente se autentica en la pantalla de login.

Los reportes semanales/quincenales en Excel o PDF aún no forman parte de esta primera etapa.

## Proceso de sincronización heredado

Los scripts actuales de sincronización, procesamiento y correo se conservan porque siguen conectados entre sí y contienen lógica que podrá reutilizarse para los reportes futuros.

## Flujo del proceso heredado

1. **Obtener Registros**: Realiza peticiones HTTP a la API del biométrico.
1.5 **Obtener Usuarios**: Si no existen usuarios se revisan los registros del biometrico.
2. **Procesar Datos**: Analiza registros quincenalmente, validando entradas/salidas, retardos y horas extra.
3. **Generar Reportes**: Crea resúmenes en CSV y JSON.
4. **Automatización**: (próximo paso) Envío automático de reportes por email.

## Instalación del proceso heredado

1. Crear entorno virtual:
   ```bash
   python3 -m venv venv
   ```

2. Activar entorno:
   ```bash
   source venv/bin/activate  # Linux/Mac
   # o
   venv\Scripts\activate  # Windows
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Configuración del proceso heredado

Editar `config/settings.py` para ajustar únicamente las reglas de horarios:
- Horarios de entrada/salida
- Límites de retardo y horas extra

Configura URL, contraseña y cookie del biométrico, además de credenciales de correo, mediante las variables de `.env.example`. No agregues secretos a `config/settings.py`.

## Ejecución del proceso heredado

Ejecutar el programa principal:
```bash
python main.py
```

Esto generará:
- `data/raw/records.json`: Registros crudos de la API
- `data/processed/attendance_analysis.csv`: Análisis detallado por día
- `data/processed/resumen.json`: Resumen estadístico
- `logs/biometrico.log`: Registro de ejecución

## Pruebas

Las pruebas Django usan una base SQLite temporal y no migran la base MySQL configurada:

```bash
python manage.py test --settings=consulta_service.test_settings tests.test_django_auth tests.test_django_forms
```

Para las pruebas del proceso heredado:

```bash
python -m unittest tests/test_api_client.py
python -m unittest tests/test_data_processor.py
```

## Estructura de Carpetas

```
Biometrico/
├── main.py                      # Punto de entrada (orquestador)
├── requirements.txt             # Dependencias Python
├── .env                         # Variables de entorno
├── config/
│   ├── settings.py              # Constantes y configuraciones
│   └── employees.json           # Lista de empleados
├── src/
│   ├── api_client.py            # Cliente API del biométrico
│   ├── data_processor.py        # Procesamiento y análisis
│   ├── report_generator.py      # (próximo) Generación de reportes
│   └── scheduler.py             # (próximo) Automatización y emails
├── data/
│   ├── raw/                     # Registros crudos de API
│   └── processed/               # Datos procesados y reportes
├── logs/                        # Archivos de registro
├── tests/                       # Pruebas unitarias
└── README.md                    # Este archivo
```

## Configuración de Email

Para el envío automático de reportes:

1. Configura las credenciales en `.env`:
   ```
   EMAIL_USER=tuemail@gmail.com
   EMAIL_PASSWORD=tu_app_password  # Para Gmail, usa app password
   ```

2. Actualiza emails de RH en `config/settings.py`:
   ```python
   EMAIL_RH = ["rh@empresa.com", "admin@empresa.com"]
   ```

3. Agrega campo `"email"` a cada empleado en `config/employees.json`:
   ```json
   {
     "id": 52,
     "name": "Condado Félix Alejandro",
     "email": "felix.condado@empresa.com"
   }
   ```

**Nota**: Si un empleado no tiene email, solo se envía a RH.

## Notas

- Los registros del biométrico se obtienen en orden descendente (más reciente primero).
- La lógica asume que el primer y último registro de un día corresponden a entrada y salida.
- Los horarios se configuran en `config/settings.py`.