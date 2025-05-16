import sys, traceback, pika, time, json, uuid, threading, os, logging
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from dotenv import load_dotenv
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
load_dotenv()
handler = RotatingFileHandler('digiturnoFuncionario.log', maxBytes=500000, backupCount=3)
logging.basicConfig(
    filename='digiturnoFuncionario.log',
    level=logging.ERROR,
    format='%(asctime)s [%(levelname)s] %(message)s')

@dataclass
class Turn:
    id: int
    service: str
    number: int
    customer: str
    
    def to_dict(self):
        return{
            'id': self.id,
            'service': self.service,
            'number': self.number,
            'customer': self.customer}
    
    @staticmethod
    def from_dict(data: dict) -> 'Turn':
        return Turn(**data)

class MainWindow(QMainWindow):
    updateUIsignal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.screenGeometry = QApplication.primaryScreen().geometry()
        self.db_path = "digiturno.db"
        self.queues = {'AS': [], 'CA': [], 'CO': [], 'CT': []}
        """keys: queue (Str)
        elements: tuples:
        turnID (int), service (Str), number (int), customer (Str)"""
        self.rows = [0, 0, 0, 0]
        self.id = uuid.uuid4()
        self.userID = None
        self.currentTurnID = None
        self.connection = None
        self.channel = None
        self.init_ui()
        #self.setup_rabbitmq()
        self.updateUIsignal.connect(self.handle_server_update)

    def init_ui(self):
        self.setWindowTitle("Funcionario COOHEM")
        self.setGeometry(int(self.screenGeometry.width()/2 - 450),
                         int(self.screenGeometry.height()/10), 1000, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.set_background_color(central_widget, '#EFE3C2')
        layoutMain = QVBoxLayout(central_widget)
        layoutMain.setAlignment(Qt.AlignTop)

        # Logo and title
        hBox1 = QHBoxLayout()
        hBox1.setContentsMargins(10, 0, 10, 20)

        labelLogo = QLabel()
        labelLogo.setAlignment(Qt.AlignTop)
        pixmapLogo = QPixmap("logoCoohem.png")
        labelLogo.setPixmap(pixmapLogo)
        shadowLogo = QGraphicsDropShadowEffect(labelLogo, blurRadius=20)
        shadowLogo.setOffset(5, 5)
        labelLogo.setGraphicsEffect(shadowLogo)

        self.labelTitle = QLabel(f"Funcionario")
        self.style_label(self.labelTitle, 50, "#1D3C12")

        hBox1.addWidget(labelLogo)
        hBox1.addWidget(self.labelTitle)
        self.add_spacer(hBox1)

        # Current turn
        hBox2 = QHBoxLayout()
        hBox2.setContentsMargins(30, 0, 20, 30)

        labelAtendiendo = QLabel("Atendiendo: ")
        self.style_label(labelAtendiendo, 30, "#1D3C12")
        labelAtendiendo.setMinimumWidth(int(self.screenGeometry.width()*0.087))

        self.labelTurno = QLabel("-")
        self.style_label(self.labelTurno, 30, "#1D3C12")
        self.labelTurno.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        buttonTerminado = QPushButton("Terminado")
        self.style_button(buttonTerminado, 30)
        buttonTerminado.setFixedWidth(int(self.screenGeometry.width()/10))
        buttonTerminado.clicked.connect(self.complete_current_turn)
        

        hBox2.addWidget(labelAtendiendo)
        self.add_spacer(hBox2)
        hBox2.addWidget(self.labelTurno)
        self.add_spacer(hBox2)
        hBox2.addWidget(buttonTerminado)

        # Headers
        hBox3 = QHBoxLayout()
        hBox3.setContentsMargins(10, 0, 10, 0)

        labelAsesoria = QLabel("Asesoría")
        labelCaja = QLabel("Caja")
        labelCobranza = QLabel("Cobranza")
        labelCartera = QLabel("Cartera")

        self.style_label(labelAsesoria, 30, "#1D3C12")
        self.style_label(labelCaja, 30, "#1D3C12")
        self.style_label(labelCobranza, 30, "#1D3C12")
        self.style_label(labelCartera, 30, "#1D3C12")

        labelAsesoria.setMinimumWidth(int(self.screenGeometry.width()*0.1))
        labelCaja.setMinimumWidth(int(self.screenGeometry.width()*0.1))
        labelCobranza.setMinimumWidth(int(self.screenGeometry.width()*0.1))
        labelCartera.setMinimumWidth(int(self.screenGeometry.width()*0.1))

        hBox3.addWidget(labelAsesoria)
        hBox3.addWidget(labelCaja)
        hBox3.addWidget(labelCobranza)
        hBox3.addWidget(labelCartera)

        # Grid for turns
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollWidget = QWidget()
        scrollArea.setWidget(scrollWidget)
        self.gridTurns = QGridLayout(scrollWidget)
        self.gridTurns.setContentsMargins(10, 0, 10, 0)
        self.gridTurns.setAlignment(Qt.AlignTop)

        # Logout and cancel buttons
        hBox5 = QHBoxLayout()
        hBox5.setContentsMargins(10, 0, 10, 0)

        buttonLogout = QPushButton("Cerrar sesión")
        self.style_button(buttonLogout, 25, "#C9671C")
        buttonLogout.clicked.connect(self.log_out)
        
        buttonReassign = QPushButton('Reasignar turno')
        self.style_button(buttonReassign, 25, '#618cff')
        buttonReassign.clicked.connect(self.reassign_pressed)

        buttonCancel = QPushButton("Cancelar turno")
        self.style_button(buttonCancel, 25, "#A01919")
        buttonCancel.clicked.connect(self.cancel_current_turn)

        buttonLogout.setMinimumSize(100, 75)
        buttonReassign.setMinimumSize(100, 75)
        buttonCancel.setMinimumSize(100, 75)
        buttonLogout.setMaximumSize(200, 100)
        buttonReassign.setMaximumSize(200, 100)
        buttonCancel.setMaximumSize(200, 100)

        hBox5.addWidget(buttonLogout)
        self.add_spacer(hBox5)
        hBox5.addWidget(buttonReassign)
        hBox5.addWidget(buttonCancel)

        # Add layouts to main layout
        layoutMain.addLayout(hBox1)
        layoutMain.addLayout(hBox2)
        layoutMain.addLayout(hBox3)
        layoutMain.addWidget(scrollArea)
        layoutMain.addLayout(hBox5)

    def add_pending_turn(self, turnID, service, number, queue, customer=None):
        """Add turn to GUI. Does NOT add turn to self.queues"""
        match queue:
            case 'AS': col = 0
            case 'CA': col = 1
            case 'CO': col = 2
            case 'CT': col = 3
        gridWidget = QWidget()
        gridHbox = QHBoxLayout(gridWidget)
        gridHbox.setSpacing(0)
        gridWidget.setLayout(gridHbox)

        turno = QWidget()
        turno.setMinimumWidth(int(self.screenGeometry.width()/20))
        turno.setMaximumSize(int(self.screenGeometry.width()/6), 100)
        self.format_turn(turno, f"{service}-{number}", f"{customer}")

        llamar = QPushButton("Llamar")
        llamar.setMinimumWidth(70)
        llamar.setMaximumSize(90, 100)
        self.style_button(llamar, 20)
        llamar.clicked.connect(lambda _, t=turnID, q=queue: self.call_next_turn(t, q))

        self.add_spacer(gridHbox)
        gridHbox.addWidget(turno)
        gridHbox.addWidget(llamar)
        self.add_spacer(gridHbox)
        self.gridTurns.addWidget(gridWidget, self.rows[col], col)
        self.rows[col] += 1

    def update_grid(self):
        self.clear_grid()
        self.grid_spacers()
        self.load_pending()

    def clear_grid(self):
        self.rows = [0, 0, 0, 0]
        while self.gridTurns.count():
            item = self.gridTurns.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def grid_spacers(self):
        for i in range(4):
            expanding_spacer = QSpacerItem(500, 20, QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.gridTurns.addItem(expanding_spacer, 0, i)

    def load_pending(self):
        for queue, turns in self.queues.items():
            for turn in turns:
                self.add_pending_turn(turn.id, turn.service, turn.number, queue, turn.customer)
    
    def remove_turn(self, turnID, queue):
        for turn in self.queues[queue]:
            if turn.id == int(turnID):
                turnRemoving = Turn(
                    id=int(turnID),
                    service=turn.service,
                    number=turn.number,
                    customer=turn.customer)
                break
        print(f"Removing {turnRemoving} from {queue}")
        self.queues[queue].remove(turnRemoving)

    def update_called_turn(self, turnID, queue):
        print('Updating turn label')
        for turn in self.queues[queue]:
            print(f'Iterating over {turn}')
            if turn.id == int(turnID):
                print('Got ID match (line 242)')
                service = turn.service
                number = turn.number
                customer = turn.customer
                break
        self.currentTurnID = int(turnID)
        self.labelTurno.setText(f"{service}-{number} . {customer}")

    def handle_server_update(self, message):
        print(f"Handling message:\n{message}\n")
        try:
            if message.startswith("NEW_TURN:"):
                _, turnID, turnInfo, queue, customer = message.split(':')
                service, number = turnInfo.split('-')
                self.queues[queue].append(Turn(
                    id=int(turnID),
                    service=service,
                    number=int(number),
                    customer=customer))
                self.add_pending_turn(turnID, service, number, queue, customer)
            
            elif message.startswith("CALLED:"):
                _, turnID, queue, user = message.split(':')
                print(f"Queue before called:\n{self.queues}\n")
                if int(user) == self.userID: self.update_called_turn(turnID, queue)
                self.remove_turn(turnID, queue)
                self.update_grid()
            
            elif message.startswith('ACK_STATIONS_REQUEST:'):
                stations = json.loads(message[len('ACK_STATIONS_REQUEST:'):])
                self.dialog.stationMenu.addItems(stations)
            
            elif message.startswith("ACK_LOGIN_REQUEST:"):
                _, userID, userName, station = message.split(':')
                self.dialog.verify_credentials(userID, userName, station)
                
            elif message.startswith('ACK_REASSIGN_TURN:'):
                _, turnID, turnInfo, queue, customer, rk = message.split(':')
                service, number = turnInfo.split('-')
                self.queues[queue].append(Turn(
                    id=int(turnID),
                    service=service,
                    number=int(number),
                    customer=customer))
                self.add_pending_turn(turnID, service, number, queue, customer)
                if rk == str(self.id):
                    self.currentTurnID = None
                    self.labelTurno.setText('-')
            
            elif message.startswith('ACK_CANCEL_TURN') or message.startswith('ACK_COMPLETE_TURN'):
                self.currentTurnID = None
                self.labelTurno.setText("-")
            
            else:
                self.deserialize_queues(json.loads(message))
                self.update_grid()
        except:
            logging.exception('Exception handling command')
            traceback.print_exc()

    def style_label(self, label, fontSize, color):
        styleSheet = f"""
            QLabel {{
                color: {color};
                font-size: {fontSize}px;
            }}
        """
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(styleSheet)
    
    def style_button(self, button, fontSize, color=None):
        styleSheet = f"""
            QPushButton {{
                background-color: #669A0D;
                color: white;
                font-size: {fontSize}px;
            }}
        """
        if color:
            styleSheet += f"""
            QPushButton {{
                background-color: {color};
            }}
        """
        button.setStyleSheet(styleSheet)

    def format_turn(self, widget, turn, name):
        widget.setStyleSheet("QWidget {background-color: #3E7B27;}")
        layout = QVBoxLayout(widget)
        label = QLabel(f"{turn}<br>{name}")
        label.setAlignment(Qt.AlignCenter)
        self.style_label(label, 30, "white")
        layout.addWidget(label)

    def add_spacer(self, layout, width=None, height=None, expanding=None):
        label = QLabel()
        if width:
            label.setFixedWidth(width)
        if height:
            label.setFixedHeight(height)
        if expanding:
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(label)
    
    def deserialize_queues(self, queues:dict):
        self.queues = {
            queue:[Turn.from_dict(turn) for turn in turns]
            for queue, turns in queues.items()}

    def screen_width(self, num):
        return int(self.screenGeometry.width()*num/100)
    
    def screen_height(self, num):
        return int(self.screenGeometry.height()*num/100)

    def show_login(self):
        self.dialog = LoginDialog(self)
        self.setup_rabbitmq()
        self.get_stations()
        self.loggedOut = False
        if self.dialog.exec_() == QDialog.Accepted:
            self.userID = self.dialog.userID
            self.nombreF = self.dialog.name
            self.station = self.dialog.station
            self.labelTitle.setText(f"{self.nombreF}")
            self.request_queue()
            self.show()
        else:
            self.close()

    def log_out(self):
        reply = QMessageBox(self)
        reply.setWindowTitle('Cerrar sesión')
        reply.setText('¿Seguro que desea cerrar sesión?')
        reply.setIcon(QMessageBox.Icon.Question)
        btnSi = reply.addButton('Sí', QMessageBox.ButtonRole.YesRole)
        btnNo = reply.addButton('No', QMessageBox.ButtonRole.NoRole)
        reply.setDefaultButton(btnNo)
        reply.exec()
        if reply.clickedButton() == btnSi:
            time.sleep(0.1)
            self.userID = None
            self.currentTurnID = None
            self.labelTurno.setText("-")
            self.loggedOut = True
            self.release_station()
            self.close()
            self.show_login()

    def set_background_color(self, widget, color):
        palette = widget.palette()
        palette.setColor(QPalette.Background, QColor(color))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)

    def setup_rabbitmq(self):
        try:
            credentials = pika.PlainCredentials(os.getenv("RABBITMQ_USER"), os.getenv("RABBITMQ_PASS"))
            parameters = pika.ConnectionParameters(
                host=os.getenv('LOCAL_IP'),
                port=int(os.getenv('PORT')),
                credentials=credentials)
                #heartbeat=30,
                #blocked_connection_timeout=5,
                #connection_attempts=3,
                #retry_delay=1)
            self.connection = pika.BlockingConnection(parameters)
            print(f"Connection status: {self.connection.is_open}")
            self.channel = self.connection.channel()
            self.channel.exchange_declare(
                exchange='digiturno_direct',
                exchange_type='direct',
                durable=True)
            self.setup_consumers()
            self.rabbitmqThread = threading.Thread(
                target=self.start_consumer,
                daemon=True)
            self.rabbitmqThread.start()
        except Exception as e:
            logging.exception('Exception setting up RabbitMQ')
            print(f"Error setting up rabbitmq: {e}\nRetrying in 5 seconds...")
            QTimer.singleShot(5000, self.setup_rabbitmq)
    
    def setup_consumers(self):
        """Declare consumer queues and bindings"""
        self.channel.queue_declare(queue=f'broadcast_queue_{self.id}', durable=True, auto_delete=True)
        self.channel.queue_bind(
            exchange='digiturno_broadcast',
            queue=f'broadcast_queue_{self.id}',
            routing_key='')
        self.channel.queue_declare(queue=f'ack_queue_{self.id}', durable=True, auto_delete=True)
        self.channel.queue_bind(
            exchange='ack_exchange',
            queue=f'ack_queue_{self.id}',
            routing_key=str(self.id))
        self.channel.basic_consume(
            queue=f'broadcast_queue_{self.id}',
            on_message_callback=self.handle_message,
            auto_ack=True)
        self.channel.basic_consume(
            queue=f'ack_queue_{self.id}',
            on_message_callback=self.handle_message,
            auto_ack=True)

    def start_consumer(self):
        try: self.channel.start_consuming()
        except: pass

    def handle_message(self, channel, method, properties, body):
        try:
            message = body.decode('utf-8')
            self.updateUIsignal.emit(message)
        except:
            logging.exception('Exception handling message')
            traceback.print_exc()
            
    def get_stations(self):
        print('Getting stations...')
        try:
            self.channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=f'STATIONS_REQUEST:{self.id}',
                properties=pika.BasicProperties(delivery_mode=2))
        except:
            logging.exception('Exception sending stations request')
            traceback.print_exc()

    def request_verification(self, username, password, station):
        try:
            self.channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=f'LOGIN_REQUEST:{username}:{password}:{station}:{self.id}',
                properties=pika.BasicProperties(delivery_mode=2))
        except:
            logging.exception('Exception requesting verification')
            traceback.print_exc()
            self.setup_rabbitmq()

    def request_queue(self):
        try:
            self.channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=f'QUEUE_REQUEST:{self.id}')
        except:
            logging.exception('Exception requesting queue')
            traceback.print_exc()
            self.setup_rabbitmq()

    def call_next_turn(self, turnID, queue):
        try:
            self.channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=f'NEXT_TURN:{self.userID}:{turnID}:{queue}:{self.station}:{self.id}')
        except:
            logging.exception('Exception calling next turn')
            traceback.print_exc()
            self.setup_rabbitmq()

    def complete_current_turn(self):
        try:
            self.channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=f'COMPLETE_TURN:{self.station}:{self.id}')
        except:
            logging.exception('Exception sending turn completion')
            traceback.print_exc()

    def cancel_current_turn(self):
        if self.currentTurnID:
            reply = QMessageBox(self)
            reply.setWindowTitle('Cancelar turno')
            reply.setText('¿Seguro que desea cancelar el turno?')
            reply.setIcon(QMessageBox.Icon.Question)
            btnSi = reply.addButton('Sí', QMessageBox.ButtonRole.YesRole)
            btnNo = reply.addButton('No', QMessageBox.ButtonRole.NoRole)
            reply.setDefaultButton(btnNo)
            reply.exec()
            if reply.clickedButton() == btnSi:
                try:
                    self.channel.basic_publish(
                        exchange='digiturno_direct',
                        routing_key='server_command',
                        body=f'CANCEL_TURN:{self.currentTurnID}:{self.station}:{self.userID}:{self.id}')
                except:
                    logging.exception('Exception canceling current turn')
                    traceback.print_exc()
                    self.setup_rabbitmq()
    
    def reassign_pressed(self):
        if self.currentTurnID:
            selection = QMessageBox()
            selection.setWindowTitle('Reasignar turno')
            selection.setText('¿A qué servicio desea reasignar el turno?')
            btnAsesoria = selection.addButton('Asesoría', QMessageBox.ButtonRole.AcceptRole)
            btnCaja = selection.addButton('Caja', QMessageBox.ButtonRole.AcceptRole)
            btnCobranza = selection.addButton('Cobranza', QMessageBox.ButtonRole.AcceptRole)
            btnCartera = selection.addButton('Cartera', QMessageBox.ButtonRole.AcceptRole)
            btnCancel = QPushButton()
            selection.addButton(btnCancel, QMessageBox.ButtonRole.RejectRole)
            btnCancel.hide()
            selection.exec()
            if selection.clickedButton() == btnAsesoria:
                self.reassign_turn('AS')
            elif selection.clickedButton() == btnCaja:
                self.reassign_turn('CA')
            elif selection.clickedButton() == btnCobranza:
                self.reassign_turn('CO')
            elif selection.clickedButton() == btnCartera:
                self.reassign_turn('CT')
    
    def reassign_turn(self, queue):
        try:
            msgBody = f'REASSIGN_TURN:{self.currentTurnID}:{queue}:{self.station}:{self.userID}:{self.id}'.encode('utf-8')
            self.channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=msgBody)
        except: logging.exception('Exception sending turn reassignment')
    
    def release_station(self):
        try:
            print('Releasing station...')
            self.channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=f'RELEASE_STATION:{self.station}',
                properties=pika.BasicProperties(delivery_mode=2))
            print('Station released')
        except Exception as e: print(f'releasing station got: {e}')

    def cleanup_connections(self):
        """For some reason, when I try to safely close connections, stop consumer and join the thread, it throws an error on exit"""
        print('Closing connections...')
        try: self.channel.stop_consuming()
        except: pass
        try: self.rabbitmqThread.join()
        except: pass
        print('Connections closed')

    def closeEvent(self, event):
        print('Executing client\'s closeEvent...')
        if not self.loggedOut:
            print('Condition met')
            self.release_station()
            #self.cleanup_connections()
            print('Closing client...')
            os._exit(0)
        print('Closing client...')
        super().closeEvent(event)
        print('Client closed')

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.screenGeometry = QApplication.primaryScreen().geometry()
        self.setWindowTitle("Iniciar sesión")
        self.setStyleSheet("background-color: #EFE3C2;")
        self.setGeometry(int(self.screenGeometry.width()/2 - 200),
                         int(self.screenGeometry.height()/2 - 100), 400, 200)
        self.layout = QVBoxLayout()
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("Usuario")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Contraseña")
        self.password.setEchoMode(QLineEdit.Password)
        self.stationMenu = QComboBox()
        
        self.loginButton = QPushButton("Iniciar sesión")
        self.loginButton.clicked.connect(self.request_verification_dialog)
        
        self.layout.addWidget(self.username)
        self.layout.addWidget(self.password)
        self.layout.addWidget(self.stationMenu)
        self.layout.addWidget(self.loginButton)
        self.setLayout(self.layout)

    def request_verification_dialog(self):
        if self.username.text() != "" and self.password.text() != "" and self.stationMenu.currentText() != "":
            client.request_verification(self.username.text(), self.password.text(), self.stationMenu.currentText())
        else:
            QMessageBox.warning(self, "Error", "Llene todos los campos.")

    def verify_credentials(self, userID, name, station):
        if userID == 'NOT_FOUND':
            QMessageBox.warning(self, "Error", "Credenciales inválidas.")
        elif userID == 'NO_ACCESS':
            QMessageBox.warning(self, "Error", "Funcionario bloqueado.")
        elif userID == 'STATION_BUSY':
            QMessageBox.warning(self, "Error", "Estación en uso.")
        else:
            self.userID = int(userID)
            self.name = name
            self.station = station
            self.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = MainWindow()
    client.show_login()
    sys.exit(app.exec_())