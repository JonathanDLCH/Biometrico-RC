import unittest
from datetime import datetime
import pandas as pd
from src.data_processor import AttendanceProcessor

class TestAttendanceProcessor(unittest.TestCase):
    def setUp(self):
        """Crear procesador con horarios estándar."""
        self.processor = AttendanceProcessor(
            hora_entrada="08:00:00",
            hora_salida="17:00:00",
            limite_retardo_min=30
        )

    def test_procesar_registros_normal(self):
        """Test: día normal con entrada a tiempo y salida esperada."""
        records = [
            {
                "enrollid": 5,
                "name": "Juan Pérez",
                "time": "2026-04-15 08:00:00",
                "mode": 8,
                "inout": 0,
                "event": 0
            },
            {
                "enrollid": 5,
                "name": "Juan Pérez",
                "time": "2026-04-15 17:00:00",
                "mode": 8,
                "inout": 0,
                "event": 0
            }
        ]
        df = self.processor.procesar_registros(records)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['estado'], 'Normal')
        self.assertEqual(df.iloc[0]['retardo_minutos'], 0)

    def test_procesar_registros_retardo(self):
        """Test: día con retardo de 30 minutos."""
        records = [
            {
                "enrollid": 5,
                "name": "Juan Pérez",
                "time": "2026-04-15 08:30:00",
                "mode": 8,
                "inout": 0,
                "event": 0
            },
            {
                "enrollid": 5,
                "name": "Juan Pérez",
                "time": "2026-04-15 17:00:00",
                "mode": 8,
                "inout": 0,
                "event": 0
            }
        ]
        df = self.processor.procesar_registros(records)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['estado'], 'Retardo')
        self.assertEqual(df.iloc[0]['retardo_minutos'], 30)

    def test_procesar_registros_sin_salida(self):
        """Test: registro de entrada pero no salida."""
        records = [
            {
                "enrollid": 5,
                "name": "Juan Pérez",
                "time": "2026-04-15 09:00:00",
                "mode": 8,
                "inout": 0,
                "event": 0
            }
        ]
        df = self.processor.procesar_registros(records)
        self.assertEqual(len(df), 1)
        self.assertTrue(df.iloc[0]['falta_salida'])
        self.assertEqual(df.iloc[0]['estado'], 'Entrada sin salida')

    def test_generar_resumen(self):
        """Test: generar resumen de múltiples días."""
        records = [
            # Día 15 - Normal
            {
                "enrollid": 5,
                "name": "Juan Pérez",
                "time": "2026-04-15 08:00:00",
                "mode": 8,
                "inout": 0,
                "event": 0
            },
            {
                "enrollid": 5,
                "name": "Juan Pérez",
                "time": "2026-04-15 17:00:00",
                "mode": 8,
                "inout": 0,
                "event": 0
            },
            # Día 14 - Retardo
            {
                "enrollid": 5,
                "name": "Juan Pérez",
                "time": "2026-04-14 08:20:00",
                "mode": 8,
                "inout": 0,
                "event": 0
            },
            {
                "enrollid": 5,
                "name": "Juan Pérez",
                "time": "2026-04-14 17:00:00",
                "mode": 8,
                "inout": 0,
                "event": 0
            }
        ]
        df = self.processor.procesar_registros(records)
        resumen = self.processor.generar_resumen(df)
        
        self.assertEqual(resumen['total_dias'], 2)
        self.assertEqual(resumen['dias_normales'], 1)
        self.assertEqual(resumen['dias_retardo'], 1)

if __name__ == '__main__':
    unittest.main()
