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
                         int(self.screenGeometry.height()/2 - 300), 900, 600)
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
        hBox2.setContentsMargins(10, 0, 10, 20)

        labelAtendiendo = QLabel("Atendiendo: ")
        self.style_label(labelAtendiendo, 30, "#1D3C12")

        self.labelTurno = QLabel("Sample turn text")
        self.style_label(self.labelTurno, 30, "#1D3C12")

        buttonTerminado = QPushButton("Terminado")
        self.style_button(buttonTerminado, 30)
        buttonTerminado.clicked.connect(self.complete_current_turn)

        hBox2.addWidget(labelAtendiendo)
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

        hBox3.addWidget(labelAsesoria)
        hBox3.addWidget(labelCaja)
        hBox3.addWidget(labelCobranza)
        hBox3.addWidget(labelCartera)

        # Grid for turns
        hBox4 = QHBoxLayout()
        hBox3Widget = QWidget()
        self.gridTurns = QGridLayout(hBox3Widget)
        self.gridTurns.setContentsMargins(10, 0, 10, 0)

        # Spacers
        for i in range(4):
            expanding_spacer = QSpacerItem(500, 20, QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.gridTurns.addItem(expanding_spacer, 0, i)
        
        # Load pending turns from DB
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
        if row < 5:
            gridWidget = QWidget()
            gridHbox = QHBoxLayout(gridWidget)
            gridHbox.setSpacing(0)
            gridWidget.setLayout(gridHbox)

            turno = QWidget()
            turno.setMinimumWidth(int(QApplication.primaryScreen().geometry().width()/20))
            turno.setMaximumWidth(int(QApplication.primaryScreen().geometry().width()/6))
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

    def update_grid(self, servicio, numero):
        removed_row = -1
        removed_col = -1
        
        for row in range(self.gridTurns.rowCount()):
            for col in range(self.gridTurns.columnCount()):
                item = self.gridTurns.itemAtPosition(row, col)
                if item and item.widget():
                    turn_label = item.widget().findChild(QLabel)
                    if turn_label and f"{servicio}-{numero}" in turn_label.text():
                        self.gridTurns.removeWidget(item.widget())
                        item.widget().deleteLater()
                        if numero in self.queue[servicio]:
                            self.queue[servicio].remove(numero)
                        removed_row, removed_col = row, col
                        break
        
        if removed_row != -1:
            for r in range(removed_row + 1, self.gridTurns.rowCount()):
                item = self.gridTurns.itemAtPosition(r, removed_col)
                if item and item.widget():
                    widget = item.widget()
                    self.gridTurns.removeWidget(widget)
                    self.gridTurns.addWidget(widget, r-1, removed_col)

    def update_called_turn(self, servicio, numero, nombre):
        self.labelTurno.setText(f"{servicio}-{numero} . {nombre}")

    def handle_server_update(self, message):
        try:
            if message.startswith("NEW_TURN:"):
                _, turnInfo, nombre = message.split(':')
                servicio, numero = turnInfo.split('-')
                self.queue[servicio].append(numero)
                self.add_pending_turn(servicio, numero, nombre)

            elif message.startswith("CALLED:"):
                _, turnInfo, station = message.split(':')
                servicio, numero = turnInfo.split('-')
                self.update_grid(servicio, numero)

            elif message.startswith("COMPLETED:"):
                _, turnInfo = message.split(':')
                servicio, numero = turnInfo.split('-')
                self.update_grid(servicio, numero)
        except:
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

    def show_login(self):
        dialog = LoginDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.userID = dialog.userID
            self.labelTitle.setText(f"Funcionario {self.userID}")
            self.show()
        else:
            self.close()

    def log_out(self):
        self.shutdownFlag = True
        
        time.sleep(0.1)
        self.cleanup_connections()
        
        self.shutdownFlag = False
        self.userID = None
        self.close()
        self.show_login()

    def set_background_color(self, widget, color):
        palette = widget.palette()
        palette.setColor(QPalette.Background, QColor(color))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)
        
    def setup_rabbitmq(self):
        with self.connectionLock:
            try:
                parameters = pika.ConnectionParameters(
                    host='localhost',
                    heartbeat=600,
                    blocked_connection_timeout=300,
                    connection_attempts=5,
                    retry_delay=5
                )
                
                self.cleanup_connections()
                
                self.command_connection = pika.BlockingConnection(parameters)
                self.command_channel = self.command_connection.channel()
                
                self.broadcast_connection = pika.BlockingConnection(parameters)
                self.broadcast_channel = self.broadcast_connection.channel()
                
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
                print(f"RabbitMQ setup failed: {e}")
                QTimer.singleShot(5000, self.setup_rabbitmq)

    def start_broadcast_consumer(self):
        while not self.shutdownFlag:
            try:
                if not hasattr(self, 'broadcast_channel') or not self.broadcast_channel.is_open:
                    if self.shutdownFlag:
                        break
                    time.sleep(1)
                    continue
                
                self.broadcast_channel.start_consuming()
                
            except pika.exceptions.StreamLostError:
                if not self.shutdownFlag:
                    QMetaObject.invokeMethod(self, "setup_rabbitmq", Qt.QueuedConnection)
                continue
                
            except Exception as e:
                if not self.shutdownFlag:
                    time.sleep(5)
                continue

    def cleanup_connections(self):
        try:
            if hasattr(self, 'broadcast_channel') and self.broadcast_channel.is_open:
                try:
                    self.broadcast_channel.stop_consuming()
                except:
                    pass
                self.broadcast_channel.close()
        except:
            pass
        
        try:
            if hasattr(self, 'broadcast_connection') and self.broadcast_connection.is_open:
                self.broadcast_connection.close()
        except:
            pass
        
        try:
            if hasattr(self, 'command_channel') and self.command_channel.is_open:
                self.command_channel.close()
        except:
            pass
        
        try:
            if hasattr(self, 'command_connection') and self.command_connection.is_open:
                self.command_connection.close()
        except:
            pass

    def closeEvent(self, event):
        self.shutdownFlag = True
        self.cleanup_connections()
        super().closeEvent(event)

    def handle_broadcast(self, ch, method, properties, body):
        try:
            message = body.decode('utf-8')
            self.updateUIsignal.emit(message)
        except Exception as e:
            print(f"Error processing broadcast: {e}")

    def call_next_turn(self, servicio, numero):
        """Send message to call next turn. Parameters:
        
        servicio (Str): Turn's service type
        
        numero (int): Turn number"""
        try:
            self.command_channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=f'NEXT_TURN:{self.userID}:{servicio}-{numero}')
            self.update_grid(servicio, numero)
        except Exception as e:
            print(f"Error calling next turn: {e}")
            self.setup_rabbitmq()

    def complete_current_turn(self):
        if self.labelTurno.text() != "Sample turn text":
            turn_info = self.labelTurno.text().split(' . ')[0]
            servicio, numero = turn_info.split('-')
            try:
                self.command_channel.basic_publish(
                    exchange='digiturno_direct',
                    routing_key='server_command',
                    body=f'COMPLETE_TURN:{self.userID}')
                self.labelTurno.setText("Sample turn text")
            except Exception as e:
                print(f"Error completing turn: {e}")
                self.setup_rabbitmq()

    def cancel_current_turn(self):
        if self.labelTurno.text() != "Sample turn text":
            turn_info = self.labelTurno.text().split(' . ')[0]
            servicio, numero = turn_info.split('-')
            try:
                self.command_channel.basic_publish(
                    exchange='digiturno_direct',
                    routing_key='server_command',
                    body=f'CANCEL_TURN:{self.userID}')
                self.labelTurno.setText("Sample turn text")
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
    app = QApplication(sys.argv)
    client = MainWindow()
    client.show_login()
    sys.exit(app.exec_())