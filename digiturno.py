import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digiturno COOHEM")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.set_background_color(central_widget, "#EFE3C2")
        self.screenGeometry = QApplication.primaryScreen().geometry()

        main_layout = QVBoxLayout(central_widget)
        self.stackedWidget = QStackedWidget()
        main_layout.addWidget(self.stackedWidget)

####### Layout ENTRADA #######
        self.ent = QWidget()
        self.layoutEnt = QVBoxLayout(self.ent)
        self.layoutEnt.setAlignment(Qt.AlignTop)
        self.layoutEnt.setSpacing(self.screen_height(15))
        self.ent.setLayout(self.layoutEnt)
        #
        self.entHbox1 = QHBoxLayout()
        self.entHbox1.setSpacing(5)

        bienvenido = QLabel("Bienvenido")
        self.style_label(bienvenido, 5.5)

        spacer1 = QLabel() # Spacing
        
        self.add_logo(self.entHbox1)
        self.entHbox1.addWidget(bienvenido)
        self.entHbox1.addWidget(spacer1)
        #
        pregunta = QLabel("¿Eres asociado?")
        self.style_label(pregunta, 9)
        #
        self.entHbox2 = QHBoxLayout()
        self.entHbox2.setAlignment(Qt.AlignCenter)
        self.entHbox2.setSpacing(self.screen_width(10))

        self.entNo = QPushButton("No")
        self.entSi = QPushButton("Sí")
        self.entNo.setFixedWidth(self.screen_width(20))
        self.entSi.setFixedWidth(self.screen_width(20))
        self.style_button(self.entNo, 10, 30, 2)
        self.style_button(self.entSi, 10, 30, 2)
        self.entNo.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.entSi.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))

        self.entHbox2.addWidget(self.entNo)
        self.entHbox2.addWidget(self.entSi)
        #
        self.layoutEnt.addLayout(self.entHbox1)
        self.layoutEnt.addWidget(pregunta)
        self.layoutEnt.addLayout(self.entHbox2)

####### Layout ASOCIADO #######
        self.asc = QWidget()
        self.layoutAsc = QVBoxLayout(self.asc)
        self.layoutAsc.setAlignment(Qt.AlignTop)
        #
        self.ascHbox1 = QHBoxLayout()
        self.ascHbox1.setContentsMargins(0, 0, 0, self.screen_height(10))

        labelCedula = QLabel("Ingresa tu cédula")
        self.style_label(labelCedula, 5)

        spacer2 = QLabel() # Spacing

        self.add_logo(self.ascHbox1)
        self.ascHbox1.addWidget(labelCedula)
        self.ascHbox1.addWidget(spacer2)
        #
        self.ascHbox2 = QHBoxLayout()
        self.ascHbox2.setAlignment(Qt.AlignCenter)

        self.cedula = QLineEdit()
        self.cedula.setFixedWidth(self.screen_width(60))
        self.style_line_edit(self.cedula, 8)
        self.cedula.setReadOnly(True)

        self.ascHbox2.addWidget(self.cedula)
        #
        self.ascHbox3 = QHBoxLayout()

        volver = QPushButton("Volver")
        volver.setFixedWidth(self.screen_width(17))
        self.style_button(volver, 5, 15, 2)

        spacer3 = QLabel()

        self.keypad = QGridLayout()
        self.keypad.setAlignment(Qt.AlignCenter)
        self.keypad.setSpacing(0)
        kpadButtons = [('7',0,0), ('8',0,1), ('9',0,2),
                        ('4',1,0), ('5',1,1), ('6',1,2),
                        ('1',2,0), ('2',2,1), ('3',2,2),
                        ('Borrar',3,0), ('0',3,1), ('',3,2)]
        for text,row,col in kpadButtons:
            kButton = QPushButton(text)
            kButton.setFixedWidth(self.screen_width(10))
            if kButton.text() == "Borrar":
                self.style_button(kButton, 2, 15, 2)
                kButton.setFixedHeight(self.keypad.itemAtPosition(0,0).geometry().height())
                print(f"borrar size: {self.keypad.itemAtPosition(0,0).geometry().height()}")
            else: self.style_button(kButton, 5, 15, 2)
            kButton.clicked.connect(self.kpad_pressed)
            print(f"num size: {kButton.height()}")
            self.keypad.addWidget(kButton, row, col)
        
        spacer4 = QLabel()
        spacer5 = QLabel()
        spacer5.setFixedWidth(volver.width())

        self.ascHbox3.addWidget(volver)
        self.ascHbox3.addWidget(spacer3)
        self.ascHbox3.addLayout(self.keypad)
        self.ascHbox3.addWidget(spacer4)
        self.ascHbox3.addWidget(spacer5)
        #
        self.layoutAsc.addLayout(self.ascHbox1)
        self.layoutAsc.addLayout(self.ascHbox2)
        self.layoutAsc.addLayout(self.ascHbox3)
        
