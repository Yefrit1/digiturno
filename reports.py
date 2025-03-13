import sqlite3, csv
from datetime import datetime

class ReportGenerator:
    def __init__(self, db_path='digiturno.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

    def daily_summary(self, date=None):
        """Generate daily summary report"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")

            query = """
                SELECT 
                    COUNT(*) AS total_turns,
                    SUM(CASE WHEN estado = 'atendido' THEN 1 ELSE 0 END) AS attended,
                    SUM(CASE WHEN estado = 'cancelado' THEN 1 ELSE 0 END) AS canceled,
                    ROUND(AVG((julianday(llamado) - julianday(creado)) * 1440), 1) AS avg_wait
                FROM turnos 
                WHERE DATE(creado) = ?
            """
            self.cursor.execute(query, (date,))
            return self.cursor.fetchone()
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        except e as Exception:
            print(f"Error: {e}")

    def employee_productivity(self, date=None):
        """Generate employee productivity report"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")

            query = """
                SELECT 
                    e.active_employee,
                    COUNT(t.id) AS turns_handled
                FROM estaciones e
                LEFT JOIN turnos t ON e.id = t.estacion_id
                WHERE DATE(t.llamado) = ?
                GROUP BY e.active_employee
            """
            self.cursor.execute(query, (date,))
            return self.cursor.fetchall()
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def station_load(self, date=None):
        """Generate station load report"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")

            query = """
                SELECT 
                    e.nombre,
                    e.servicio,
                    COUNT(t.id) AS turns_processed
                FROM estaciones e
                LEFT JOIN turnos t ON e.id = t.estacion_id
                WHERE DATE(t.llamado) = ?
                GROUP BY e.nombre
            """
            self.cursor.execute(query, (date,))
            return self.cursor.fetchall()
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def export_to_csv(self, data, headers, filename):
        """Export report data to CSV"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(data)
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False