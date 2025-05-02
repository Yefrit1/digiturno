import pika, json, os, sqlite3, traceback, csv, io
from b2sdk.v2 import B2Api, InMemoryAccountInfo
from datetime import datetime, timedelta
from dotenv import load_dotenv
db_path = 'digiturno.db'
load_dotenv()

class Reporter:
    def __init__(self):
        os.makedirs("reports", exist_ok=True)
        self.setup_rabbitmq()
        self.channel.basic_consume(
            queue='report_queue',
            on_message_callback=self.on_message,
            auto_ack=True)
        print("[*] Waiting for report requests. Press CTRL+C to exit.")
        self.channel.start_consuming()

    def setup_rabbitmq(self):
        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER"),
            os.getenv("RABBITMQ_PASS"))
        parameters = pika.ConnectionParameters('localhost', credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        self.channel = connection.channel()
        self.channel.queue_declare(queue='report_queue', durable=True)

    def on_message(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            print(f'[>] Received command: {data}')

            if data.get('command') != 'generate_report':
                print("[~] Unknown command.")
                return

            period = data.get('period', 'day')
            start = data.get('from')
            end = data.get('to')
            action = data.get('action', 'send')

            rows, startDateTime = self.generate_report(period, start, end)
            if not rows:
                print('[~] No data found for requested report.')
                return

            if action == 'save':
                filename = self.build_filename(period, startDateTime, end)
                filepath = os.path.join("reports", filename)
                with open(filepath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Turno", "Cliente", "Creado", "Llamado", "Funcionario"])
                    writer.writerows(rows)
                print(f'[✓] Report saved to {filepath}')
                
                url = self.upload_to_b2(filepath, filename)
                if url and properties.reply_to:
                    self.channel.basic_publish(
                        exchange='',
                        routing_key=properties.reply_to,
                        body=json.dumps({"url": url}).encode("utf-8")
                    )

            elif action == 'send':
                multirows = []
                for i in range(15101):
                    multirows.append(rows)
                #output = io.StringIO()
                #writer = csv.writer(output)
                #writer.writerows(multirows)
                #csv_string = output.getvalue()
                self.channel.basic_publish(
                    exchange='',
                    routing_key=properties.reply_to,
                    #body=csv_string.encode("utf-8"))
                    body=json.dumps(multirows))
                print('[✓] Report sent to reply queue')

            else:
                print(f"[!] Unknown action: {action}")

        except Exception as e:
            traceback.print_exc()
        
    def generate_report(self, period, startDate, endDate=None):
        startDateTime = datetime.strptime(startDate, '%Y-%m-%d')
        match period:
            case 'day':
                endDateTime = startDateTime + timedelta(days=1)
            case 'week':
                startDateTime -= timedelta(days=startDateTime.weekday())
                endDateTime = startDateTime + timedelta(days=7)
            case 'month':
                startDateTime = startDateTime.replace(day=1)
                endDateTime = (startDateTime.replace(day=28) + timedelta(days=4)).replace(day=1)
            case 'year':
                startDateTime = startDateTime.replace(month=1, day=1)
                endDateTime = datetime(startDateTime.year + 1, 1, 1)
            case 'custom' if endDate:
                endDateTime = datetime.strptime(endDate, '%Y-%m-%d') + timedelta(days=1)
            case _:
                print("[!] Invalid period or missing 'to' for custom.")
                return None, None

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
        return rows, startDateTime

    def build_filename(self, period, startDateTime, endDate=None):
        match period:
            case 'day':
                return f"report_{startDateTime.date()}.csv"
            case 'week':
                weekNum = startDateTime.isocalendar().week
                return f"report_{startDateTime.year}_week_{weekNum}.csv"
            case 'month':
                return f"report_{startDateTime.year}_month_{startDateTime.month}.csv"
            case 'year':
                return f"report_year_{startDateTime.year}.csv"
            case 'custom' if endDate:
                return f"report_from_{startDateTime.date()}_to_{endDate}.csv"
            case _:
                return "report.csv"
    
    def upload_to_b2(self, filepath, filename):
        try:
            info = InMemoryAccountInfo()
            b2_api = B2Api(info)
            b2_api.authorize_account("production", os.getenv("B2_KEY_ID"), os.getenv("B2_APP_KEY"))
            bucket = b2_api.get_bucket_by_name(os.getenv("B2_BUCKET"))
            authorization = bucket.get_download_authorization(filename, 3600)
            with open(filepath, 'rb') as file:
                bucket.upload_bytes(file.read(), filename)
            
            url = bucket.get_download_url(filename)
            downloadURL = f'{url}?Authorization={authorization}'
            print(f"[✓] Uploaded to B2: {downloadURL}")
            return downloadURL
        except Exception as e:
            print("[!] Failed to upload to B2")
            traceback.print_exc()
            return None

if __name__ == "__main__":
    try:
        Reporter()
    except KeyboardInterrupt:
        print("[x] Report worker stopped.")
