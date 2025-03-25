import sys, traceback, sqlite3, socket, threading, random
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class TurnAlert(QLabel):
    def __init__(self, parent=None):
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
            border-radius: 30px;
        """)
        self.setFixedSize(700, 500)
        # Opacity property
        self.opacityP = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacityP)
        self.opacityP.setOpacity(1.0)
        # Animation for pulsating effect
        self.anim = QPropertyAnimation(self.opacityP, b"opacity")
        self.anim.setLoopCount(5)
        self.anim.setDuration(1500)
        self.anim.setStartValue(0.0)
        self.anim.setKeyValueAt(0.2, 1.0)
        self.anim.setKeyValueAt(0.8, 1.0)
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

class Digiturno(QMainWindow):
    command_received = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digiturno")
        self.queue = {'AS': [], 'CA': [], 'CO': [], 'CT': []}
        self.serving = {'1': [], '2': [], '3': [], '4': [], '5': [], '6': [], '7': [], '8': [], '9': []}

        self.init_ui()
        self.init_db()
        self.command_received.connect(self.handle_command)
        self.init_display()
        
        self.showFullScreen()
        self.start_server()

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
        headerLayout.setContentsMargins(20, 20, 20, 20)
        # Logo
        labelLogo = QLabel()
        pixmapLogo = QPixmap("logoCoohem.png")
        labelLogo.setPixmap(pixmapLogo)
        logoShadow = QGraphicsDropShadowEffect(labelLogo, blurRadius=15)
        logoShadow.setOffset(5, 5)
        labelLogo.setGraphicsEffect(logoShadow)
        headerLayout.addSpacing(20)
        headerLayout.addWidget(labelLogo)
        headerLayout.addStretch()
        # Clock
        self.clockLabel = QLabel()
        self.clockLabel.setStyleSheet("""
            font-size: 60px;
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
        # Grid layout 1 (stations 1 - 5)
        self.gridLayout1 = QGridLayout()
        self.gridLayout1.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        self.gridLayout1.setHorizontalSpacing(170)
        self.gridLayout1.setVerticalSpacing(5)
        self.gridLayout1.setContentsMargins(5, 5, 5, 5)
        # Grid layout 2 (stations 6 - 9)
        self.gridLayout2 = QGridLayout()
        self.gridLayout2.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        self.gridLayout2.setHorizontalSpacing(170)
        self.gridLayout2.setVerticalSpacing(5)
        self.gridLayout2.setContentsMargins(5, 5, 5, 5)
        # HBox for waiting
        self.waitLayout = QHBoxLayout()
        self.waitLayout.setContentsMargins(150, 20, 20, 20)
        self.waitLayout.setSpacing(10)
        self.waitLayout.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        self.waitHeader = QHBoxLayout()
        self.waitLabels = QHBoxLayout()
        self.waitLayout.addLayout(self.waitHeader)
        self.waitLayout.addLayout(self.waitLabels)
        # Headers
        self.add_header("Caja 1", 0, 0, 1)
        self.add_header("Caja 2", 0, 1, 1)
        self.add_header("Asesor 1", 0, 2, 1)
        self.add_header("Asesor 2", 0, 3, 1)
        self.add_header("Asesor 3", 0, 4, 1)
        self.add_header("Asesor 4", 0, 0, 2)
        self.add_header("Asesor 5", 0, 1, 2)
        self.add_header("Cartera", 0, 2, 2)
        self.add_header("Cobranza", 0, 3, 2)
        self.add_header("En cola", 0, 0, 3)
        # Turn display box
        self.turnAlert = TurnAlert(self)
        self.position_turn_alert()
        # Clock timer
        self.timeUpdateTimer = QTimer(self)
        self.timeUpdateTimer.timeout.connect(self.update_clock)
        self.timeUpdateTimer.start(1000)
        self.update_clock()
        # Add grids to vertical layout
        verticalLayout.addLayout(self.gridLayout1)
        verticalLayout.addLayout(self.gridLayout2)
        verticalLayout.addLayout(self.waitLayout)

    def start_server(self):
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()
    
    def run_server(self):
        HOST = '0.0.0.0'
        PORT = 47529
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((HOST, PORT))
                s.listen()
                print(f"Server listening on {HOST}:{PORT}")  # Debug
                while True:
                    conn, addr = s.accept()
                    with conn:
                        print(f"Connected by {addr}")  # Debug
                        data = conn.recv(1024).decode('utf-8').strip()
                        if data:
                            print(f"Received command: {data}")  # Debug
                            self.command_received.emit(data)
        except Exception as e:
            print(f"Server error: {e}")

    def handle_command(self, command):
        # Handle command for next turn
        if command.startswith('NEXT_'):
            station = command.split('_')[1]
            print(f"Calling next turn for {station}")  # Debug
            self.next_turn(int(station))
        # Handle command for cancel turn
        elif command.startswith('CANCEL_'):
            station = command.split('_')[1]
            print(f"Canceling current turn in {station}") # Debug
            self.cancel_turn(int(station))
        # Handle command for new ticket
        elif command.startswith('NEWTICKET_'):
            _, cliente_id, servicio = command.split('_')
            self.new_turn(cliente_id, servicio)
            print("Command recieved")

    def new_turn(self, cedula, servicio):
        fechaHoy = datetime.now().strftime("%Y-%m-%d")
        try:
            self.cursor.execute('''
                SELECT MAX(numero) FROM turnos
                WHERE servicio = ? AND DATE(creado) = ?
                                ''', (servicio, fechaHoy))
            result = self.cursor.fetchone()[0]
            lastNum = int(result) if result is not None else 0
            newNum = lastNum + 1
            # Insert turn to DB
            self.cursor.execute('''
                INSERT INTO turnos (cliente_id, servicio, numero, estado, creado)
                VALUES (
                    (SELECT id FROM clientes WHERE identificacion = ?),
                    ?, ?, 'pendiente', datetime('now'))''', (cedula, servicio, newNum))
            self.conn.commit()
            # Add turn to queue and grid
            self.queue[servicio].append(newNum)
            self.orderedTurns.append((servicio, newNum))
            print(f"Ordered turns: {self.orderedTurns}")
            self.update_waiting()

        except Exception as e:
            print(f"Error creating ticket: {e}")
            self.conn.rollback()
    
    def next_turn(self, station):
        service = self.match_service(station)
        if self.queue[service]:
            nextTurn = self.queue[service].pop(0)
            self.serving[station] = nextTurn
            # Updates current turn status to "atendido" in DB
            self.cursor.execute('''
                UPDATE turnos SET estado = 'atendido', llamado = datetime('now')
                WHERE servicio = ? AND numero = ? AND DATE(creado) = DATE('now')
                                ''', (service, nextTurn))
            self.cursor.execute('''
                UPDATE funcionarios SET atendidos_hoy = atendidos_hoy + 1
                WHERE id = ?
                                ''', (station,))
            self.conn.commit()
            self.orderedTurns.remove((service, nextTurn))
            print(f"Ordered turns: {self.orderedTurns}")
            self.update_serving(station)
            self.update_waiting()
            self.show_alert(station, nextTurn)
        else:
            self.serving[station] = None
            self.update_serving(station)
            self.update_waiting()
            print(f"No hay turnos en espera para el servicio {service}")
    
    # Loads data from DB if created today
    def init_display(self):
        # Sort turns by creation order
        self.cursor.execute('''
            SELECT servicio, numero
            FROM turnos
            WHERE estado = 'pendiente'
            AND DATE(creado) = DATE('now')
            ORDER BY creado
                            ''')
        self.orderedTurns = self.cursor.fetchall()
        print(f"Ordered turns: {self.orderedTurns}")
        self.update_waiting()

    # Updates displayed turns in serving
    def update_serving(self, station, init_mode=False):
        col = station - 1
        # Calls in next turn to serve
        if not init_mode:
            # First 5 stations
            if col < 5:
                itemToRemove = self.gridLayout1.itemAtPosition(1, col)
                if itemToRemove:
                    widget = itemToRemove.widget()
                    widget.deleteLater()
                    widget.setGraphicsEffect(None) # Removes shadow effect to prevent lingering
                    #widget.graphicsEffect().setEnabled(False) Use this instead of the line above if it presents any issues
                    self.gridLayout1.removeItem(itemToRemove)
                else: # Use this block to show feedback when the station is empty
                    pass
                if self.serving[station]:
                    ticket = QLabel(f"{self.match_service(station)}-{self.serving[station]}")
                    self.style_label(ticket, True)
                    self.gridLayout1.addWidget(ticket, 1, col)
            # Last 4 stations
            elif col > 4:
                col -= 5
                itemToRemove = self.gridLayout2.itemAtPosition(1, col)
                if itemToRemove:
                    widget = itemToRemove.widget()
                    widget.deleteLater()
                    widget.setGraphicsEffect(None) # Removes shadow effect to prevent lingering
                    #widget.graphicsEffect().setEnabled(False) Use this instead of the line above if it presents any issues
                    self.gridLayout2.removeItem(itemToRemove)
                else: # Use this block to show feedback when the station is empty
                    pass
                # Add new ticket being served
                if self.serving[station]:
                    ticket = QLabel(f"{self.match_service(station)}-{self.serving[station]}")
                    self.style_label(ticket, True)
                    self.gridLayout2.addWidget(ticket, 1, col)
    
    # Updates displayed turns in waiting
    def update_waiting(self):
        self.clear_waitLabels()
        # Add all waiting turns to layout
        counter = 0
        for servicio, numero in self.orderedTurns:
            if counter < 7:
                turn = QLabel(f"{servicio}-{numero}")
                self.style_label(turn, False)
                self.waitLabels.addWidget(turn)
            else: print("No more space for waiting labels")
            counter += 1
    
    # Removes widgets from waitLabels
    def clear_waitLabels(self):
        while self.waitLabels.count():
            child = self.waitLabels.takeAt(0)
            if child.widget():
                child.widget().setGraphicsEffect(None)
                child.widget().deleteLater()

    # Cancels serving turn
    def cancel_turn(self, station):
        col = station - 1
        service = self.match_service(station)
        if self.serving[station]:
            turn = self.serving[station]
            self.serving[station] = None
            self.cursor.execute('''
                UPDATE turnos SET estado = 'cancelado'
                WHERE servicio = ? AND numero = ? AND DATE(creado) = DATE('now')
                                ''', (service, turn))
            self.cursor.execute('''
                UPDATE estaciones SET atendidos_hoy = atendidos_hoy - 1,
                    cancelados_hoy = cancelados_hoy + 1
                WHERE id = ?
                                ''', (station,))
            self.conn.commit()
            if col < 5:
                item = self.gridLayout1.itemAtPosition(1, col)
                item.widget().deleteLater()
                item.widget().setGraphicsEffect(None)
                print(f"Canceled turn in {station}")
            elif col > 4:
                col -= 5
                item = self.gridLayout2.itemAtPosition(1, col)
                item.widget().deleteLater()
                item.widget().setGraphicsEffect(None)
                print(f"Canceled turn in {station}")
        else: print("No turns to cancel.")

    # Takes station and returns service
    def match_service(self, station):
        match station:
            case 1 | 2: return 'P'
            case 3 | 4 | 5 | 6 | 7: return 'Q'
            case 8: return 'R'
            case 9: return 'S'

    # Shows turn alert
    def show_alert(self, station, turnNumber):
        stationText = ""
        service = self.match_service(station)
        match station:
            case 1: stationText = "Caja 1"
            case 2: stationText = "Caja 2"
            case 3: stationText = "Asesor 1"
            case 4: stationText = "Asesor 2"
            case 5: stationText = "Asesor 3"
            case 6: stationText = "Asesor 4"
            case 7: stationText = "Asesor 5"
            case 8: stationText = "Cartera"
            case 9: stationText = "Cobranza"
        self.turnAlert.setText(f"""
            <div style='text-align: center;'>
                <span style='font-size: 250px; font-weight: bold;'>{service}-{turnNumber}</span><br>
                <span style='font-size: 80px;'>{stationText}</span>
            </div>
                                 """)
        self.turnAlert.show_box()
        self.turnAlert.anim.finished.connect(self.turnAlert.hide_box)
        self.turnAlert.anim.start()

    # Sets style for turn labels
    def style_label(self, label, serving):
        label.setAutoFillBackground(True)  # Crucial for background rendering, whatever that means
        if serving:
            label.setStyleSheet(f"""
                QLabel {{
                    background: qlineargradient(
                        x1:0.5, y1:0, x2:0.5, y2:1,
                        stop:0 #85A947, stop:1 #3E7B27
                    );
                    background-image: none;
                    border-radius: 5px;
                    color: white;
                    font-size: 50px;
                    font-weight: bold;
                    padding: 10px;
                    min-width: 165px;
                    min-height: 110px;
                }}
                """)
        else:
            label.setStyleSheet(f"""
                QLabel {{
                    background: qlineargradient(
                        x1:0.5, y1:0, x2:0.5, y2:1,
                        stop:0 #B8CAA8, stop:1 #68735F
                    );
                    background-image: none;
                    border-radius: 5px;
                    color: white;
                    font-size: 50px;
                    font-weight: bold;
                    padding: 10px;
                    min-width: 165px;
                    min-height: 110px;
                }}
                """)
        label.setAlignment(Qt.AlignCenter)
        labelShadow = QGraphicsDropShadowEffect(label, blurRadius=5)
        labelShadow.setOffset(3,3)
        label.setGraphicsEffect(labelShadow)
    
    # Styles and adds header labels to the grid
    def add_header(self, text, row, col, grid):
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                background-color: #123524;
                background-image: none;
                border-radius: 5px;
                color: white;
                font-size: 30px;
                padding: 10px;
                min-width: 165px;
                min-height: 110px;
            }}
            """)
        label.setAlignment(Qt.AlignCenter)
        if grid == 1:
            self.gridLayout1.addWidget(label, row, col)
        elif grid == 2:
            self.gridLayout2.addWidget(label, row, col)
        else:
            self.waitHeader.addWidget(label)

    # Repositions turn alert when resizing
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_turn_alert()

    # Positions turn alert on the middle
    def position_turn_alert(self):
        self.turnAlert.move(
            (self.width() - self.turnAlert.width()) // 2,
            (self.height() - self.turnAlert.height()) // 2
        )
    
    # Formats clock and keeps it on time
    def update_clock(self):
        currentTime = datetime.now().strftime("%H:%M")
        if int(datetime.now().strftime("%H")) >= 12:
            currentTime += " p.m."
        else:
            currentTime += " a.m."
        self.clockLabel.setText(currentTime)
    
    # Initializes DB
    def init_db(self):
        self.conn = sqlite3.connect('digiturno.db')
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
                    is_admin INTEGER DEFAULT 0,
                    atendidos_hoy INTEGER DEFAULT 0,
                    cancelados_hoy INTEGER DEFAULT 0,
                    atendidos INTEGER,
                    cancelados INTEGER
                )''')
            # Tabla de control de fecha
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS control_fecha (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    last_reset DATE NOT NULL
                )
                                ''')
            self.conn.commit()
        except Exception as e:
            print(f"Error creating DB: {e}")
            self.conn.rollback()
        try:
            # Create funcionarios
            self.cursor.execute('''
                    INSERT OR IGNORE INTO funcionarios (identificacion, nombre, usuario, contrasena)
                    VALUES ('CC2132', 'funcionario1', 'funcionario1', 'pass'), ('CC3215', 'funcionario2', 'funcionario2', 'pass'),
                        ('CC4896', 'funcionario3', 'funcionario3', 'pass'), ('CC9525', 'funcionario4', 'funcionario4', 'pass'),
                        ('CC1962', 'funcionario5', 'funcionario5', 'pass'), ('CC1052', 'funcionario6', 'funcionario6', 'pass'),
                        ('CC1524', 'funcionario7', 'funcionario7', 'pass'), ('CC8513', 'funcionario8', 'funcionario8', 'pass'),
                        ('CC4198', 'funcionario9', 'funcionario9', 'pass')
                ''')
            # Create control de fecha
            self.cursor.execute('''
                INSERT OR IGNORE INTO control_fecha (id, last_reset)
                VALUES (1, '2000-01-01')
                                ''')
            # Check for daily reset
            today = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute('''
                SELECT last_reset FROM control_fecha WHERE id = 1
                                ''')
            last_reset = self.cursor.fetchone()[0]
            if last_reset != today:
                self.cursor.execute('''
                    UPDATE funcionarios
                    SET atendidos_hoy = 0, cancelados_hoy = 0
                                    ''')
                self.cursor.execute('''
                    UPDATE control_fecha
                    SET last_reset = ?
                    WHERE id = 1
                    ''', (today,))
            for service in self.queue:
                self.queue[service].clear()
            # Load all pending turn from DB to queue
            self.cursor.execute('''
                SELECT servicio, numero
                FROM turnos
                WHERE estado = 'pendiente'
                AND DATE(creado) = DATE('now')
                ORDER BY creado
            ''')
            for servicio, numero in self.cursor.fetchall():
                self.queue[servicio].append(numero)
            self.conn.commit()
        except Exception as e:
            print(f"Error with init_db: {e}")
            self.conn.rollback()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Digiturno()
    sys.exit(app.exec_())