import sys, traceback, sqlite3, socket, threading
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
        self.queue = {'A': [], 'B': [], 'C': [], 'D': [], 'E': [], 'F': [], 'G': [], 'H': [], 'I': []}
        self.attending = {'A': [], 'B': [], 'C': [], 'D': [], 'E': [], 'F': [], 'G': [], 'H': [], 'I': []}

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
        # Placeholder button for simulating new turns
        self.buttonNew = QPushButton("Nuevo turno", self)
        self.waitHeader.addWidget(self.buttonNew)
        self.buttonNew.clicked.connect(lambda: self.handle_new_turn("ID111", True, "C"))
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
                            #print(f"Received command: {data}")  # Debug
                            self.command_received.emit(data)
        except Exception as e:
            print(f"Server error: {e}")

    def handle_command(self, command):
        #print(f"Handling command: {command}")  # Debug
        # Handle command for next turn
        if command.startswith('NEXT_'):
            service = command.split('_')[1]
            #print(f"Calling next turn for {service}")  # Debug
            self.next_turn(service)
        # Handle command for cancel turn
        elif command.startswith('CANCEL_'):
            service = command.split('_')[1]
            #print(f"Canceling current turn in {service}") # Debug
            self.cancel_turn(service)
        # Handle command for new ticket
        elif command.startswith('NEWTICKET_'):
            _, cliente_id, afiliado, servicio = command.split('_')
            self.handle_new_turn(cliente_id, afiliado == '1', servicio)

    def handle_new_turn(self, cliente_id, afiliado, servicio):
        fechaHoy = datetime.now().strftime("%Y-%m-%d")
        try:
            # Registrar/verificar usuario
            self.cursor.execute('''
                INSERT OR IGNORE INTO clientes (identificacion, afiliado)
                VALUES (?, ?)
            ''', (cliente_id, afiliado))
            # Obtener número del siguiente turno
            self.cursor.execute('''
                SELECT MAX(numero) FROM turnos
                WHERE servicio = ? AND DATE(creado) = ?
                                ''', (servicio, fechaHoy))
            result = self.cursor.fetchone()[0]
            ultNum = int(result) if result is not None else 0
            nuevoNum = ultNum + 1
            # Insert turn to DB
            self.cursor.execute('''
                INSERT INTO turnos (cliente_id, servicio, numero, estado, creado)
                VALUES (
                    (SELECT id FROM clientes WHERE identificacion = ?),
                    ?, ?, 'pendiente', datetime('now'))''', (cliente_id, servicio, nuevoNum))
            self.conn.commit()
            # Add turn to queue and grid
            self.queue[servicio].append(nuevoNum)
            self.update_waiting()

        except Exception as e:
            print(f"Error creating ticket: {e}")
            self.conn.rollback()
    
    def next_turn(self, service):
        if self.queue[service]:
            nextTurn = self.queue[service].pop(0)
            self.attending[service] = nextTurn
            #print(f"Atendiendo el turno {service}-{nextTurn}")  # Debug
            # Updates current turn status to "atendido" in DB
            self.cursor.execute('''
                UPDATE turnos SET estado = 'atendido', llamado = datetime('now')
                WHERE servicio = ? AND numero = ? AND DATE(creado) = DATE('now')
                                ''', (service, nextTurn))
            self.conn.commit()
            self.update_attending(service)
            self.show_alert(service, nextTurn)
        else:
            self.attending[service] = None
            self.update_attending(service)
            #print(f"No hay turnos en espera para la caja {service}")  # Debug
    
    # Loads pending turn from DB if created today
    def init_display(self):
        self.update_waiting()

    # Updates displayed turns in attending
    def update_attending(self, service, init_mode=False):
        col = ord(service.upper()) - ord('A')
        # Calls in next turn to attend
        if not init_mode:
            # First 5 stations
            if col < 5:
                itemToRemove = self.gridLayout1.itemAtPosition(1, col)
                if itemToRemove:
                    #print(f"Item to remove: {itemToRemove.widget().text()}")  # Debug
                    widget = itemToRemove.widget()
                    widget.deleteLater()
                    widget.setGraphicsEffect(None) # Removes shadow effect to prevent lingering
                    #widget.graphicsEffect().setEnabled(False) Use this instead of the line above if it presents any issues
                    self.gridLayout1.removeItem(itemToRemove)
                else: # Use this block to show feedback when the station is empty
                    print("No item to remove (station free)")  # Debug
                if self.attending[service]:
                    ticket = QLabel(f"{service}-{self.attending[service]}")
                    self.style_label(ticket, True)
                    self.gridLayout1.addWidget(ticket, 1, col)
            # Last 4 stations
            elif col > 4:
                col -= 5
                itemToRemove = self.gridLayout2.itemAtPosition(1, col)
                if itemToRemove:
                    #print(f"Item to remove: {itemToRemove.widget().text()}")  # Debug
                    widget = itemToRemove.widget()
                    widget.deleteLater()
                    widget.setGraphicsEffect(None) # Removes shadow effect to prevent lingering
                    #widget.graphicsEffect().setEnabled(False) Use this instead of the line above if it presents any issues
                    self.gridLayout2.removeItem(itemToRemove)
                else: # Use this block to show feedback when the station is empty
                    print("No item to remove (station free)")  # Debug
                # Add new ticket being attended
                if self.attending[service]:
                    ticket = QLabel(f"{service}-{self.attending[service]}")
                    self.style_label(ticket, True)
                    self.gridLayout2.addWidget(ticket, 1, col)
        self.update_waiting()
    
    # Updates displayed turns in waiting
    def update_waiting(self):
        self.clear_waitLabels()
        print(f"Connection state: {self.conn}")
        # Sort turns by call order
        self.cursor.execute('''
            SELECT servicio, numero
            FROM turnos
            WHERE estado = 'pendiente'
            AND DATE(creado) = DATE('now')
            ORDER BY creado
                            ''')
        orderedTurns = self.cursor.fetchall()
        print(f"Turns fetched: {orderedTurns}")
        # Add all waiting turns to layout
        for servicio, numero in orderedTurns:
            turn = QLabel(f"{servicio}-{numero}")
            self.style_label(turn, False)
            self.waitLabels.addWidget(turn)
    
    # Removes widgets from waitLabels
    def clear_waitLabels(self):
        while self.waitLabels.count():
            child = self.waitLabels.takeAt(0)
            if child.widget():
                child.widget().setGraphicsEffect(None)
                child.widget().deleteLater()

    # Cancels attending turn
    def cancel_turn(self, service):
        col = ord(service.upper()) - ord('A') + 1
        if self.attending[service]:
            turn = self.attending[service]
            self.attending[service] = None
            self.cursor.execute('''
                UPDATE turnos SET estado = 'cancelado'
                WHERE servicio = ? AND numero = ? AND DATE(creado) = DATE('now')
                                ''', (service, turn))
            self.conn.commit()
            item = self.gridLayout1.itemAtPosition(1, col)
            item.widget().deleteLater()
            item.widget().setGraphicsEffect(None)
            #print(f"Canceled turn in {service}")
        else: print("No turns to cancel.")

    # Shows turn alert
    def show_alert(self, turnPrefix, turnNumber):
        service = ""
        match turnPrefix:
            case "A": service = "Caja 1"
            case "B": service = "Caja 2"
            case "C": service = "Asesor 1"
            case "D": service = "Asesor 2"
            case "E": service = "Asesor 3"
            case "F": service = "Asesor 4"
            case "G": service = "Asesor 5"
            case "H": service = "Cobranza"
            case "I": service = "Cartera"
        self.turnAlert.setText(f"""
            <div style='text-align: center;'>
                <span style='font-size: 250px; font-weight: bold;'>{turnPrefix}-{turnNumber}</span><br>
                <span style='font-size: 80px;'>{service}</span>
            </div>
                                 """)
        self.turnAlert.show_box()
        self.turnAlert.anim.finished.connect(self.turnAlert.hide_box)
        self.turnAlert.anim.start()

    # Sets style for turn labels
    def style_label(self, label, attending):
        label.setAutoFillBackground(True)  # Crucial for background rendering, whatever that means
        if attending:
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
        # Tabla de usuarios
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identificacion TEXT UNIQUE NOT NULL,
                nombre TEXT,
                afiliado BOOLEAN NOT NULL
            )''')
        # Tabla de turnos
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS turnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                servicio TEXT NOT NULL,
                numero INTEGER NOT NULL,
                estado TEXT NOT NULL, -- 'pendiente', 'atendido', 'cancelado'
                creado DATETIME,
                llamado DATETIME,
                FOREIGN KEY(cliente_id) REFERENCES clientes(id)
            ) ''')
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Digiturno()
    sys.exit(app.exec_())