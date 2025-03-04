import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class CajaTurno(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            """
                background-color: #6FDE42;
                font-size: 100px;
                font-weight: bold;
                color: white;
                border-radius: 40px;
            """)
        self.setFixedSize(500, 250)
        self.hide()

    def show_box(self):
        """Show the box."""
        self.show()

    def hide_box(self):
        """Hide the box."""
        self.hide()

class Digiturno(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digiturno")
        self.turno = 0
        self.queueTurnCounter = 0

        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.vBoxMain = QVBoxLayout(central_widget)
        self.hBox1 = QHBoxLayout()
        self.hBox2 = QHBoxLayout()
        self.hBox3 = QHBoxLayout()
        self.hBox4 = QHBoxLayout()
        self.hBox5 = QHBoxLayout()
        self.hBox6 = QHBoxLayout()
        self.hBox7 = QHBoxLayout()
        self.hBoxSimulator = QHBoxLayout()

        self.cajaTurno = CajaTurno(f"Turno: {self.turno}", self)
        self.cajaTurno.hide()

        # Logo
        labelLogo = QLabel()
        labelLogo.setAlignment(Qt.AlignTop)
        pixmapLogo = QPixmap("logoCoohem.png")  # Replace with your logo path
        labelLogo.setPixmap(pixmapLogo)
        
        # Button
        botonSiguiente = QPushButton("Simulate New Turn", self)
        botonSiguiente.clicked.connect(self.turnoSiguiente)

        # HBOX1: Logo
        self.hBox1.addStretch()
        self.hBox1.addWidget(labelLogo)
        self.hBox1.addStretch()

        # Background image label
        self.background_label = QLabel(self)
        self.background_label.setAlignment(Qt.AlignCenter)
        self.background_label.setScaledContents(True)  # Scale the image to fit the label
        pixmap = QPixmap("background.png")
        self.background_label.setPixmap(pixmap)

        # Container for hBox2, hBox3, and hBox4
        content_container = QWidget()
        content_container.setLayout(QVBoxLayout())
        content_container.layout().addSpacing(20)
        content_container.layout().addLayout(self.hBox2)
        content_container.layout().addSpacing(20)
        content_container.layout().addLayout(self.hBox3)
        content_container.layout().addSpacing(80)
        content_container.layout().addLayout(self.hBox4)
        content_container.layout().addSpacing(20)
        content_container.layout().addLayout(self.hBox5)
        content_container.layout().addLayout(self.hBox6)
        content_container.layout().addLayout(self.hBox7)
        content_container.layout().addStretch()

        overlay_layout = QVBoxLayout(self.background_label)
        overlay_layout.addWidget(content_container)

        # HBOX2: Texto "Atendiendo"
        labelAtendiendo = QLabel("Atendiendo:")
        labelAtendiendo.setAlignment(Qt.AlignLeft)
        labelAtendiendo.setStyleSheet("font-size: 30px; font-weight: bold; color: #002E08;")
        
        self.hBox2.addSpacing(30)
        self.hBox2.addWidget(labelAtendiendo)

        # HBOX3: Turnos atendiendo
        # Límite: 8 turnos
        self.hBox3.addSpacing(20)
        self.addProceedingTurn("A", "110", "Caja 1")
        self.addProceedingTurn("B", "111", "Caja 2")
        self.addProceedingTurn("C", "112", "Caja 3")
        self.addProceedingTurn("D", "113", "Caja 4")
        self.addProceedingTurn("E", "114", "Caja 5")
        self.hBox3.addStretch()

        # HBOX4: Texto "Fila"
        self.hBox4.addSpacing(20)
        labelFila = QLabel("Fila:")
        labelFila.setAlignment(Qt.AlignLeft)
        labelFila.setStyleSheet("font-size: 30px; font-weight: bold; color: #002E08;")

        self.hBox4.addWidget(labelFila)

        # HBOX5: Fila de turnos (1)
        self.hBox5.addSpacing(20)
        i = 0
        j = 'A'
        while i < 20:
            self.addQueueTurn(f"{j}", f"{110+i}", f"Caja {j}")
            i += 1
            j = chr(ord(j) + 1)
        self.hBox5.addStretch()

        # HBOX6: Fila de turnos (2)
        self.hBox6.addStretch()

        # HBOX7: Fila de turnos (3)
        self.hBox7.addWidget(botonSiguiente)
        self.hBox7.addStretch()

        # Add everything to the main layout
        self.vBoxMain.addLayout(self.hBox1)
        self.vBoxMain.addSpacing(20)
        self.vBoxMain.addWidget(self.background_label)  # Add the background label

        # Timer for animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.animation_step = 0

        self.showFullScreen()

    def addProceedingTurn(self, turnLetter="", turnNumber="", counter=""):
        # Use HTML to format the label text with different font sizes
        label = QLabel()
        label.setText(
            f"""
            <div style='text-align: center;'>
                <span style='font-size: 40px; font-weight: bold;'>{turnLetter}-{turnNumber}</span><br>
                <span style='font-size: 20px;'>{counter}</span>
            </div>
            """
        )
        label.setAlignment(Qt.AlignCenter)
        label.setFixedSize(190, 120)
        label.setStyleSheet(
            """
                background-color: white;
                border-radius: 5px;
                color: #002E08;
            """
        )
        self.hBox3.addWidget(label)

    def addQueueTurn(self, turnLetter="", turnNumber="", counter=""):
        # Use HTML to format the label text with different font sizes
        label = QLabel()
        label.setText(
            f"""
            <div style='text-align: center;'>
                <span style='font-size: 40px; font-weight: bold;'>{turnLetter}-{turnNumber}</span><br>
                <span style='font-size: 20px;'>{counter}</span>
            </div>
            """
        )
        label.setAlignment(Qt.AlignCenter)
        label.setFixedSize(190, 120)
        label.setStyleSheet(
            """
                background-color: white;
                border-radius: 5px;
                color: #002E08;
            """
        )
        if self.queueTurnCounter < 8:
            self.hBox5.addWidget(label)
        elif self.queueTurnCounter < 16:
            if self.queueTurnCounter == 8:
                self.hBox6.addSpacing(20)
            self.hBox6.addWidget(label)
        else:
            if self.queueTurnCounter == 16:
                self.hBox7.addSpacing(20)
            self.hBox7.addWidget(label)            
        self.queueTurnCounter += 1

    def resizeEvent(self, event):
        """Override resizeEvent to position the overlay box in the center."""
        super().resizeEvent(event)
        self.position_overlay_box()

    def position_overlay_box(self):
        x = (self.width() - self.cajaTurno.width()) // 2
        y = (self.height() - self.cajaTurno.height()) // 2
        self.cajaTurno.move(x, y)

    def turnoSiguiente(self):
        self.turno += 1
        self.cajaTurno.setText(f"Turno: {self.turno}")
        self.animation_step = 0
        self.timer.start(800)  # Intervalo

    def turnoAnterior(self):
        self.turno -= 1
        self.cajaTurno.setText(f"Turno: {self.turno}")
        self.animation_step = 0
        self.timer.start(800)  # Intervalo

    def update_animation(self):
        if self.animation_step < 10:
            if self.animation_step % 2 == 0:
                self.cajaTurno.show_box()
            else:
                self.cajaTurno.hide_box()
            self.animation_step += 1
        else:
            self.timer.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Digiturno()
    window.show()
    sys.exit(app.exec_())