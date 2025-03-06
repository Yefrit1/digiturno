import sys, traceback, sqlite3, socket, threading
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class AlertaTurno(QLabel):
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
        # Content frame
        content_frame = BackgroundFrame()
        mainLayout.addWidget(content_frame, stretch=1)
        # Ticket grid layout
        self.gridLayout = QGridLayout(content_frame)
        self.gridLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.gridLayout.setHorizontalSpacing(5)
        self.gridLayout.setVerticalSpacing(5)
        self.gridLayout.setContentsMargins(5, 5, 5, 5)
        # Headers
        self.add_header("Atendiendo", 1, 0)
        spanLabel1 = QLabel("")
        spanLabel1.setFixedSize(170, 30)
        self.gridLayout.addWidget(spanLabel1, 2, 0)
        self.add_header("En espera", 3, 0)
        self.add_header("Caja 1", 0, 1)
        self.add_header("Caja 2", 0, 2)
        self.add_header("Asesor 1", 0, 3)
        self.add_header("Asesor 2", 0, 4)
        self.add_header("Asesor 3", 0, 5)
        self.add_header("Asesor 4", 0, 6)
        self.add_header("Asesor 5", 0, 7)
        self.add_header("Cartera", 0, 8)
        self.add_header("Cobranza", 0, 9)
        # Turn display box
        self.alertaTurno = AlertaTurno(self)
        self.position_turn_alert()
        # Clock timer
        self.timeUpdateTimer = QTimer(self)
        self.timeUpdateTimer.timeout.connect(self.update_clock)
        self.timeUpdateTimer.start(1000)
        self.update_clock()

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
        print(f"Handling command: {command}")  # Debug
        # Handle command for next turn
        if command.startswith('NEXT_'):
            service = command.split('_')[1]
            print(f"Calling next turn for {service}")  # Debug
            self.next_turn(service)
        elif command.startswith('CANCEL_'):
            service = command.split('_')[1]
            self.cancel_turn(service)
            print(f"Canceling current turn in {service}") # Debug
        # Handle command for new ticket
        elif command.startswith('NEWTICKET_'):
            _, cliente_id, afiliado, servicio = command.split('_')
            self.handle_new_turn(cliente_id, afiliado == '1', servicio)
    
    def next_turn(self, service):
        if self.queue[service]:
            nextTurn = self.queue[service].pop(0)
            self.attending[service] = nextTurn
            print(f"Atendiendo el turno {service}-{nextTurn}")  # Debug
            self.update_display(service)
            self.show_alert(service, nextTurn)
            # Updates current turn status to "atendido" in DB
            self.cursor.execute('''
                UPDATE turnos SET estado = 'atendido', llamado = datetime('now')
                WHERE servicio = ? AND numero = ? AND DATE(creado) = DATE('now')
                                ''', (service, nextTurn))
            self.conn.commit()
        else:
            self.attending[service] = None
            self.update_display(service)
            print(f"No hay turnos en espera para la caja {service}")  # Debug
    
    # Loads pending turn from DB if created today
    def init_display(self):
        for servicio in self.queue:
            self.update_display(servicio, init_mode=True)

    # 
    def update_display(self, caja, init_mode=False):
        # For debugging:
        print(f"Actualizando display de la caja {caja}") 
        print(f"Grid layout before update:")
        for r in range(self.gridLayout.rowCount()):
            for c in range(self.gridLayout.columnCount()):
                item = self.gridLayout.itemAtPosition(r, c)
                if item and item.widget():
                    print(f"Row {r}, Col {c}: {item.widget().text()}")
        col = ord(caja.upper()) - ord('A') + 1
        # Calls in next turn to attend
        if not init_mode:
            itemToRemove = self.gridLayout.itemAtPosition(1, col)
            if itemToRemove:
                print(f"Item to remove: {itemToRemove.widget().text()}")  # Debug
                if widget := itemToRemove.widget():
                    widget.deleteLater()
                    widget.setGraphicsEffect(None) # Removes shadow effect to prevent lingering
                    #widget.graphicsEffect().setEnabled(False) Use this instead of the line above if it presents any issues
                self.gridLayout.removeItem(itemToRemove)
            else: # Use this block to show feedback when the queue is empty
                print("No item to remove (station free)")  # Debug
            
            # Add new ticket being attended
            if self.attending[caja]:
                ticket = QLabel(f"{caja}-{self.attending[caja]}")
                self.style_label(ticket, True)
                self.gridLayout.addWidget(ticket, 1, col)
        # Remove all waiting tickets
        for row in range(3, self.gridLayout.columnCount()):
            if item:= self.gridLayout.itemAtPosition(row, col):
                item.widget().deleteLater()
                item.widget().setGraphicsEffect(None) # Removes shadow effect to prevent lingering
        # Add waiting tickets
        for idx, ticket_num in enumerate(self.queue[caja]):
            ticket = QLabel(f"{caja}-{ticket_num}")
            self.style_label(ticket, False)
            self.gridLayout.addWidget(ticket, 3+idx, col)
        # Print grid layout after update for debugging
        print(f"Grid layout after update:")
        for r in range(self.gridLayout.rowCount()):
            for c in range(self.gridLayout.columnCount()):
                item = self.gridLayout.itemAtPosition(r, c)
                if item and item.widget():
                    print(f"Row {r}, Col {c}: {item.widget().text()}")
    
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
            item = self.gridLayout.itemAtPosition(1, col)
            item.widget().deleteLater()
            item.widget().setGraphicsEffect(None)
            print(f"Canceled turn in {service}")
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
        self.alertaTurno.setText(f"""
            <div style='text-align: center;'>
                <span style='font-size: 250px; font-weight: bold;'>{turnPrefix}-{turnNumber}</span><br>
                <span style='font-size: 80px;'>{service}</span>
            </div>
                                 """)
        self.alertaTurno.show_box()
        self.alertaTurno.anim.finished.connect(self.alertaTurno.hide_box)
        self.alertaTurno.anim.start()

    # Sets style for turn labels
    def style_label(self, label, atendiendo):
        label.setAutoFillBackground(True)  # Crucial for background rendering, whatever that means
        if atendiendo:
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
        label.setAlignment(Qt.AlignCenter)
        labelShadow = QGraphicsDropShadowEffect(label, blurRadius=5)
        labelShadow.setOffset(3,3)
        label.setGraphicsEffect(labelShadow)
    
    # Styles and adds header labels to the grid
    def add_header(self, text, row, col):
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
        self.gridLayout.addWidget(label, row, col)

    # repositions turn alert when resizing
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_turn_alert()

    # Positions turn alert on the middle
    def position_turn_alert(self):
        self.alertaTurno.move(
            (self.width() - self.alertaTurno.width()) // 2,
            (self.height() - self.alertaTurno.height()) // 2
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
            print(f"DEBUG: Service {servicio} - Last: {ultNum} → New: {nuevoNum}") #Debug
            # Insert turn to DB
            self.cursor.execute('''
                INSERT INTO turnos (cliente_id, servicio, numero, estado, creado)
                VALUES (
                    (SELECT id FROM clientes WHERE identificacion = ?),
                    ?, ?, 'pendiente', datetime('now'))''', (cliente_id, servicio, nuevoNum))
            self.conn.commit()
            # Add turn to queue and grid
            self.queue[servicio].append(nuevoNum)
            col = ord(servicio.upper()) - ord('A') + 1
            ticket = QLabel(f"{servicio}-{nuevoNum}")
            self.style_label(ticket, True)
            self.gridLayout.addWidget(ticket, self.queue[servicio][-1]+2, col)

        except Exception as e:
            print(f"Error creating ticket: {e}")
            self.conn.rollback()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Digiturno()
    sys.exit(app.exec_())