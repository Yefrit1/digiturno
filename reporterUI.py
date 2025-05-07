import sys, os, pika, json, traceback, threading, time, csv
from dotenv import load_dotenv
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
load_dotenv()

class MainWindow(QMainWindow):
    commandSignal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.screenGeometry = QApplication.primaryScreen().geometry()
        self.init_ui()
        self.setup_rabbitmq()
        self.commandSignal.connect(self.handle_command)
        self.ping_reporter()
        
    def init_ui(self):
        self.setWindowTitle("Digiturno reportes")
        self.setGeometry(int(self.screenGeometry.width()/2 - 500),
                         int(self.screenGeometry.height()/2 - 350), 1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.set_background_color(central_widget, "#EFE3C2")
        
        mainLayout = QVBoxLayout(central_widget)
        self.stackedWidget = QStackedWidget()
        mainLayout.addWidget(self.stackedWidget)
        
####### Layout 0 #######
        widget0 = QWidget()
        layout0 = QVBoxLayout(widget0)
        widget0.setLayout(layout0)
        #
        hWidget0 = QWidget()
        hBox0 = QHBoxLayout(hWidget0)
        hWidget0.setLayout(hBox0)
        
        self.startTxt = QLineEdit()
        labelHypen = QLabel('---')
        self.endTxt = QLineEdit()
        self.startTxt.editingFinished.connect(self.validate_date_input)
        self.endTxt.editingFinished.connect(self.validate_date_input)
        self.startTxt.focusInEvent = lambda e: self.active_field_changed('start')
        self.endTxt.focusInEvent = lambda e: self.active_field_changed('end')
        
        hBox0.addWidget(self.startTxt)
        hBox0.addWidget(labelHypen)
        hBox0.addWidget(self.endTxt)
        #
        self.calendar = QCalendarWidget()
        self.lastDate1 = self.calendar.selectedDate()
        self.lastDate2 = self.calendar.selectedDate()
        self.calendar_changed()
        self.calendar.selectionChanged.connect(self.calendar_changed)
        
        hWidget1 = QWidget()
        hBox1 = QHBoxLayout(hWidget1)
        hWidget1.setLayout(hBox1)
        
        vWidget0 = QWidget()
        vBox0 = QVBoxLayout(vWidget0)
        vWidget0.setLayout(vBox0)
        
        labelRange = QLabel('Rango de tiempo:')
        btnDay = QRadioButton('Día')
        btnWeek = QRadioButton('Semana')
        btnMonth = QRadioButton('Mes')
        btnYear = QRadioButton('Año')
        btnCustom = QRadioButton('Entre _ y _')
        self.btnGroup = QButtonGroup()
        self.btnGroup.addButton(btnDay, 0)
        self.btnGroup.addButton(btnWeek, 1)
        self.btnGroup.addButton(btnMonth, 2)
        self.btnGroup.addButton(btnYear, 3)
        self.btnGroup.addButton(btnCustom, 4)
        self.btnGroup.buttonToggled.connect(self.on_button_toggle)
        btnDay.setChecked(True)
        
        vBox0.addWidget(labelRange)
        vBox0.addWidget(btnDay)
        vBox0.addWidget(btnWeek)
        vBox0.addWidget(btnMonth)
        vBox0.addWidget(btnYear)
        vBox0.addWidget(btnCustom)
        
        vWidget1 = QWidget()
        vBox1 = QVBoxLayout(vWidget1)
        vWidget1.setLayout(vBox1)
        
        self.btnGenerate = QPushButton('Generar reporte')
        self.btnGenerate.clicked.connect(self.generate_pressed)
        self.btnPing = QPushButton('Ping servidor')
        self.btnPing.clicked.connect(self.ping_reporter)
        self.labelPing = QLabel('Sin conexión')
        self.labelPing.setAlignment(Qt.AlignRight)
        self.labelPing.setStyleSheet('font-weight: bold; color: red;')
        
        vBox1.addWidget(self.btnGenerate)
        vBox1.addStretch()
        vBox1.addWidget(self.labelPing)
        vBox1.addWidget(self.btnPing)
        
        hBox1.addWidget(vWidget0)
        hBox1.addWidget(vWidget1)
        #
        layout0.addWidget(hWidget0)
        layout0.addWidget(self.calendar)
        layout0.addWidget(hWidget1)

####### Layout 1 #######
        widget1 = QWidget()
        layout1 = QVBoxLayout(widget1)
        widget1.setLayout(layout1)
        #
        hWidget2 = QWidget()
        hBox2 = QHBoxLayout(hWidget2)
        hWidget2.setLayout(hBox2)
        
        btnReturn = QPushButton('Volver')
        btnSave = QPushButton('Guardar')
        
        btnReturn.clicked.connect(self.return_pressed)
        btnSave.clicked.connect(self.save_pressed)
        
        hBox2.addWidget(btnReturn)
        hBox2.addStretch()
        hBox2.addWidget(btnSave)
        #
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        
        self.reportTable = QTableWidget()
        self.reportTable.setColumnCount(6)
        self.reportTable.setHorizontalHeaderLabels(['Turno', 'Cliente', 'Asociado', 'Creado', 'Llamado', 'Funcionario'])
        
        scrollArea.setWidget(self.reportTable)
        #
        layout1.addWidget(hWidget2)
        layout1.addWidget(scrollArea)
        
####### Stack widgets #######
        self.stackedWidget.addWidget(widget0)
        self.stackedWidget.addWidget(widget1)
    
    def load_report(self):
        self.reportTable.clearContents()
        self.reportTable.setRowCount(len(self.rows))
        for rowIdx, row in enumerate(self.rows):
            for col, data in enumerate(row):
                self.reportTable.setItem(rowIdx, col, QTableWidgetItem(str(data)))
                self.reportTable.item(rowIdx, col).setTextAlignment(Qt.AlignCenter)
    
    def active_field_changed(self, field):
        self.activeField = field
        if field == 'start':
            self.endTxt.setStyleSheet('')
            self.startTxt.setStyleSheet('border: 2px solid black; background-color: #efffec;')
            self.calendar.setSelectedDate(self.lastDate1)
            self.calendar.setMinimumDate(QDate(1, 1, 1))
            self.calendar.setMaximumDate(self.lastDate2)
        else:
            self.startTxt.setStyleSheet('')
            self.endTxt.setStyleSheet('border: 2px solid black; background-color: #efffec;')
            self.calendar.setSelectedDate(self.lastDate2)
            self.calendar.setMaximumDate(QDate(9999, 12, 31))
            self.calendar.setMinimumDate(self.lastDate1)
    
    def validate_date_input(self):
        try:
            date1 = QDate.fromString(self.startTxt.text(), 'yyyy-MM-dd')
            date2 = QDate.fromString(self.endTxt.text(), 'yyyy-MM-dd')
            if date1.isValid() and date2.isValid():
                self.lastDate1 = date1
                self.lastDate2 = date2
                if self.activeField == 'start':
                    self.calendar.setSelectedDate(date1)
                else: self.calendar.setSelectedDate(date2)
            else: raise ValueError('Invalid date format')
        except ValueError:
            self.startTxt.setText(self.lastDate1.toString('yyyy-MM-dd'))
            self.endTxt.setText(self.lastDate2.toString('yyyy-MM-dd'))
    
    def calendar_changed(self):
        selected = self.calendar.selectedDate()
        if hasattr(self, 'activeField'):
            if self.activeField == 'start':
                self.lastDate1 = selected
            else:
                self.lastDate2 = selected
        else:
            self.lastDate1 = self.lastDate2 = selected
        self.startTxt.setText(self.lastDate1.toString('yyyy-MM-dd'))
        self.endTxt.setText(self.lastDate2.toString('yyyy-MM-dd'))
    
    def on_button_toggle(self, btn, checked):
        if not checked: return
        if self.btnGroup.checkedId() == 4:
            self.endTxt.setDisabled(False)
        else:
            self.active_field_changed('start')
            self.endTxt.setDisabled(True)
        
    def generate_pressed(self):
        end = None
        match self.btnGroup.checkedId():
            case 0: period = 'day'
            case 1: period = 'week'
            case 2: period = 'month'
            case 3: period = 'year'
            case 4:
                period = 'custom'
                end = self.endTxt.text()
        self.request_report(period, self.startTxt.text(), end)
        
    def return_pressed(self):
        self.stackedWidget.setCurrentIndex(0)
    
    def save_pressed(self):
        filePath, _ = QFileDialog.getSaveFileName(
            parent=self,
            caption='Guardar reporte',
            directory=self.filename,
            filter='CSV Files (*.csv);;All Files (*)')
        if filePath:
            with open(filePath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["Turno", "Cliente", "Asociado", "Creado", "Llamado", "Funcionario"])
                writer.writerows(self.rows)
        
    def setup_rabbitmq(self):
        credentials = pika.PlainCredentials(
            os.getenv('RABBITMQ_USER'),
            os.getenv('RABBITMQ_PASS'))
        parametersLocal = pika.ConnectionParameters(
            host=os.getenv('LOCAL_IP'),
            port=int(os.getenv('PORT')),
            credentials=credentials)
        parametersPublic = pika.ConnectionParameters(
            host=os.getenv('PUBLIC_IP'),
            port=int(os.getenv('PORT')),
            credentials=credentials)
        try:
            print('[~] Attempting to connect via public IP...')
            self.connection = pika.BlockingConnection(parametersPublic)
            print('[✓] Connected successfully.')
        except pika.exceptions.AMQPConnectionError:
            print('[!] Failed to connect via public IP.\n\n[~] Attempting to connect via local IP...')
            self.connection = pika.BlockingConnection(parametersLocal)
            print('[✓] Connected successfully.')
        except: traceback.print_exc()
        
        self.channel = self.connection.channel()
        self.channel.basic_consume(queue='amq.rabbitmq.reply-to',
            on_message_callback=self.handle_message,
            auto_ack=True)

        self.rabbitmq_thread = threading.Thread(
            target=self.start_consumer,
            daemon=True)
        self.rabbitmq_thread.start()
        
    def start_consumer(self):
        self.channel.start_consuming()
        
    def handle_message(self, channel, method, properties, body):
        try:
            message = body.decode('utf-8')
            self.commandSignal.emit(message)
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def handle_command(self, msg):
        msg = json.loads(msg)
        print(f'[>] Received command:\n{msg}')
        match msg.get('command'):
            case 'pong':
                self.labelPing.setText('Conectado')
                self.labelPing.setStyleSheet('font-weight: bold; color: green;')
            case 'report':
                self.rows = msg.get('data')
                self.filename = msg.get('filename')
                self.load_report()
                self.stackedWidget.setCurrentIndex(1)
    
    def ping_reporter(self):
        msgBody = {'command': 'ping'}
        self.channel.basic_publish(exchange="",
            routing_key="report_queue",
            properties=pika.BasicProperties(
                reply_to='amq.rabbitmq.reply-to',
                delivery_mode=1),
            body=json.dumps(msgBody))
        
    def request_report(self, period, start, end=None):
        msgBody = {'command': 'generate_report',
            'period': f'{period}',
            'from': f'{start}',
            'to': f'{end}'}
        self.channel.basic_publish(exchange="",
            routing_key="report_queue",
            properties=pika.BasicProperties(
                reply_to='amq.rabbitmq.reply-to',
                expiration='10000',
                delivery_mode=1),
            body=json.dumps(msgBody))
    
    def set_background_color(self, widget, color):
        palette = widget.palette()
        palette.setColor(QPalette.Background, QColor(color))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())