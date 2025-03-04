import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class CajaTurno(QLabel):
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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digiturno")
        self.turno = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}
        self.queue = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}
        
        self.init_ui()
        self.showFullScreen()

    def init_ui(self):
        # Central widget setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.setBackgroundImage("background.png")

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
        self.addTicket('A', '101')
        self.addTicket('B', '102')
        self.addTicket('C', '103')
        self.addTicket('D', '104')
        self.addTicket('E', '105')
        self.addTicket('A', '106')
        self.addTicket('B', '107')
        self.addTicket('C', '108')
        self.addTicket('D', '109')
        self.addTicket('E', '110')
        self.addTicket('A', '111')
        self.addTicket('D', '112')
        self.addTicket('D', '113')

        #self.next_btn = QPushButton("Siguiente Turno", clicked=self.siguiente_turno)

        # Turn display box
        self.caja_turno = CajaTurno(self)
        self.positionOverlayBox()

        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateAnimation)

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

    def addTicket(self, caja, num):
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

    def setBackgroundImage(self, image_path):
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
        self.caja_turno.move(
            (self.width() - self.caja_turno.width()) // 2,
            (self.height() - self.caja_turno.height()) // 2
        )

    def siguiente_turno(self):
        self.turno += 1
        self.caja_turno.setText(f"Turno: {self.turno}")
        self.animation_step = 0
        self.timer.start(800)

    def updateAnimation(self):
        if self.animation_step < 10:
            self.caja_turno.setVisible(self.animation_step % 2 == 0)
            self.animation_step += 1
        else:
            self.timer.stop()
            self.caja_turno.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Digiturno()
    sys.exit(app.exec_())