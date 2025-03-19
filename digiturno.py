import sys, sqlite3
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
        self.ascHbox1.setContentsMargins(0, 0, 0, self.screen_height(5))

        labelAscID = QLabel("Ingresa tu cédula")
        self.style_label(labelAscID, 5)

        spacer2 = QLabel() # Spacing

        self.add_logo(self.ascHbox1)
        self.ascHbox1.addWidget(labelAscID)
        self.ascHbox1.addWidget(spacer2)
        #
        self.ascHbox2 = QHBoxLayout()
        self.ascHbox2.setAlignment(Qt.AlignCenter)

        self.ascId = QLineEdit()
        self.ascId.setFixedWidth(self.screen_width(60))
        self.style_line_edit(self.ascId, 8)
        self.ascId.setReadOnly(True)

        self.ascHbox2.addWidget(self.ascId)
        #
        self.ascHbox3 = QHBoxLayout()

        spacer3 = QLabel()

        self.ascKpad = QGridLayout()
        self.ascKpad.setAlignment(Qt.AlignCenter)
        self.ascKpad.setSpacing(0)
        aKpadButtons = [('7',0,0), ('8',0,1), ('9',0,2),
                        ('4',1,0), ('5',1,1), ('6',1,2),
                        ('1',2,0), ('2',2,1), ('3',2,2),
                        ('',3,0), ('0',3,1), ('',3,2)]
        for text,row,col in aKpadButtons:
            akButton = QPushButton(text)
            akButton.setFixedWidth(self.screen_width(10))
            self.style_button(akButton, 5, 15, 2)
            akButton.clicked.connect(self.kpad_pressed)
            self.ascKpad.addWidget(akButton, row, col)
        
        spacer4 = QLabel()

        self.ascHbox3.addWidget(spacer3)
        self.ascHbox3.addLayout(self.ascKpad)
        self.ascHbox3.addWidget(spacer4)
        #
        self.ascHbox4 = QHBoxLayout()
        self.ascHbox4.setSpacing(0)

        ascReturn = QPushButton("Volver")
        ascReturn.setFixedSize(self.screen_width(15), self.screen_height(11))
        self.style_button(ascReturn, 3, 15, 2, "return.png",4)
        ascReturn.clicked.connect(self.serv_volver)

        spacer5 = QLabel()

        ascDel = QPushButton("Borrar")
        ascDel.setFixedSize(self.screen_width(15), ascReturn.height())
        self.style_button(ascDel, 3, 15, 2, "delete.png",5)
        ascDel.clicked.connect(self.kpad_delete)

        ascOk = QPushButton("Confirmar")
        ascOk.setFixedSize(self.screen_width(15), ascReturn.height())
        self.style_button(ascOk, 2.3, 15, 2, "ok.png", 4)
        ascOk.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))

        spacer6 = QLabel()
        spacer7 = QLabel()
        spacer7.setFixedWidth(ascReturn.width())

        self.ascHbox4.addWidget(ascReturn)
        self.ascHbox4.addWidget(spacer5)
        self.ascHbox4.addWidget(ascDel)
        self.ascHbox4.addWidget(ascOk)
        self.ascHbox4.addWidget(spacer6)
        self.ascHbox4.addWidget(spacer7)
        #
        self.layoutAsc.addLayout(self.ascHbox1)
        self.layoutAsc.addLayout(self.ascHbox2)
        self.layoutAsc.addLayout(self.ascHbox3)
        self.layoutAsc.addLayout(self.ascHbox4)
        
        """
####### Layout NO ASOCIADO #######
        self.noAsc = QWidget()
        self.layoutNoAsc = QVBoxLayout(self.noAsc)
        self.layoutNoAsc.setAlignment(Qt.AlignTop)
        #
        self.noAscHbox1 = QHBoxLayout()
        self.noAscHbox1.setContentsMargins(0, 0, 0, self.screen_height(5))

        labelNoAscID = QLabel("Ingresa tu cédula")
        self.style_label(labelNoAscID, 5)

        spacer8 = QLabel() # Spacing

        self.add_logo(self.noAscHbox1)
        self.noAscHbox1.addWidget(labelNoAscID)
        self.noAscHbox1.addWidget(spacer8)
        #
        self.noAscHbox2 = QHBoxLayout()
        self.noAscHbox2.setAlignment(Qt.AlignCenter)

        self.noAscId = QLineEdit()
        self.noAscId.setFixedWidth(self.screen_width(60))
        self.style_line_edit(self.noAscId, 8)
        self.noAscId.setReadOnly(True)

        self.noAscHbox2.addWidget(self.noAscId)
        #
        self.noAscHbox3 = QHBoxLayout()

        spacer9 = QLabel()

        self.noAscKpad = QGridLayout()
        self.noAscKpad.setAlignment(Qt.AlignCenter)
        self.noAscKpad.setSpacing(0)
        nKpadButtons = [('7',0,0), ('8',0,1), ('9',0,2),
                        ('4',1,0), ('5',1,1), ('6',1,2),
                        ('1',2,0), ('2',2,1), ('3',2,2),
                        ('',3,0), ('0',3,1), ('',3,2)]
        for text,row,col in nKpadButtons:
            nkButton = QPushButton(text)
            nkButton.setFixedWidth(self.screen_width(10))
            self.style_button(nkButton, 5, 15, 2)
            nkButton.clicked.connect(self.kpad_pressed)
            self.noAscKpad.addWidget(nkButton, row, col)
        
        spacer10 = QLabel()

        self.noAscHbox3.addWidget(spacer9)
        self.noAscHbox3.addLayout(self.noAscKpad)
        self.noAscHbox3.addWidget(spacer10)
        #
        self.noAscHbox4 = QHBoxLayout()
        self.noAscHbox4.setSpacing(0)

        noAscReturn = QPushButton("Volver")
        noAscReturn.setFixedSize(self.screen_width(15), self.screen_height(11))
        self.style_button(noAscReturn, 3, 15, 2, "return.png",4)
        noAscReturn.clicked.connect(self.serv_volver)

        spacer11 = QLabel()

        noAscDel = QPushButton("Borrar")
        noAscDel.setFixedSize(self.screen_width(15), noAscReturn.height())
        self.style_button(noAscDel, 3, 15, 2, "delete.png",5)
        noAscDel.clicked.connect(self.kpad_delete)

        noAscOk = QPushButton("Confirmar")
        noAscOk.setFixedSize(self.screen_width(15), noAscReturn.height())
        self.style_button(noAscOk, 2.3, 15, 2, "ok.png", 4)
        noAscOk.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))

        spacer12 = QLabel()
        spacer13 = QLabel()
        spacer13.setFixedWidth(noAscReturn.width())

        self.noAscHbox4.addWidget(noAscReturn)
        self.noAscHbox4.addWidget(spacer11)
        self.noAscHbox4.addWidget(noAscDel)
        self.noAscHbox4.addWidget(noAscOk)
        self.noAscHbox4.addWidget(spacer12)
        self.noAscHbox4.addWidget(spacer13)
        #
        self.layoutNoAsc.addLayout(self.noAscHbox1)
        self.layoutNoAsc.addLayout(self.noAscHbox2)
        self.layoutNoAsc.addLayout(self.noAscHbox3)
        self.layoutNoAsc.addLayout(self.noAscHbox4)
        """

