import sys, sqlite3, traceback, pika, threading, time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class MainWindow(QMainWindow):
    updateUIsignal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.screenGeometry = QApplication.primaryScreen().geometry()
        self.db_path = "digiturno.db"
        self.queue = {'AS': [], 'CA': [], 'CO': [], 'CT': []}
        self.userID = None
        self.shutdownFlag = False
        self.connectionLock = threading.Lock()
        self.pendingRequests = {}
        self.init_ui()
        self.setup_rabbitmq()
        self.updateUIsignal.connect(self.handle_server_update)
    
    def init_ui(self):
        self.setWindowTitle("Funcionario COOHEM")
        self.setGeometry(int(self.screenGeometry.width()/2 - 450),
                         int(self.screenGeometry.height()/10), 900, 600)
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
        labelAtendiendo.setMinimumWidth(self.screen_width(8.7))

        self.labelTurno = QLabel("-")
        self.style_label(self.labelTurno, 30, "#1D3C12")
        self.labelTurno.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        #self.labelTurno.setSizePolicy()

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

        labelAsesoria.setMinimumWidth(self.screen_width(10))
        labelCaja.setMinimumWidth(self.screen_width(10))
        labelCobranza.setMinimumWidth(self.screen_width(10))
        labelCartera.setMinimumWidth(self.screen_width(10))

        hBox3.addWidget(labelAsesoria)
        hBox3.addWidget(labelCaja)
        hBox3.addWidget(labelCobranza)
        hBox3.addWidget(labelCartera)

        # Grid for turns
        hBox4 = QHBoxLayout()
        hBox3Widget = QWidget()
        self.gridTurns = QGridLayout(hBox3Widget)
        self.gridTurns.setContentsMargins(10, 0, 10, 0)
        
        # Load pending turns from DB
        self.update_grid()

        hBox4.addWidget(hBox3Widget)

        # Logout and cancel buttons
        hBox5 = QHBoxLayout()
        hBox5.setContentsMargins(10, 0, 10, 0)

        buttonLogout = QPushButton("Cerrar sesión")
        self.style_button(buttonLogout, 25, "#C9671C")
        buttonLogout.clicked.connect(self.log_out)

        buttonCancel = QPushButton("Cancelar turno")
        self.style_button(buttonCancel, 25, "#A01919")
        buttonCancel.clicked.connect(self.cancel_current_turn)

        buttonLogout.setMinimumSize(100, 75)
        buttonCancel.setMinimumSize(100, 75)
        buttonLogout.setMaximumSize(200, 100)
        buttonCancel.setMaximumSize(200, 100)

        hBox5.addWidget(buttonLogout)
        self.add_spacer(hBox5)
        hBox5.addWidget(buttonCancel)

        # Add layouts to main layout
        layoutMain.addLayout(hBox1)
        layoutMain.addLayout(hBox2)
        layoutMain.addLayout(hBox3)
        layoutMain.addLayout(hBox4)
        layoutMain.addStretch()
        layoutMain.addLayout(hBox5)

    def add_pending_turn(self, servicio, numero, nombre=None):
        row = len(self.queue[servicio]) - 1
        if row < 4:
            gridWidget = QWidget()
            gridHbox = QHBoxLayout(gridWidget)
            gridHbox.setSpacing(0)
            gridWidget.setLayout(gridHbox)

            turno = QWidget()
            turno.setMinimumWidth(int(self.screenGeometry.width()/20))
            turno.setMaximumWidth(int(self.screenGeometry.width()/6))
            self.format_turn(turno, f"{servicio}-{numero}", f"{nombre}")

            llamar = QPushButton("Llamar")
            llamar.setMinimumWidth(70)
            llamar.setMaximumSize(90, 100)
            self.style_button(llamar, 20)
            llamar.clicked.connect(lambda _, s=servicio, n=numero: self.call_next_turn(s, n))

            self.add_spacer(gridHbox)
            gridHbox.addWidget(turno)
            gridHbox.addWidget(llamar)
            self.add_spacer(gridHbox)
            match servicio:
                case 'AS': col = 0
                case 'CA': col = 1
                case 'CO': col = 2
                case 'CT': col = 3
            self.gridTurns.addWidget(gridWidget, row, col)

    def update_grid(self):
        self.clear_grid()
        for i in range(4):
            expanding_spacer = QSpacerItem(500, 20, QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.gridTurns.addItem(expanding_spacer, 0, i)
        self.load_pending()

    def clear_grid(self):
        self.queue = {key: [] for key in self.queue} # Clear queue dict
        while self.gridTurns.count():
            item = self.gridTurns.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def load_pending(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT t.servicio, t.numero, c.nombre
                    FROM turnos t
                    JOIN clientes c ON t.cliente_id = c.id
                    WHERE t.estado = 'pendiente'
                    AND DATE(t.creado) = DATE('now')
                    ORDER BY t.creado
                ''')
                for servicio, numero, nombre in cursor.fetchall():
                    self.queue[servicio].append(numero)
                    self.add_pending_turn(servicio, numero, nombre)
        except:
            traceback.print_exc()
            print("^Error loading turns. Read traceback above^")

    def update_called_turn(self, servicio, numero, nombre):
        self.labelTurno.setText(f"{servicio}-{numero} . {nombre}")

    def handle_server_update(self, message):
        print(f"Handling server update: {message}")
        try:
            if message == "RECONNECT_RABBITMQ":
                self.setup_rabbitmq()
            elif message.startswith("NEW_TURN:"):
                _, turnInfo, nombre = message.split(':')
                servicio, numero = turnInfo.split('-')
                self.queue[servicio].append(numero)
                self.add_pending_turn(servicio, numero, nombre)

            elif message.startswith("CALLED:"):
                _, turnInfo = message.split(':')
                servicio, numero = turnInfo.split('-')
                print("updating grid...")
                self.update_grid()
                print("grid updated")

            elif message.startswith("COMPLETED:"):
                _, turnInfo = message.split(':')
                servicio, numero = turnInfo.split('-')
                self.update_grid()
        except:
            traceback.print_exc()
            print("^Error handling server update. Read traceback above^")

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

    def screen_width(self, num):
        """Returns pixel value of screen width % based on parameter"""
        return int(self.screenGeometry.width()*num/100)
    def screen_height(self, num):
        """Returns pixel value of screen height % based on parameter"""
        return int(self.screenGeometry.height()*num/100)

    def show_login(self):
        dialog = LoginDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            print(f"Current User ID: {dialog.userID}")
            self.userID = dialog.userID
            self.labelTitle.setText(f"Funcionario {self.userID}")
            self.shutdownFlag = False
            self.setup_rabbitmq()
            self.show()
        else:
            self.close()

    def log_out(self):
        self.shutdownFlag = True
        
        time.sleep(0.1)
        self.cleanup_connections()

        self.userID = None
        self.close()
        self.show_login()

    def set_background_color(self, widget, color):
        palette = widget.palette()
        palette.setColor(QPalette.Background, QColor(color))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)
        
    def setup_rabbitmq(self):
        try:
            if not self.connectionLock.acquire(blocking=False):
                print("Could not acquire lock for RabbitMQ")
                return
            try:
                self.unsafe_cleanup_connections()

                parameters = pika.ConnectionParameters(
                    host='localhost',
                    heartbeat=15,
                    blocked_connection_timeout=2,
                    connection_attempts=5,
                    retry_delay=1)
                
                self.command_connection = pika.BlockingConnection(parameters)
                self.command_channel = self.command_connection.channel()
                
                self.broadcast_connection = pika.BlockingConnection(parameters)
                self.broadcast_channel = self.broadcast_connection.channel()

                self.ack_connection = pika.BlockingConnection(parameters)
                self.ack_channel = self.ack_connection.channel()
                
                self.command_channel.exchange_declare(
                    exchange='ack_exchange',
                    exchange_type='direct',
                    durable=True)

                if self.userID:
                    self.ack_queue = f'ack_queue_{self.userID}'
                    self.ack_channel.queue_declare(
                        queue=self.ack_queue,
                        exclusive=True)

                    self.ack_channel.queue_bind(
                        exchange='ack_exchange',
                        queue=self.ack_queue,
                        routing_key=str(self.userID))
                    
                    self.ack_channel.basic_consume(
                        queue=self.ack_queue,
                        on_message_callback=self.handle_ack,
                        auto_ack=True)
                    
                    self.ack_thread = threading.Thread(
                        target=self.start_ack_consumer,
                        daemon=True)
                    self.ack_thread.start()

                result = self.broadcast_channel.queue_declare(queue='', exclusive=True)
                self.broadcast_channel.queue_bind(
                    exchange='digiturno_broadcast',
                    queue=result.method.queue)
                
                self.broadcast_channel.basic_consume(
                    queue=result.method.queue,
                    on_message_callback=self.handle_broadcast)
                
                self.broadcast_thread = threading.Thread(
                    target=self.start_broadcast_consumer,
                    daemon=True)
                self.broadcast_thread.start()
                
            except Exception as e:
                traceback.print_exc()
                print("^Error with RabbitMQ setup. Read traceback above^")
                self.unsafe_cleanup_connections()
                QTimer.singleShot(5000, self.setup_rabbitmq)
            finally:
                self.connectionLock.release()
        except:
            traceback.print_exc()
            print("^Lock aquisition failed. Read traceback above^")

    def start_consumer(self,consumer):
        while not self.shutdownFlag:
            try:
                if not hasattr(self, f'{consumer}_channel') or \
                not getattr(self, f'{consumer}_channel').is_open:
                    if self.shutdownFlag: break
                    time.sleep(0.5)
                    continue
                getattr(self, f'{consumer}_channel').start_consuming()
            except pika.exceptions.StreamLostError:
                if not self.shutdownFlag:
                    self.updateUIsignal.emit("RECONNECT_RABBITMQ")
                continue
            except Exception as e:
                if not self.shutdownFlag:
                    time.sleep(0.5)
                continue

    def start_broadcast_consumer(self):
        self.start_consumer('broadcast')

    def start_ack_consumer(self):
        self.start_consumer('ack')

    def cleanup_connections(self):
        """Thread-safe connection cleanup"""
        if self.connectionLock.locked():
            self.unsafe_cleanup_connections()
        else:
            with self.connectionLock:
                self.unsafe_cleanup_connections()

    def unsafe_cleanup_connections(self):
        """Actual cleanup logic without locking"""
        def safe_close(conn):
            try:
                if conn and conn.is_open:
                    conn.close()
            except: pass
        def safe_stop_consuming(chan):
            try:
                if chan and chan.is_open:
                    chan.stop_consuming()
            except: pass

        # Clean up connections
        for connType in ['broadcast', 'command', 'ack']:
            channel = getattr(self, f'{connType}_channel', None)
            connection = getattr(self, f'{connType}_connection', None)
            if channel:
                safe_stop_consuming(channel)
                delattr(self, f'{connType}_channel')
            if connection:
                safe_close(connection)
                delattr(self, f'{connType}_connection')

    def closeEvent(self, event):
        self.shutdownFlag = True
        self.unsafe_cleanup_connections()
        super().closeEvent(event)

    def handle_broadcast(self, ch, method, properties, body):
        try:
            message = body.decode('utf-8')
            self.updateUIsignal.emit(message)
            print(f"Broadcast handled: {message}")
        except Exception as e:
            print(f"Error processing broadcast: {e}")

    def handle_ack(self, ch, method, properties, body):
        message = body.decode('utf-8')
        if message.startswith('ACK_NEXT_TURN:'):
            _, turnInfo, nombre = message.split(':')
            servicio, numero = turnInfo.split('-')
            self.update_called_turn(servicio, numero, nombre)
            print(f"ack handled: {message}")

    def call_next_turn(self, servicio, numero):
        """Send message to call next turn. Parameters:
        
        servicio (Str): Turn's service type
        
        numero (int): Turn number"""
        try:
            self.command_channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=f'NEXT_TURN:{self.userID}:{servicio}-{numero}')
        except:
            traceback.print_exc()
            print("^Error calling next turn. Read traceback above^")
            self.setup_rabbitmq()

    def complete_current_turn(self):
        if self.labelTurno.text() != "-":
            try:
                self.command_channel.basic_publish(
                    exchange='digiturno_direct',
                    routing_key='server_command',
                    body=f'COMPLETE_TURN:{self.userID}')
                self.labelTurno.setText("-")
            except:
                traceback.print_exc()
                print(f"^Error completing turn. Read traceback above^")
                self.setup_rabbitmq()

    def cancel_current_turn(self):
        if self.labelTurno.text() != "-":
            try:
                self.command_channel.basic_publish(
                    exchange='digiturno_direct',
                    routing_key='server_command',
                    body=f'CANCEL_TURN:{self.userID}')
                self.labelTurno.setText("-")
            except Exception as e:
                print(f"Error canceling turn: {e}")
                self.setup_rabbitmq()

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
        
        self.loginButton = QPushButton("Iniciar sesión")
        self.loginButton.clicked.connect(self.verify_credentials)
        
        self.layout.addWidget(self.username)
        self.layout.addWidget(self.password)
        self.layout.addWidget(self.loginButton)
        self.setLayout(self.layout)

    def verify_credentials(self):
        conn = sqlite3.connect('digiturno.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id FROM funcionarios
            WHERE usuario = ? AND contrasena = ?
        ''', (self.username.text(), self.password.text()))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            self.userID = result[0]
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Credenciales inválidas.")

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        client = MainWindow()
        client.show_login()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Fatal error: {e}")