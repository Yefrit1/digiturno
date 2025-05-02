import sqlite3, csv, os
from datetime import datetime, timedelta
db_path = 'digiturno.db'

class ReportGenerator:
    def __init__(self,):
        os.makedirs("reports", exist_ok=True)
    
    def generate_report(self, period, startDate, endDate=None):
        startDateTime = datetime.strptime(startDate, '%Y-%m-%d')
        match period:
            case 'day':
                endDateTime = datetime.strptime(startDate, '%Y-%m-%d') + timedelta(days=1)
                filename = f"report_{startDate}.csv"
            case 'week':
                startDateTime -= timedelta(days=startDateTime.weekday())
                endDateTime = startDateTime + timedelta(days=7)
                weekNum = startDateTime.isocalendar().week
                filename = f"report_{startDateTime.year}_week_{weekNum}.csv"
            case 'month':
                startDateTime = startDateTime.replace(day=1)
                nextMonth = startDateTime.replace(day=28) + timedelta(days=4)
                endDateTime = nextMonth.replace(day=1)
                filename = f"report_{startDateTime.year}_month_{startDateTime.month}.csv"
            case 'year':
                startDateTime = startDateTime.replace(month=1, day=1)
                endDateTime = datetime(startDateTime.year + 1, 1, 1)
                filename = f"report_year_{startDateTime.year}.csv"
            case 'custom' if endDate:
                endDateTime = datetime.strptime(endDate, '%Y-%m-%d') + timedelta(days=1)
                filename = f"report_from_{startDate}_to_{endDate}.csv"
            case _:
                print('Wrong args')
                return None
            
        startStr = startDateTime.strftime('%Y-%m-%d %H:%M:%S')
        endStr = endDateTime.strftime('%Y-%m-%d %H:%M:%S')
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
            ORDER BY t.creado ASC'''
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (startStr, endStr))
            rows = cursor.fetchall()
        if not rows:
            return None
        
        os.makedirs("reports", exist_ok=True)
        filepath = os.path.join("reports", filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Turno", "Cliente", "Creado", "Llamado", "Funcionario"])
            writer.writerows(rows)
        return filepath
