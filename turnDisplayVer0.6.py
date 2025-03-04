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
            background-color: #6FDE42;
            font-size: 100px;
            font-weight: bold;
            color: white;
            border-radius: 30px;
        """)
        self.setFixedSize(500, 250)
        self.hide()

    def show_box(self):
        self.show()

    def hide_box(self):
        self.hide()

class BackgroundFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            BackgroundFrame {
                background-color: rgba(240, 240, 240, 50);
                border-radius: 20px;
            }
        """)

class Digiturno(QMainWindow):
    command_received = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.init_db()
        self.command_received.connect(self.handle_command)

        self.setWindowTitle("Digiturno")
        self.atendiendo = {'A': [], 'B': [], 'C': [], 'D': [], 'E': []}
        self.queue = {'A': [1, 5, 10], 'B': [3, 8, 9], 'C': [7, 11], 'D': [2, 4, 13], 'E': [6, 12, 14]}
        
        self.init_ui()
        self.showFullScreen()
        self.start_server()

    def init_ui(self):
        # Central widget setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.set_background("background7.jpg")

        # Main layout
        mainLayout = QVBoxLayout(self.central_widget)
        mainLayout.setContentsMargins(20, 20, 20, 20)
        mainLayout.setSpacing(20)

        # Header layout
        headerLayout = QHBoxLayout()
        headerLayout.setContentsMargins(0, 0, 0, 0)

        # Logo
        labelLogo = QLabel()
        pixmapLogo = QPixmap("logoCoohem.png")  # Replace with your logo path
        labelLogo.setPixmap(pixmapLogo)
        headerLayout.addWidget(labelLogo)
        headerLayout.addStretch()

        # Clock
        self.clockLabel = QLabel()
        self.clockLabel.setStyleSheet("""
            font-size: 60px;
            color: white;
            font-weight: bold;
                                      """)
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
        self.gridLayout.setContentsMargins(20, 20, 20, 20)

        # Headers
        self.addHeader("Atendiendo", 0, 1)
        spanLabel = QLabel("")
        spanLabel.setFixedSize(50, 120)
        self.gridLayout.addWidget(spanLabel, 0, 2)
        self.addHeader("En espera", 0, 3)
        self.addHeader("Caja 1", 1, 0)
        self.addHeader("Caja 2", 2, 0)
        self.addHeader("Caja 3", 3, 0)
        self.addHeader("Caja 4", 4, 0)
        self.addHeader("Caja 5", 5, 0)

        # Turn display box
        self.alertaTurno = AlertaTurno(self)
        self.positionOverlayBox()

        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)

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

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
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
    
    def handle_command(self, command):
        print(f"Handling command: {command}")  # Debug
        if command.startswith('NEXT_'):
            caja = command.split('_')[1]
            print(f"Calling next turn for {caja}")  # Debug
            self.siguiente_turno(caja)
    
    def siguiente_turno(self, caja):
        if self.queue[caja]:
            siguiente_ticket = self.queue[caja].pop(0)
            self.atendiendo[caja] = siguiente_ticket
            print(f"Atendiendo el turno {caja}-{siguiente_ticket}")  # Debug
            self.actualizar_display(caja)
            self.mostrar_turno(f"{caja}-{siguiente_ticket}")
        else:
            self.atendiendo[caja] = None
            self.actualizar_display(caja)
            print(f"No hay turnos en espera para la caja {caja}")  # Debug
    
    def actualizar_display(self, caja):
        # For debugging:
        print(f"Actualizando display de la caja {caja}") 
        print(f"Grid layout before update:")
        for r in range(self.gridLayout.rowCount()):
            for c in range(self.gridLayout.columnCount()):
                item = self.gridLayout.itemAtPosition(r, c)
                if item and item.widget():
                    print(f"Row {r}, Col {c}: {item.widget().text()}")
        
        # Remove current ticket being attended
        row = ord(caja.upper()) - ord('A') + 1
        itemToRemove = self.gridLayout.itemAtPosition(row, 1)
        if itemToRemove:
            print(f"Item to remove: {itemToRemove.widget().text()}")  # Debug
            if widget := itemToRemove.widget():
                widget.deleteLater()
            self.gridLayout.removeItem(itemToRemove)
        else: # Use this block to show feedback when the queue is empty
            print("No item to remove (queue empty)")  # Debug
        
        # Add new ticket being attended
        if self.atendiendo[caja]:
            ticket = QLabel(f"{caja}-{self.atendiendo[caja]}")
            self.style_label(ticket)
            self.gridLayout.addWidget(ticket, row, 1)
        
        # Remove all waiting tickets
        for col in range(3, self.gridLayout.columnCount()):
            if item:= self.gridLayout.itemAtPosition(row, col):
                item.widget().deleteLater()
        
        # Add waiting tickets
        for idx, ticket_num in enumerate(self.queue[caja]):
            ticket = QLabel(f"{caja}-{ticket_num}")
            self.style_label(ticket)
            self.gridLayout.addWidget(ticket, row, 3+idx)
        
        # Print grid layout after update
        print(f"Grid layout after update:")
        for r in range(self.gridLayout.rowCount()):
            for c in range(self.gridLayout.columnCount()):
                item = self.gridLayout.itemAtPosition(r, c)
                if item and item.widget():
                    print(f"Row {r}, Col {c}: {item.widget().text()}") # Debug
    
    def mostrar_turno(self, turno):
        self.alertaTurno.setText(turno)
        self.animation_step = 0
        self.timer.start(800)

    def style_label(self, label):
        label.setAutoFillBackground(True)  # Crucial for background rendering
        label.setStyleSheet(f"""
            QLabel {{
                background-color: white;
                background-image: none;
                border-radius: 5px;
                color: #002E08;
                font-size: 50px;
                font-weight: bold;
                padding: 10px;
                min-width: 190px;
                min-height: 120px;
            }}
            """)
        label.setAlignment(Qt.AlignCenter)
    
    def addHeader(self, text, row, col):
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(0, 0, 0, 0.5);
                background-image: none;
                border-radius: 5px;
                color: white;
                font-size: 30px;
                font-weight: bold;
                padding: 10px;
                min-width: 190px;
                min-height: 120px;
            }}
            """)
        label.setAlignment(Qt.AlignCenter)
        self.gridLayout.addWidget(label, row, col)

    def set_background(self, image_path):
        try:
            self.central_widget.setObjectName("MainBackground")
            style = f"""
                QWidget#MainBackground {{
                    background-image: url({image_path});
                    background-position: center;
                    background-repeat: no-repeat;
                    background-attachment: fixed;
                }}
            """
            self.central_widget.setStyleSheet(style)
        except Exception as e:
            print(f"Background error: {e}")
            self.central_widget.setStyleSheet("QWidget#MainBackground {background-color: #33A62B;}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.positionOverlayBox()

    def positionOverlayBox(self):
        self.alertaTurno.move(
            (self.width() - self.alertaTurno.width()) // 2,
            (self.height() - self.alertaTurno.height()) // 2
        )

    def update_animation(self):
        if self.animation_step < 10:
            self.alertaTurno.setVisible(self.animation_step % 2 == 0)
            self.animation_step += 1
        else:
            self.timer.stop()
            self.alertaTurno.hide()
        
    def update_clock(self):
        currentTime = datetime.now().strftime("%H:%M:%S")
        self.clockLabel.setText(currentTime)
    
    def init_db(self):
        self.conn = sqlite3.connect('digiturno.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS turnos (
                id INTEGER PRIMARY KEY,
                servicio TEXT NOT NULL,
                numero TEXT NOT NULL,
                estado TEXT NOT NULL, -- 'pendiente', 'atendido', 'cancelado'
                creado DATETIME,
                llamado DATETIME
            ) ''')
        self.conn.commit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Digiturno()
    sys.exit(app.exec_())