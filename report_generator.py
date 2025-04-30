import sqlite3
import csv
import os
from datetime import datetime, timedelta

class ReportGenerator:
    def __init__(self, db_path='digiturno.db'):
        self.db_path = db_path
        os.makedirs("reports", exist_ok=True)

    def generate_report(self, period='day', date=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if date:
                base_date = datetime.strptime(date, "%Y-%m-%d")
            else:
                base_date = datetime.today()

            start_date, end_date = self._get_date_range(period, base_date)

            query = '''
                SELECT
                    t.servicio || '-' || t.numero AS turno,
                    c.nombre AS cliente,
                    t.creado,
                    t.llamado,
                    f.nombre AS funcionario
                FROM turnos t
                JOIN clientes c ON t.cliente_id = c.id
                LEFT JOIN funcionarios f ON t.funcionario_id = f.id
                WHERE t.creado BETWEEN ? AND ?
                ORDER BY t.creado ASC
            '''
            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()

        if not rows:
            return None  # No report generated

        filename = f"report_{period}_{base_date.strftime('%Y-%m-%d')}.csv"
        filepath = os.path.join("reports", filename)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Turno", "Cliente", "Creado", "Llamado", "Funcionario"])
            writer.writerows(rows)

        return filepath

    def _get_date_range(self, period, base_date):
        if period == 'day':
            start = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == 'week':
            start = base_date - timedelta(days=base_date.weekday())
            end = start + timedelta(days=7)
        elif period == 'month':
            start = base_date.replace(day=1)
            next_month = start.replace(day=28) + timedelta(days=4)
            end = next_month.replace(day=1)
        elif period == 'year':
            start = base_date.replace(month=1, day=1)
            end = base_date.replace(month=12, day=31) + timedelta(days=1)
        else:  # all
            start = '0001-01-01 00:00:00'
            end = '9999-12-31 23:59:59'
            return start, end

        return start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S')
