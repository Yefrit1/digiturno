import pika, json, os, sqlite3, traceback
from dotenv import load_dotenv
from datetime import datetime, timedelta
from report_generator import ReportGenerator
db_path = 'digiturno.db'
load_dotenv()

class ReportWorker:
    def __init__(self):
        self.reporter = ReportGenerator()
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
            print(f'[>] Handling command: {data}')
            if data.get('command') == 'generate_report':
                period = data.get('period', 'day')
                startDate = data.get('from')
                endDate = data.get('to')
                print(f'[>] Generating report: {period}, {startDate or "today"}')
                match data.get('action'):
                    case 'save':
                        result = self.reporter.generate_report(period, startDate)
                        if result:
                            print(f'[✓] Report generated: {result}')
                        else:
                            print('[~] No data found for requested report.')
                    case 'get':
                        pass
        except Exception as e:
            #print(f"[!] Error processing message: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    try:
        ReportWorker()
    except KeyboardInterrupt:
        print("[x] Report worker stopped.")
