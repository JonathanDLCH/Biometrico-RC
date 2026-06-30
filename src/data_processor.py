from datetime import datetime, timedelta
import pandas as pd
import logging
from config.settings import HORA_ENTRADA, HORA_SALIDA, HORA_SALIDA_SABADO, LIMITE_RETARDO_MINUTOS, LIMITE_HORAS_EXTRA_MINUTOS

logging.basicConfig(level=logging.INFO)

class AttendanceProcessor:
    """
    Procesa registros de asistencia del biométrico aplicando lógica de negocio:
    - Validar pares entrada/salida
    - Detectar retardos
    - Detectar faltas (sin entrada o sin salida)
    - Calcular horas extra
    """

    def __init__(self, hora_entrada=HORA_ENTRADA, hora_salida=HORA_SALIDA, 
                 hora_salida_sabado=HORA_SALIDA_SABADO,
                 limite_retardo_min=LIMITE_RETARDO_MINUTOS, limite_horas_extra_min=LIMITE_HORAS_EXTRA_MINUTOS):
        """
        Inicializa el procesador.
        
        :param hora_entrada: Hora de entrada esperada (HH:MM:SS)
        :param hora_salida: Hora de salida esperada para días de semana (HH:MM:SS)
        :param hora_salida_sabado: Hora de salida esperada para sábados (HH:MM:SS)
        :param limite_retardo_min: Minutos permitidos de retardo
        :param limite_horas_extra_min: Minutos después de hora salida para contar como hora extra
        """
        self.hora_entrada = datetime.strptime(hora_entrada, "%H:%M:%S").time()
        self.hora_salida = datetime.strptime(hora_salida, "%H:%M:%S").time()
        self.hora_salida_sabado = datetime.strptime(hora_salida_sabado, "%H:%M:%S").time()
        self.limite_retardo_min = limite_retardo_min
        self.limite_horas_extra_min = limite_horas_extra_min

    def procesar_registros(self, records):
        """
        Procesa una lista de registros biométricos.
        
        :param records: Lista de dicts con campos: enrollid, time, name
        :return: DataFrame con análisis por día
        """
        if not records:
            return pd.DataFrame()

        # Convertir a DataFrame
        df = pd.DataFrame(records)
        df['timestamp'] = pd.to_datetime(df['time'])
        df['date'] = df['timestamp'].dt.date
        df['time_only'] = df['timestamp'].dt.time

        # Agrupar por día y orderar por hora
        df_sorted = df.sort_values('timestamp')
        
        # Procesar por día
        resultados = []
        for date, group in df_sorted.groupby('date'):
            analisis_dia = self._analizar_dia(date, group)
            resultados.append(analisis_dia)

        return pd.DataFrame(resultados)

    def _analizar_dia(self, date, records_dia):
        """
        Analiza registros de un día específico.
        
        :param date: Fecha del día
        :param records_dia: DataFrame con registros del día
        :return: Dict con análisis
        """
        # Obtener primer y último registro
        primer_registro = records_dia.iloc[0]
        ultimo_registro = records_dia.iloc[-1]

        hora_entrada_real = primer_registro['time_only']
        hora_salida_real = ultimo_registro['time_only']

        # Calcular retardo
        retardo_min = self._calcular_retardo(hora_entrada_real)
        tiene_retardo = retardo_min > 0

        # Calcular horas extra
        hora_salida_esperada = self._hora_salida_esperada(date)
        horas_extra_min = self._calcular_horas_extra(hora_salida_real, hora_salida_esperada)
        tiene_horas_extra = horas_extra_min > 0

        # Validar registro completo - Lógica mejorada para casos 2 y 3
        num_registros = len(records_dia)
        
        if num_registros == 0:
            falta_entrada = True
            falta_salida = True
        elif num_registros == 1:
            # Un solo registro: determinar si es entrada o salida
            unico_registro = records_dia.iloc[0]['time_only']
            # Si el registro es antes del mediodía, asumir entrada sin salida
            # Si es después del mediodía, asumir salida sin entrada
            if unico_registro < datetime.strptime("12:00:00", "%H:%M:%S").time():
                falta_entrada = False  # Tiene entrada
                falta_salida = True    # Falta salida
            else:
                falta_entrada = True   # Falta entrada
                falta_salida = False   # Tiene salida
        else:
            # Múltiples registros: asumir primer = entrada, último = salida
            falta_entrada = False
            falta_salida = False

        # Calcular horas trabajadas
        horas_trabajadas = self._calcular_horas_trabajadas(hora_entrada_real, hora_salida_real)

        return {
            'date': date,
            'enrollid': primer_registro['enrollid'],
            'name': primer_registro['name'],
            'hora_entrada': hora_entrada_real,
            'hora_salida': hora_salida_real,
            'retardo_minutos': retardo_min,
            'tiene_retardo': tiene_retardo,
            'horas_extra_minutos': horas_extra_min,
            'tiene_horas_extra': tiene_horas_extra,
            'falta_entrada': falta_entrada,
            'falta_salida': falta_salida,
            'horas_trabajadas': horas_trabajadas,
            'registros_totales': len(records_dia),
            'estado': self._determinar_estado(falta_entrada, falta_salida, tiene_retardo, tiene_horas_extra)
        }

    def _calcular_retardo(self, hora_entrada_real):
        """Calcula minutos de retardo respecto a la hora de entrada esperada."""
        # Si la llegada es anterior o igual a la hora de entrada + tolerancia, no hay retardo
        entrada_base = datetime.combine(datetime.today(), self.hora_entrada)
        entrada_con_tolerancia = entrada_base + timedelta(minutes=self.limite_retardo_min)
        entrada_real = datetime.combine(datetime.today(), hora_entrada_real)

        if entrada_real <= entrada_con_tolerancia:
            return 0

        # Retardo = minutos que exceden la tolerancia
        retardo = (entrada_real - entrada_con_tolerancia).total_seconds() / 60
        return max(0, retardo)

    def _hora_salida_esperada(self, date):
        """Devuelve la hora de salida esperada según el día."""
        if date.weekday() == 5:  # sábado
            return self.hora_salida_sabado
        return self.hora_salida

    def _calcular_horas_extra(self, hora_salida_real, hora_salida_esperada):
        """Calcula minutos de horas extra respecto a la hora de salida esperada."""
        if hora_salida_real <= hora_salida_esperada:
            return 0
        
        salida_esperada = datetime.combine(datetime.today(), hora_salida_esperada)
        salida_real = datetime.combine(datetime.today(), hora_salida_real)
        horas_extra = (salida_real - salida_esperada).total_seconds() / 60
        return max(0, horas_extra)

    def _calcular_horas_trabajadas(self, hora_entrada, hora_salida):
        """Calcula total de horas trabajadas en un día."""
        entrada = datetime.combine(datetime.today(), hora_entrada)
        salida = datetime.combine(datetime.today(), hora_salida)
        horas = (salida - entrada).total_seconds() / 3600
        return round(horas, 2)

    def _determinar_estado(self, falta_entrada, falta_salida, tiene_retardo, tiene_horas_extra):
        """Determina el estado general del día."""
        if falta_entrada and falta_salida:
            return "Sin registros"
        if falta_entrada:
            return "Salida sin entrada"
        if falta_salida:
            return "Entrada sin salida"
        if tiene_retardo:
            return "Retardo"
        if tiene_horas_extra:
            return "Horas extra"
        return "Normal"

    def generar_resumen(self, df_procesado):
        """Genera resumen estadístico del período."""
        if df_procesado.empty:
            return {}

        return {
            'total_dias': len(df_procesado),
            'dias_normales': len(df_procesado[df_procesado['estado'] == 'Normal']),
            'dias_retardo': len(df_procesado[df_procesado['tiene_retardo']]),
            'dias_sin_entrada': len(df_procesado[df_procesado['falta_entrada']]),
            'dias_sin_salida': len(df_procesado[df_procesado['falta_salida']]),
            'dias_horas_extra': len(df_procesado[df_procesado['tiene_horas_extra']]),
            'total_retardo_minutos': df_procesado['retardo_minutos'].sum(),
            'total_horas_extra_minutos': df_procesado['horas_extra_minutos'].sum(),
            'promedio_horas_diarias': df_procesado['horas_trabajadas'].mean(),
        }