####### Layout SERVICIO #######
        self.serv = QWidget()
        self.layoutServ = QVBoxLayout(self.serv)
        bluleibel = QLabel("SERVICIO")
        self.style_label(bluleibel, 5)
        volverAsc = QPushButton("Volver")
        volverAsc.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.layoutServ.addWidget(bluleibel)
        self.layoutServ.addWidget(volverAsc)

####### Stack layouts #######
        self.stackedWidget.addWidget(self.ent)
        self.stackedWidget.addWidget(self.asc)
        #self.stackedWidget.addWidget(self.noAsc)
        self.stackedWidget.addWidget(self.serv)

        self.init_db()
        self.showFullScreen()

    # Called when a button from the keypad is pressed
    def kpad_pressed(self):
        if self.stackedWidget.currentIndex() == 1:
            button = self.sender()
            current_number = self.ascId.text()
            new_number = current_number + button.text()
            self.ascId.setText(new_number)
        elif self.stackedWidget.currentIndex() == 2:
            button = self.sender()
            current_number = self.noAscId.text()
            new_number = current_number + button.text()
            self.noAscId.setText(new_number)

    def kpad_delete(self):
        # For single digit deletion
        if self.stackedWidget.currentIndex() == 1:
            self.ascId.setText(self.ascId.text()[:-1])
        elif self.stackedWidget.currentIndex() == 2:
            self.noAscId.setText(self.noAscId.text()[:-1])
        # For clearing the whole line, just setText to ""

    def serv_volver(self):
        self.stackedWidget.setCurrentIndex(0)
        self.ascId.setText("")
    
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
    def style_button(self, button, fontSize, radius, border, img=None, imgSize=None):
        styleSheet = f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0.5, y1:0, x2:0.5, y2:1,
                    stop:0 #85A947, stop:1 #3E7B27
                );
                border-radius: {radius}px;
                border: {border}px solid white;
                color: white;
                font-size: {self.screen_width(fontSize)}px;
            }}
            QPushButton:pressed{{
                background: qlineargradient(
                    x1:0.5, y1:0, x2:0.5, y2:1,
                    stop:0 #A9DB55, stop:1 #85A947
                )
            }}
        """
        if img:
            styleSheet += f"""
                QPushButton {{
                    qproperty-icon: url({img});
                    qproperty-iconSize: {self.screen_width(imgSize)}px;
                }}
            """
        button.setStyleSheet(styleSheet)
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
    
    def init_db(self):
        self.conn = sqlite3.connect('digiturno.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())