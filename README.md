# Sistema de Gestión de Asistencias Biométricas

Este proyecto automatiza la gestión de asistencias laborales usando un biométrico chino con API local.

## Flujo del Programa

1. **Obtener Registros**: Realiza peticiones HTTP a la API del biométrico.
1.5 **Obtener Usuarios**: Si no existen usuarios se revisan los registros del biometrico.
2. **Procesar Datos**: Analiza registros quincenalmente, validando entradas/salidas, retardos y horas extra.
3. **Generar Reportes**: Crea resúmenes en CSV y JSON.
4. **Automatización**: (próximo paso) Envío automático de reportes por email.

## Instalación

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

## Configuración

Editar `config/settings.py` para ajustar:
- Horarios de entrada/salida
- Límites de retardo y horas extra
- URL y credenciales del biométrico

Actualizar `config/employees.json` con la lista de empleados activos.

## Uso

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

Ejecutar suite de pruebas unitarias:
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