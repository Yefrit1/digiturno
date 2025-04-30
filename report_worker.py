import pika, json, os
from dotenv import load_dotenv
from datetime import datetime
from report_generator import ReportGenerator
load_dotenv()

class ReportWorker:
    def __init__(self):
        self.reporter = ReportGenerator()
        self.setup_rabbitmq()
        self.check_and_generate_today()
        self.channel.basic_consume(
            queue='report_queue',
            on_message_callback=self.on_message,
            auto_ack=True
        )
        print("[*] Waiting for report requests. Press CTRL+C to exit.")
        self.channel.start_consuming()

    def setup_rabbitmq(self):
        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER"),
            os.getenv("RABBITMQ_PASS"))
        parameters = pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        self.channel = connection.channel()
        self.channel.queue_declare(queue='report_queue')

    def check_and_generate_today(self):
        today_str = datetime.today().strftime('%Y-%m-%d')
        report_path = f"reports/report_day_{today_str}.csv"
        if not os.path.exists(report_path):
            print("[+] Generating today's report...")
            result = self.reporter.generate_report(period="day", date=today_str)
            if result:
                print(f"[✓] Report saved: {result}")
            else:
                print("[~] No data for today's report.")

    def on_message(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            if data.get("command") == "generate_report":
                period = data.get("period", "day")
                date = data.get("date")
                print(f"[>] Generating report: {period}, {date or 'today'}")
                result = self.reporter.generate_report(period, date)
                if result:
                    print(f"[✓] Report generated: {result}")
                else:
                    print("[~] No data found for requested report.")
        except Exception as e:
            print(f"[!] Error processing message: {e}")

if __name__ == "__main__":
    try:
        ReportWorker()
    except KeyboardInterrupt:
        print("[x] Report worker stopped.")