####### Layout NO ASOCIADO #######
        self.noAsc = QWidget()
        self.layoutNoAsc = QVBoxLayout(self.noAsc)
        
####### Layout SERVICIO #######
        self.serv = QWidget()
        self.layoutServ = QVBoxLayout(self.serv)

####### Stack layouts #######
        self.stackedWidget.addWidget(self.ent)
        self.stackedWidget.addWidget(self.asc)
        self.stackedWidget.addWidget(self.noAsc)
        self.stackedWidget.addWidget(self.serv)

        self.showFullScreen()

    # Called when a button from the keypad is pressed
    def kpad_pressed(self):
        button = self.sender()
        current_number = self.cedula.text()
        new_number = current_number + button.text()
        self.cedula.setText(new_number)
    
    # Sets stylesheet for a label
    def style_label(self, label, fontSize):
        label.setStyleSheet(f"""
            QLabel {{
                color: #284F1A;
                font-size: {self.screen_width(fontSize)}px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(label, blurRadius=20)
        shadow.setOffset(5, 5)
        label.setGraphicsEffect(shadow)
        label.setAlignment(Qt.AlignCenter)

    # Sets stylesheet for a button
    def style_button(self, button, fontSize, radius, border):
        button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0.5, y1:0, x2:0.5, y2:1,
                    stop:0 #85A947, stop:1 #3E7B27
                );
                border-radius: {radius}px;
                border: {border}px solid black;
                color: white;
                font-size: {self.screen_width(fontSize)}px;
            }}
            QPushButton:pressed{{
                background: qlineargradient(
                    x1:0.5, y1:0, x2:0.5, y2:1,
                    stop:0 #A9DB55, stop:1 #85A947
                )
            }}
        """)
        shadow = QGraphicsDropShadowEffect(button, blurRadius=20)
        shadow.setOffset(5, 5)
        button.setGraphicsEffect(shadow)

    # Sets stylesheet for a line edit
    def style_line_edit(self, label, fontSize):
        label.setStyleSheet(f"""
            QLineEdit {{
                color: #204114;
                border-radius:10px;
                font-size: {self.screen_width(fontSize)}px;
            }}
        """)
        label.setAlignment(Qt.AlignCenter)

    # Adds a logo label
    def add_logo(self, layout):
        label = QLabel()
        label.setAlignment(Qt.AlignTop)
        pixmap = QPixmap("logoCoohem.png")
        label.setPixmap(pixmap)
        shadow = QGraphicsDropShadowEffect(label, blurRadius=20)
        shadow.setOffset(5, 5)
        label.setGraphicsEffect(shadow)
        layout.addWidget(label)

    # Used on a widget to set background color
    def set_background_color(self, widget, color):
        palette = widget.palette()
        palette.setColor(QPalette.Background, QColor(color))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)

    # Used on a widget to set a background pic
    def set_background_image(self, widget):
        pixmap = QPixmap("logoCoohem.png")
        if not pixmap.isNull():
            palette = widget.palette()
            brush = QBrush(pixmap)
            palette.setBrush(QPalette.Window, brush)
            widget.setAutoFillBackground(True)
            widget.setPalette(palette)
    
    # Returns pixel value of screen width % based on parameter
    def screen_width(self, num):
        return int(self.screenGeometry.width()*num/100)
    # Returns pixel value of screen height % based on parameter
    def screen_height(self, num):
        return int(self.screenGeometry.height()*num/100)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())