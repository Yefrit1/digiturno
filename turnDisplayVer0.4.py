import sys
import sqlite3
import socket
import threading
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
    command_recieved = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.init_db()

        self.setWindowTitle("Digiturno")
        self.atendiendo = {'A': [], 'B': [], 'C': [], 'D': [], 'E': []}
        self.queue = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}
        
        self.init_ui()
        self.showFullScreen()
        self.start_server()

    def init_ui(self):
        # Central widget setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.set_background("background.png")

        # Main layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header
        header = QLabel("Sistema de Gestión de Turnos")
        header.setStyleSheet("font-size: 40px; font-weight: bold; color: #002E08;")
        main_layout.addWidget(header, alignment=Qt.AlignCenter)

        # Content frame
        content_frame = BackgroundFrame()
        main_layout.addWidget(content_frame, stretch=1)

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

        # Add sample tickets
        self.crear_ticket('A', '101')
        self.crear_ticket('B', '102')
        self.crear_ticket('C', '103')
        self.crear_ticket('D', '104')
        self.crear_ticket('E', '105')
        self.crear_ticket('A', '106')
        self.crear_ticket('B', '107')
        self.crear_ticket('C', '108')
        self.crear_ticket('D', '109')
        self.crear_ticket('E', '110')
        self.crear_ticket('A', '111')
        self.crear_ticket('D', '112')
        self.crear_ticket('D', '113')

        #self.next_btn = QPushButton("Siguiente Turno", clicked=self.nextTurn)

        # Turn display box
        self.alertaTurno = AlertaTurno(self)
        self.positionOverlayBox()

        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateAnimation)

    def start_server(self):
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()
    
    def run_server(self):
        HOST = '0.0.0.0'
        PORT = 47529

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            while True:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024).decode('utf-8').strip()
                    if data:
                        self.command_recieved.emit(data)
    
    def handle_command(self, command):
        if command.startswith('NEXT_'):
            caja = command.split('_')[1]
            self.siguiente_turno(caja)

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
    
    def siguiente_turno(self, caja):
        if self.queue[caja]:
            siguiente_ticket = self.queue[caja].pop(0)
            self.atendiendo[caja] = siguiente_ticket
            self.actualizar_display(caja)
            self.mostrar_turno(f"{caja}-{siguiente_ticket}")
    
    def actualizar_display(self, caja):
        row = ord(caja.upper()) - ord('A') + 1
        if self.gridLayout.itemAtPosition(row, 1):
            self.gridLayout.itemAtPosition(row, 1).widget().deleteLater()
        
        if self.atendiendo[caja]:
            ticket = QLabel(f"{caja}-{self.atendiendo[caja]}")
            self.gridLayout.addWidget(ticket, row, 1)
        
        for col in range(3, self.gridLayout.columnCount()):
            if item:= self.gridLayout.itemAtPosition(row, col):
                item.widget().deleteLater()
        
        for idx, ticket_num in enumerate(self.queue[caja]):
            ticket = QLabel(f"{caja}-{ticket_num}")
            ticket.setAutoFillBackground(True)  # Crucial for background rendering
            ticket.setStyleSheet(f"""
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
            ticket.setAlignment(Qt.AlignCenter)
            self.gridLayout.addWidget(ticket, row, 3+idx)
    
    def mostrar_turno(self, turno):
        self.alertaTurno.setText(turno)
        self.animation_step = 0
        self.timer.start(800)

    def crear_ticket(self, caja, num):
        row = ord(caja.upper()) - ord('A')
        col = self.queue[caja]
        
        ticket = QLabel(f"{caja}-{num}")
        ticket.setAutoFillBackground(True)  # Crucial for background rendering
        ticket.setStyleSheet(f"""
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
        ticket.setAlignment(Qt.AlignCenter)
        if self.queue[caja] == 0:
            self.gridLayout.addWidget(ticket, row+1, col+1, alignment=Qt.AlignTop | Qt.AlignLeft)
        else:
            self.gridLayout.addWidget(ticket, row+1, col+1+self.queue[caja], alignment=Qt.AlignTop | Qt.AlignLeft)
        self.queue[caja] += 1

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

    def updateAnimation(self):
        if self.animation_step < 10:
            self.alertaTurno.setVisible(self.animation_step % 2 == 0)
            self.animation_step += 1
        else:
            self.timer.stop()
            self.alertaTurno.hide()
    
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