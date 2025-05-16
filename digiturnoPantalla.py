import sys, traceback, sqlite3, threading, pika, json, os, logging, time
from dataclasses import dataclass
from dotenv import load_dotenv
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
db_path = 'digiturno.db'
load_dotenv()
logging.basicConfig(
    filename='digiturnoPantalla.log',
    level=logging.ERROR,
    format='%(asctime)s [%(levelname)s] %(message)s')

class TurnAlert(QLabel):
    def __init__(self, parent=None):
        self.screenGeometry = QApplication.primaryScreen().geometry()
        super().__init__("Turno: 0", parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            background: qlineargradient(
                x1:0.5, y1:0, x2:0.5, y2:1,
                stop:0 #85A947, stop:1 #3E7B27
            );
            font-weight: bold;
            color: white;
            border: 3px solid #3E7B27;
            border-radius: 30px;""")
        self.setFixedSize(int(self.screenGeometry.width()*0.47), int(self.screenGeometry.height()*0.5))
        # Opacity property
        self.opacityP = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacityP)
        self.opacityP.setOpacity(1.0)
        # Animation for pulsating effect
        self.anim = QPropertyAnimation(self.opacityP, b"opacity")
        self.anim.setLoopCount(5)
        self.anim.setDuration(1500)
        self.anim.setStartValue(0.0)
        self.anim.setKeyValueAt(0.15, 1.0)
        self.anim.setKeyValueAt(0.85, 1.0)
        self.anim.setEndValue(0.0)
        self.hide()

    def show_box(self):
        self.show()

    def hide_box(self):
        self.hide()
        try:
            self.anim.finished.disconnect()
        except:
            pass

class BackgroundFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
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

class Digiturno(QMainWindow):
    command_received = pyqtSignal(str)
    def __init__(self):
        self.screenGeometry = QApplication.primaryScreen().geometry()
        super().__init__()
        self.setWindowTitle("Digiturno")
        self.commandLock = threading.Lock()
        self.channelLock = threading.Lock()
        self.queues = {'AS': [], 'CA': [], 'CO': [], 'CT': []}
        """Keys (Str): Service type
        Elements (Turn class): Turns with attributes:
        id (int): Turn ID from turnos table
        service (Str): Service type
        number (int): Turn number
        customer (Str): Customer name"""
        self.stations = {}
        """Keys (Str): Station name (Caja 1...)
        Elements: funcionarioID (int): Staff member ID"""
        self.servingStations = {}
        """Keys (Str): nombre from estaciones table
        Elements (tuple (int, Str, int)): Turn information: id, service type and number"""
        self.orderedServing = []
        """Tuples (turnID, estacion, turno, nombre)
        turnID (int): id from turnos table
        estacion (Str): Station passed by funcionario
        turno (Str): Turn information: service type and number
        nombre (Str): Customer's name"""
        self.init_ui()
        self.init_db()
        self.setup_rabbitmq()
        self.command_received.connect(self.handle_command)
        self.load_pending()
        self.load_stations()
        
        self.showFullScreen()

    def init_ui(self):
        # Central widget setup
        self.cWidget = QWidget()
        self.setCentralWidget(self.cWidget)
        self.cWidget.setObjectName("MainBackground")
        self.cWidget.setStyleSheet("QWidget#MainBackground {background-color: #EFE3C2;}")
        # Main layout
        mainLayout = QVBoxLayout(self.cWidget)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        # Header layout
        headerLayout = QHBoxLayout()
        headerLayout.setContentsMargins(
            self.screen_width(2), self.screen_height(3),
            self.screen_width(2), self.screen_height(2))
        # Logo
        labelLogo = QLabel()
        pixmapLogo = QPixmap("logoCoohem.png")
        labelLogo.setPixmap(pixmapLogo)
        logoShadow = QGraphicsDropShadowEffect(labelLogo, blurRadius=15)
        logoShadow.setOffset(5, 5)
        labelLogo.setGraphicsEffect(logoShadow)
        headerLayout.addWidget(labelLogo)
        headerLayout.addStretch()
        # Clock
        self.clockLabel = QLabel()
        self.clockLabel.setAlignment(Qt.AlignTop)
        self.clockLabel.setStyleSheet(f"""
            font-size: {self.screen_width(3)}px;
            color: #002E08;
        """)
        clockShadow = QGraphicsDropShadowEffect(self.clockLabel, blurRadius=15)
        clockShadow.setOffset(5, 5)
        self.clockLabel.setGraphicsEffect(clockShadow)
        headerLayout.addWidget(self.clockLabel)
        mainLayout.addLayout(headerLayout)
        # Content frame and vertical layout
        content_frame = BackgroundFrame()
        mainLayout.addWidget(content_frame, stretch=1)
        verticalLayout = QVBoxLayout()
        #verticalLayout.setAlignment(Qt.AlignTop)
        content_frame.setLayout(verticalLayout)
        # Grid layout for serving turns
        self.gridLayout = QGridLayout()
        self.gridLayout.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        self.gridLayout.setHorizontalSpacing(self.screen_width(4))
        self.gridLayout.setVerticalSpacing(self.screen_height(15))
        self.gridLayout.setContentsMargins(
            self.screen_width(3), self.screen_height(5),
            self.screen_width(3), 0)
        # Turn display box
        self.turnAlert = TurnAlert(self)
        self.position_turn_alert()
        # Clock timer
        self.timeUpdateTimer = QTimer(self)
        self.timeUpdateTimer.timeout.connect(self.update_clock)
        self.timeUpdateTimer.start(1000)
        self.update_clock()
        # Add grids to vertical layout
        verticalLayout.addLayout(self.gridLayout)
        #verticalLayout.addLayout(self.waitLayout)

    def handle_command(self, command):
        """Process incoming commands recieved via signal"""
        with self.commandLock:
            print(f"Command received: {command}") # Debug
            
            if command.startswith('NEW_TURN:'): # Producer: digiturno.py
                _, cliente_id, servicio = command.split(':')
                self.new_turn(cliente_id, servicio)
                
            elif command.startswith('NEXT_TURN:'): # Producer: funcionario.py
                _, funID, turnID, queue, stat, rk = command.split(':')
                self.next_turn(int(funID), int(turnID), queue, stat, rk)
            
            elif command.startswith('CANCEL_TURN:'): # Producer: funcionario.py
                _, turnID, station, funcionario, rk = command.split(':')
                self.cancel_turn(int(turnID), station, int(funcionario), rk)
                
            elif command.startswith('REASSIGN_TURN:'):
                _, turnID, queue, station, funcionario, rk = command.split(':')
                self.reassign_turn(turnID, queue, station, funcionario, rk)
            
            elif command.startswith('COMPLETE_TURN:'): # Producer: funcionario.py
                _, station, rk = command.split(':')
                self.complete_turn(station, rk)
            
            elif command.startswith('QUEUE_REQUEST:'): # Producer: funcionario.py
                _, funcionario = command.split(':')
                self.ack_queue_request(funcionario)
            
            elif command.startswith('STATIONS_REQUEST:'):
                _, rk = command.split(':')
                self.ack_stations_request(rk)
            
            elif command.startswith('RELEASE_STATION:'):
                _, station = command.split(':')
                self.release_station(station)
            
            elif command.startswith('LOGIN_REQUEST:'): # Producer: funcionario.py
                _, username, password, station, rk = command.split(':')
                self.ack_login_request(username, password, station, rk)
            
            elif command.startswith('ADMIN_LOGIN_REQUEST:'): # Producer: admin.py
                _, username, password = command.split(':')
                self.ack_admin_login_request(username, password)
            
            elif command.startswith('CUSTOMER_ID_CHECK:'): # Producer: digiturno.py
                _, cedula = command.split(':')
                self.ack_customer_ID_check(cedula)
            
            elif command.startswith('NEW_CUSTOMER:'): # Producer: digiturno.py
                _, cedula, nombre = command.split(':')
                self.ack_new_customer(cedula, nombre)
            
            elif command.startswith('LAST_TURN_PER_SERVICE'): # Producer: digiturno.py
                self.ack_last_turn_request()
            
            elif command.startswith('FUNCIONARIOS_LIST_REQUEST'): # Producer: admin.py
                self.ack_funcionarios_list_request()
            
            elif command.startswith('FUNCIONARIOS_LIST_UPDATE:'): # Producer: admin.py
                self.funChanged = json.loads(command[len('FUNCIONARIOS_LIST_UPDATE:'):])
                self.ack_funcionarios_list_update()
            
            elif command.startswith('NEW_FUNCIONARIO:'): # Producer: admin.py
                self.newFun = json.loads(command[len('NEW_FUNCIONARIO:'):])
                self.ack_new_funcionario()
            
            elif command.startswith('DELETE_FUNCIONARIOS:'):
                ids = json.loads(command[len('DELETE_FUNCIONARIOS:'):])
                self.ack_delete_funcionarios(ids)

    def new_turn(self, cedula, servicio):
        """Handle new turns. Updates DB and queue, and calls broadcast. Parameters:
        cedula (Str): Customer's identification (not id from table)
        servicio (Str): Service type"""
        fechaHoy = datetime.now().strftime("%Y-%m-%d")
        with sqlite3.connect(db_path) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT MAX(numero) FROM turnos
                    WHERE servicio = ? AND DATE(creado) = ?
                ''', (servicio, fechaHoy))
                result = cursor.fetchone()[0] # Fetch last turn number
                number = int(result)+1 if result is not None else 1 # New turn number
                cursor.execute('''
                    SELECT nombre FROM clientes
                    WHERE identificacion = ?
                ''', (cedula,))
                customer = cursor.fetchone()[0]
                cursor.execute('''
                    INSERT INTO turnos (cliente_id, servicio, numero, cola, estado, creado)
                    VALUES ((SELECT id FROM clientes WHERE identificacion = ?),
                        ?, ?, ?, 'pendiente', datetime('now', 'localtime'))''', (cedula, servicio, number, servicio))
                turnID = cursor.lastrowid
                conn.commit()
                self.queues[servicio].append(Turn(
                    id=int(turnID),
                    service=servicio,
                    number=int(number),
                    customer=customer))
                self.broadcast_update(f"NEW_TURN:{turnID}:{servicio}-{number}:{servicio}:{customer}")
            except:
                logging.exception('Exception when trying to create new turn')
                traceback.print_exc()
                conn.rollback()
    
    def next_turn(self, funcionario, turnID, queue, station, rk):
        """Update queue, serving and DB when a turn is called. Parameters:
        funcionario (int): id from funcionarios DB
        servicio (Str): Turn's service type
        numero (int): Turn number
        estacion (Str): Station from where funcionario calls
        rk (Str): Routing key to send ack"""
        for turnInstance in self.queues[queue]:
            if turnInstance.id == int(turnID):
                service = turnInstance.service
                number = turnInstance.number
                turn = f'{service}-{number}'
                customer = turnInstance.customer
                break
        with sqlite3.connect(db_path) as conn:
            try:
                conn.cursor().execute('''
                    UPDATE turnos
                    SET estado = 'atendido', llamado = datetime('now', 'localtime'), cola = NULL, funcionario_id = ?
                    WHERE id = ?
                ''', (funcionario, turnID))
                conn.cursor().execute('''
                    UPDATE funcionarios
                    SET atendidos_hoy = atendidos_hoy + 1,
                        atendidos = atendidos + 1
                    WHERE id = ?
                ''', (funcionario,))
                conn.commit()
                self.orderedServing = [entry for entry in self.orderedServing if entry[1] != station]
                self.orderedServing.append((int(turnID), station, turn, customer))
                self.servingStations[station] = (turnID, service, number)
                
                self.queues[queue].remove(Turn(
                    id=int(turnID),
                    service=service,
                    number=int(number),
                    customer=customer))
                
                self.update_serving()
                self.show_alert(service, number, station, customer)
                self.broadcast_update(f"CALLED:{turnID}:{queue}:{funcionario}")
            except:
                logging.exception('Exception when trying to call next turn')
                traceback.print_exc()
                conn.rollback()

    def cancel_turn(self, turnID, station, funcionario, rk):
        """Cancel serving turn for funcionario. Updates DB and serving. Parameters:
        funcionario (int): id from funcionarios table
        rk (Str): Routing key from producer to send ack"""
        if station in self.servingStations and self.servingStations[station]:
            with sqlite3.connect(db_path) as conn:
                try:
                    conn.cursor().execute('''
                        UPDATE turnos
                        SET estado = 'cancelado'
                        WHERE id = ?
                    ''', (turnID,))
                    conn.cursor().execute('''
                        UPDATE funcionarios
                        SET atendidos_hoy = atendidos_hoy - 1,
                            atendidos = atendidos - 1,
                            cancelados_hoy = cancelados_hoy + 1,
                            cancelados = cancelados + 1
                        WHERE id = ?
                    ''', (funcionario,))
                    conn.commit()
                    for tuple in self.orderedServing:
                        if tuple[0] == turnID:
                            self.orderedServing.remove(tuple)
                    self.servingStations[station] = None
                    self.update_serving()
                    self.ack_cancel_turn(rk)
                except:
                    logging.exception('Exception when trying to cancel turn')
                    traceback.print_exc()
                    conn.rollback()
                    
    def reassign_turn(self, turnID, queue, station, funcionario, rk):
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE funcionarios
                    SET atendidos_hoy = atendidos_hoy - 1,
                        atendidos = atendidos - 1
                    WHERE id = ?''', (funcionario,))
                cursor.execute('''
                    UPDATE turnos
                    SET funcionario_id = NULL,
                        cola = ?,
                        estado = 'pendiente',
                        llamado = NULL
                    WHERE id = ?
                    ''', (queue, turnID))
                self.servingStations[station] = None
                for tuple in self.orderedServing:
                    if tuple[0] == int(turnID):
                        s, n = tuple[2].split('-')
                        customer = tuple[3]
                        self.queues[queue].append(Turn(
                            id=int(turnID),
                            service=s,
                            number=int(n),
                            customer=customer))
                        self.orderedServing.remove(tuple)
                        break
                    print(f'New queue:\n{self.queues}')
                self.update_serving()
                self.broadcast_update(f'ACK_REASSIGN_TURN:{turnID}:{s}-{n}:{queue}:{customer}:{rk}')
        except:
            logging.exception('Exception reassigning turn')
            traceback.print_exc()
    
    def complete_turn(self, station, rk):
        """Remove current serving turn from display. Parameters:
        station (str): Station nombre from estaciones table
        rk (str): Routing key to trace back sender"""
        if station in self.servingStations and self.servingStations[station]:
            try:
                for tuple in self.orderedServing:
                    if self.servingStations[station][0] == tuple[0]:
                        self.orderedServing.remove(tuple)
                self.servingStations[station] = None
                self.update_serving()
                self.ack_complete_turn(rk)
            except:
                logging.exception('Exception when trying to complete turn')
                traceback.print_exc()
        
    def update_serving(self):
        """Update UI with turns that are currently being served"""
        self.clear_grid(self.gridLayout)
        for i in range(5):
            spacer = QLabel()
            spacer.setFixedWidth(self.screen_width(13))
            self.gridLayout.addWidget(spacer, 0, i)
        col = 0
        for _, station, turn, customer in self.orderedServing[::-1]: # Iterate over the inverted list to display last turn first
            if col > 10: break
            labelTurn = QLabel()
            self.style_label(labelTurn, True)
            labelTurn.setText(f"""
                <div style='text-align: center; line-height: 0.7;'>
                    <div style='font-size: {self.screen_width(1.6)}px;'>{station}</div>
                    <div style='font-size: {self.screen_width(3.6)}px;'>{turn}</div>
                    <div style='font-size: {self.screen_width(1.6)}px; font-weight: normal;'>{customer}</div>
                </div>""")
            labelTurn.setFixedWidth(self.screen_width(15))
            if col < 5:
                self.gridLayout.addWidget(labelTurn, 0, col)
            elif col < 10:
                self.gridLayout.addWidget(labelTurn, 1, col-5)
            col += 1

    def clear_grid(self, layout):
        """Remove all widgets from a grid layout"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                item.widget().setGraphicsEffect(None)
                layout.removeItem(item)

    def load_pending(self):
        """Load pending turns created today from DB"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.id, t.servicio, t.numero, t.cola, c.nombre
                FROM turnos t
                JOIN clientes c ON t.cliente_id = c.id
                WHERE t.estado = 'pendiente'
                AND DATE(t.creado) = DATE('now')
                ORDER BY t.creado
            ''')
            for turnID, service, number, queue, customer in cursor.fetchall():
                self.queues[queue].append(Turn(
                    id = int(turnID),
                    service = service,
                    number = int(number),
                    customer = customer))
        
    def load_stations(self):
        """Load station names from DB"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nombre FROM estaciones')
            result = cursor.fetchall()
            self.stations = {nom[0]: None for nom in result}
    
    def serialize_queues(self) -> dict:
        "Return dict of queues converted from Turn instances to dicts"
        queues = {queue:[turn.to_dict() for turn in turns]
                  for queue, turns in self.queues.items()}
        return queues

    def show_alert(self, servicio, numero, funcionario, nombre):
        """Show turn alert. Parameters:
        servicio (Str): Service type
        numero (int): Turn number
        funcionario (Str): Station name
        nombre (Str): Customer name"""
        self.turnAlert.setText(f"""
            <div style='text-align: center; line-height: 0.8;'>
                <div style='font-size: {self.screen_width(5)}px;'>{funcionario}</div>
                <div style='font-size: {self.screen_width(14)}px;'>{servicio}-{numero}</div>
                <div style='font-size: {self.screen_width(4)}px;'>{nombre}</div>
            </div>""")
        self.turnAlert.show_box()
        self.turnAlert.anim.finished.connect(self.turnAlert.hide_box)
        self.turnAlert.anim.start()

    def style_label(self, label, serving=False):
        """Set stylesheet, alignment and shadow effect for a label. Parameters:
        label (QLabel): Label to format
        serving (bool, optional): True for 'serving', False for 'waiting'. Defaults to False"""
        label.setAutoFillBackground(True)  # Crucial for background rendering, whatever that means
        styleSheet = f"""
            QLabel {{
                background: qlineargradient(
                    x1:0.5, y1:0, x2:0.5, y2:1,
                    stop:0 #B8CAA8, stop:1 #68735F
                );
                background-image: none;
                border-radius: 5px;
                color: white;
                font-size: {self.screen_width(2)}px;
                font-weight: bold;
                padding: 10px;
            }}"""
        if serving:
            styleSheet += f"""
                QLabel {{
                    background: qlineargradient(
                        x1:0.5, y1:0, x2:0.5, y2:1,
                        stop:0 #85A947, stop:1 #3E7B27
                    );
                    font-size: {self.screen_width(1.8)}px;}}"""
        label.setStyleSheet(styleSheet)
        label.setAlignment(Qt.AlignCenter)
        labelShadow = QGraphicsDropShadowEffect(label, blurRadius=5)
        labelShadow.setOffset(3,3)
        label.setGraphicsEffect(labelShadow)
    
    def style_header(self, label):
        """Set stylesheet and alignment for label"""
        label.setStyleSheet(f"""
            QLabel {{
                background-color: #123524;
                background-image: none;
                border-radius: 5px;
                color: white;
                font-size: {self.screen_width(2)}px;
                padding: 10px;
                min-width: 165px;
                min-height: 110px;
            }}
            """)
        label.setAlignment(Qt.AlignCenter)

    def resizeEvent(self, event):
        """Reposition turn alert when resizing window"""
        super().resizeEvent(event)
        self.position_turn_alert()

    def position_turn_alert(self):
        """"Position turn alert on the middle of the window"""
        self.turnAlert.move(
            (self.width() - self.turnAlert.width()) // 2,
            (self.height() - self.turnAlert.height()) // 2
        )
    
    def update_clock(self):
        """Format clock and keep it on time"""
        currentTime = datetime.now().strftime("%I:%M")
        if int(datetime.now().strftime("%H")) >= 12:
            currentTime += " p.m."
        else:
            currentTime += " a.m."
        self.clockLabel.setText(currentTime)

    def screen_width(self, num):
        """Return pixel value of screen width % based on parameter"""
        return int(self.screenGeometry.width()*num/100)
    def screen_height(self, num):
        """Returns pixel value of screen height % based on parameter"""
        return int(self.screenGeometry.height()*num/100)
    
    def init_db(self):
        """Create DB tables and placeholder values. Checks for daily reset"""
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")
        try:
            # Tabla de usuarios
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identificacion TEXT UNIQUE NOT NULL,
                    nombre TEXT,
                    asociado BOOLEAN NOT NULL
                )''')
            # Tabla de turnos
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS turnos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    funcionario_id INTEGER,
                    servicio TEXT NOT NULL,
                    numero INTEGER NOT NULL,
                    cola TEXT,
                    estado TEXT NOT NULL, -- 'pendiente', 'atendido', 'cancelado'
                    creado DATETIME,
                    llamado DATETIME,
                    FOREIGN KEY(cliente_id) REFERENCES clientes(id),
                    FOREIGN KEY(funcionario_id) REFERENCES funcionarios(id)
                )''')
            # Tabla de funcionarios
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS funcionarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    identificacion TEXT UNIQUE NOT NULL,
                    usuario TEXT UNIQUE NOT NULL,
                    contrasena TEXT NOT NULL,
                    rol INTEGER DEFAULT 0,
                    estado INTEGER DEFAULT 1,
                    atendidos_hoy INTEGER DEFAULT 0,
                    cancelados_hoy INTEGER DEFAULT 0,
                    atendidos INTEGER DEFAULT 0,
                    cancelados INTEGER DEFAULT 0
                )''')
            # Tabla de estaciones
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS estaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL
                )''')
            # Tabla de control de fecha
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS control_fecha (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    last_reset DATE NOT NULL)''')
            self.conn.commit()
        except Exception as e:
            self.logging.exception('Exception creating DB')
            print(f"Error creating DB: {e}")
            self.conn.rollback()
        try:
            # Check for daily reset
            today = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute('''
                SELECT last_reset FROM control_fecha WHERE id = 1''')
            last_reset = self.cursor.fetchone()[0]
            if last_reset != today:
                self.cursor.execute('''
                    UPDATE funcionarios
                    SET atendidos_hoy = 0, cancelados_hoy = 0''')
                self.cursor.execute('''
                    UPDATE control_fecha
                    SET last_reset = ?
                    WHERE id = 1
                ''', (today,))
            self.conn.commit()
        except Exception as e:
            print(f"Error with init_db: {e}")
            self.conn.rollback()
        
    def setup_rabbitmq(self):
        """Setup connection to RabbitMQ server"""
        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER"),
            os.getenv("RABBITMQ_PASS"))
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='localhost',
                credentials=credentials))
        self.channel = self.connection.channel()
        
        # Direct exchange
        self.channel.exchange_declare(
            exchange='digiturno_direct',
            exchange_type='direct',
            durable=True)
        
        # Direct exchange for acknowledge msg
        self.channel.exchange_declare(
            exchange='ack_exchange',
            exchange_type='direct',
            durable=True)
        
        # Fanout exchange for broadcasts FROM server
        self.channel.exchange_declare(
            exchange='digiturno_broadcast', 
            exchange_type='fanout',
            durable=True)
        
        # Server's command queue
        self.channel.queue_declare(queue='server_commands', durable=True)
        self.channel.queue_bind(
            exchange='digiturno_direct',
            queue='server_commands',
            routing_key='server_command')
        
        # Start consuming commands
        self.channel.basic_consume(
            queue='server_commands',
            on_message_callback=self.handle_msg)
        
        # Run in background thread
        self.rabbitmq_thread = threading.Thread(
            target=self.start_rabbitmq_consumer,
            daemon=True)
        self.rabbitmq_thread.start()
    
    def start_rabbitmq_consumer(self):
        """Consume RabbitMQ messages"""
        try:
            self.channel.start_consuming()
        except: pass
    
    def handle_msg(self, ch, method, properties, body):
        """Handle incoming messages through RabbitMQ"""
        message = body.decode('utf-8')
        self.command_received.emit(message)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    def ack_cancel_turn(self, rk):
        """Send direct acknowledgement to funcionario after canceling turn
        rk (Str): Routing key to trace back funcionario"""
        try:
            msgBody = f'ACK_CANCEL_TURN'
            with self.channelLock:
                self.channel.basic_publish(
                    exchange='ack_exchange',
                    routing_key=str(rk),
                    body=msgBody,
                    properties=pika.BasicProperties(delivery_mode=2))
                print(f'[✓] Sent msg:\n{msgBody}\n')
        except:
            logging.exception('Exception on ack_cancel_turn method')
            traceback.print_exc()
    
    def ack_complete_turn(self, rk):
        """Send direct acknowledgement to funcionario after completing current turn
        rk (Str): Routing key to trace back funcionario"""
        try:
            msgBody = f'ACK_COMPLETE_TURN'
            with self.channelLock:
                self.channel.basic_publish(
                    exchange='ack_exchange',
                    routing_key=str(rk),
                    body=msgBody,
                    properties=pika.BasicProperties(delivery_mode=2))
            print(f'[✓] Sent msg:\n{msgBody}\n')
        except:
            logging.exception('Exception on ack_complete_turn method')
            traceback.print_exc()

    def ack_queue_request(self, rk):
        """Send direct acknowledgement to funcionario with requested queue
        rk (Str): Routing key to trace back funcionario"""
        try:
            msgBody = json.dumps(self.serialize_queues()).encode('utf-8')
            with self.channelLock:
                self.channel.basic_publish(
                    exchange='ack_exchange',
                    routing_key=str(rk),
                    body=msgBody,
                    properties=pika.BasicProperties(delivery_mode=2))
                print(f'[✓] Sent msg:\n{msgBody}\n')
        except:
            logging.exception('Exception sending ack_queue_request')
            traceback.print_exc
    
    def ack_stations_request(self, rk):
        """Send direct acknowledgement to funcionario with stations available
        rk (Str): Routing key to trace back funcionario"""
        stations = [name for name, user in self.stations.items() if user is None]
        msgBody = f'ACK_STATIONS_REQUEST:{json.dumps(stations)}'.encode('utf-8')
        try:
            with self.channelLock:
                self.channel.basic_publish(
                    exchange='ack_exchange',
                    routing_key=str(rk),
                    body=msgBody,
                    properties=pika.BasicProperties(delivery_mode=2))
                print(f'[✓] Sent msg:\n{msgBody}\n')
        except:
            logging.exception('Exception on ack_stations_request method')
            traceback.print_exc()
    
    def release_station(self, station):
        """Called when a funcionario logs out or disconnects
        station (Str): Station name"""
        self.stations[station] = None

    def ack_login_request(self, username, password, station, rk):
        """Validate funcionario credentials and send acknowledgement of the result. Parameters:
        username (Str): 'usuario' column from DB table funcionarios
        password (Str): 'contrasena' column from DB table funcionarios,
        station (Str): Station name to check availability,
        rk (Str): Routing key to trace back funcionario"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, estado, nombre FROM funcionarios
                WHERE usuario = ? AND contrasena = ?
            ''', (username, password))
            result = cursor.fetchone()
            if result:
                if result[1] == 1:
                    if self.stations.get(station) is None:
                        userID = result[0]
                        nombre = result[2]
                        self.stations[station] = userID
                    else: userID = nombre = station = 'STATION_BUSY'
                else: userID = nombre = station = 'NO_ACCESS' # If credentials are valid but user is blocked
            else: userID = nombre = station = 'NOT_FOUND' # If credentials don't match any user
        with self.channelLock:
            try:
                msgBody = f'ACK_LOGIN_REQUEST:{userID}:{nombre}:{station}'
                self.channel.basic_publish(
                    exchange='ack_exchange',
                    routing_key=str(rk),
                    body=f'ACK_LOGIN_REQUEST:{userID}:{nombre}:{station}',
                    properties=pika.BasicProperties(delivery_mode=2))
                print(f'[✓] Sent msg:\n{msgBody}\n')
            except: logging.exception('Exception sending ack_login_request')
    
    def ack_admin_login_request(self, username, password):
        """Validate admin credentials and send acknowledgement with the result. Parameters:
        username (Str): 'usuario' from funcionarios table,
        password (Str): 'contrasena' from funcionarios table"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, rol, estado FROM funcionarios 
                WHERE usuario = ? AND contrasena = ?
            ''', (username, password))
            result = cursor.fetchone()
        isAdm = 0
        if result:
            if result[2] == 1:
                funID = result[0]
                if result[1] == 1:
                    isAdm = 1
            else: funID = 'NO_ACCESS'
        else: funID = 'NOT_FOUND'
        try:
            msgBody = f'ACK_LOGIN_REQUEST:{funID}:{isAdm}'
            with self.channelLock:
                self.channel.basic_publish(
                    exchange='ack_exchange',
                    routing_key='admin',
                    body=f'ACK_LOGIN_REQUEST:{funID}:{isAdm}',
                    properties=pika.BasicProperties(delivery_mode=2))
                print(f'[✓] Sent msg:\n{msgBody}\n')
        except:
            logging.exception('Exception on ack_admin_login_request method')
            traceback.print_exc()

    def ack_customer_ID_check(self, cedula):
        """Check if customer is registered in DB and send acknowledgement
        cedula (Str): 'identificacion' column from clientes table"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM clientes WHERE identificacion =  ?', (cedula,))
            customerInfo = cursor.fetchall()
            if customerInfo:
                reg = 1
                nom = customerInfo[0][2]
                asc = customerInfo[0][3]
            else:
                reg = 0
                nom = 'NULL'
                asc = 0
        try:
            msgBody = f'ACK_CUSTOMER_ID_CHECK:{reg}:{nom}:{asc}'
            with self.channelLock:
                self.channel.basic_publish(
                    exchange='ack_exchange',
                    routing_key='user',
                    body=msgBody,
                    properties=pika.BasicProperties(delivery_mode=2))
                print(f'[✓] Sent msg:\n{msgBody}\n')
        except:
            logging.exception('Exception on ack_customer_ID_check method')
            traceback.print_exc()
    
    def ack_new_customer(self, cedula, nombre):
        """Insert new customer into DB and send acknowledgement. Parameters:
        cedula (Str): 'identificacion' on clientes table
        nombre (Str): 'nombre' on clientes table"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO clientes (identificacion, nombre, asociado)
                VALUES (?, ?, False)
            ''', (cedula, nombre))
        try:
            msgBody = f'ACK_NEW_CUSTOMER:{cedula}:{nombre}'
            with self.channelLock:
                self.channel.basic_publish(
                    exchange='ack_exchange',
                    routing_key='user',
                    body=msgBody,
                    properties=pika.BasicProperties(delivery_mode=2))
                print(f'[✓] Sent msg:\n{msgBody}\n')
        except:
            logging.exception('Exception on ack_new_customer method')
            traceback.print_exc()
    
    def ack_last_turn_request(self):
        """Send acknowledgement to customer app with the last turn number of each service type"""
        fechaHoy = datetime.now().strftime("%Y-%m-%d")
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT servicio, MAX(numero) FROM turnos WHERE DATE(creado) = ? GROUP BY servicio', (fechaHoy,))
            result = cursor.fetchall()
        try:
            msgBody = json.dumps(result)
            with self.channelLock:
                self.channel.basic_publish(
                    exchange='ack_exchange',
                    routing_key='user',
                    body=msgBody,
                    properties=pika.BasicProperties(delivery_mode=2))
                print(f'[✓] Sent msg:\n{msgBody}\n')
        except:
            logging.exception('Exception on ack_last_turn_request method')
            traceback.print_exc()
    
    def ack_funcionarios_list_request(self):
        """Send acknowledgement with funcionarios list requested by admin"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, identificacion, usuario, contrasena, rol, estado FROM funcionarios")
            users = cursor.fetchall()
        try:
            msgBody = json.dumps(users)
            with self.channelLock:
                self.channel.basic_publish(
                    exchange='ack_exchange',
                    routing_key='admin',
                    body=msgBody,
                    properties=pika.BasicProperties(delivery_mode=2))
                print(f'[✓] Sent msg:\n{msgBody}\n')
        except:
            logging.exception('Exception on ack_funcionarios_list method')
            traceback.print_exc()
    
    def ack_funcionarios_list_update(self):
        """Update funcionarios table and send acknowledgement to admin"""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                for row in self.funChanged:
                    id_, nombre, identificacion, usuario, contrasena, rol, estado = row
                    cursor.execute('''
                        UPDATE funcionarios SET nombre = ?, identificacion = ?, usuario = ?, contrasena = ?, rol = ?, estado = ?
                        WHERE id = ?
                    ''', (nombre, identificacion, usuario, contrasena, rol, estado, id_))
            with self.channelLock:
                msgBody = 'ACK_FUNCIONARIOS_LIST_UPDATE:good'
                self.channel.basic_publish(
                    exchange='ack_exchange',
                    routing_key='admin',
                    body=msgBody,
                    properties=pika.BasicProperties(delivery_mode=2))
                print(f'[✓] Sent msg:\n{msgBody}\n')
        except Exception as e:
            with self.channelLock:
                msgBody = 'ACK_FUNCIONARIOS_LIST_UPDATE:error'
                self.channel.basic_publish(
                    exchange='ack_exchange',
                    routing_key='admin',
                    body=msgBody,
                    properties=pika.BasicProperties(delivery_mode=2))
                print(f'[✓] Sent msg:\n{msgBody}\n')
            print(f'Funcionarios list not updated, error: {e}')
    
    def ack_new_funcionario(self):
        """Insert new funcionario into DB and send acknowledgement to admin"""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO funcionarios (nombre, identificacion, usuario, contrasena, rol, estado)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (self.newFun[0], self.newFun[1], self.newFun[2], self.newFun[3], self.newFun[4], self.newFun[5]))
                id_ = cursor.lastrowid
            try:
                msgBody = f'ACK_NEW_FUNCIONARIO:good:{id_}:ignore'
                with self.channelLock:
                    self.channel.basic_publish(
                        exchange='ack_exchange',
                        routing_key='admin',
                        body=msgBody,
                        properties=pika.BasicProperties(delivery_mode=2))
                    print(f'[✓] Sent msg:\n{msgBody}\n')
            except:
                logging.exception('Exception on ack_new_funcionario method')
                traceback.print_exc()
        except sqlite3.IntegrityError as e:
            try:
                msgBody = f'ACK_NEW_FUNCIONARIO:error:{e}'
                with self.channelLock:
                    self.channel.basic_publish(
                        exchange='ack_exchange',
                        routing_key='admin',
                        body=msgBody,
                        properties=pika.BasicProperties(delivery_mode=2))
                    print(f'[✓] Sent msg:\n{msgBody}\n')
                print(f'Error inserting new funcionario: {e}')
            except:
                logging.exception('Exception on ack_new_funcionario method')
                traceback.print_exc()
    
    def ack_delete_funcionarios(self, ids):
        """Delete funcionarios requested by admin and send acknowledgement.
        ids (list): List of id's to remove from table"""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                for id_ in ids:
                    cursor.execute('''
                        DELETE FROM funcionarios WHERE id = ?
                    ''', (int(id_),))
            with self.channelLock:
                msgBody = f'ACK_DELETE_FUNCIONARIOS:{ids}'
                self.channel.basic_publish(
                    exchange='ack_exchange',
                    routing_key='admin',
                    body=msgBody,
                    properties=pika.BasicProperties(delivery_mode=2))
                print(f'[✓] Sent msg:\n{msgBody}\n')
        except:
            logging.exception('Exception on ack_delete_funcionario method')
            traceback.print_exc()

    def broadcast_update(self, message):
        """Send broadcast message with exchange 'digiturno_broadcast'. Sent to funcionarios"""
        try:
            with self.channelLock:
                self.channel.basic_publish(
                    exchange='digiturno_broadcast',
                    routing_key='',
                    body=message)
                print(f'[✓] Broadcast msg:\n{message}\n')
        except:
            logging.exception('Exception broadcasting msg')
            traceback.print_exc()
    
    def closeEvent(self, event):
        """Clean up on window close"""
        if hasattr(self, 'channel') and self.channel.is_open:
            try:
                self.channel.stop_consuming()
                time.sleep(0.2)
            except: pass
        if hasattr(self, 'rabbitmq_thread') and self.rabbitmq_thread.is_alive():
            try: self.rabbitmq_thread.join()
            except: pass
        if hasattr(self, 'channel') and self.channel.is_open:
            try: self.channel.close()
            except: pass
        if hasattr(self, 'connection') and self.connection.is_open:
            try: self.connection.close()
            except: pass
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Digiturno()
    sys.exit(app.exec_())