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

        self.isAsc = False

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
        
        self.add_logo(self.entHbox1)
        self.entHbox1.addWidget(bienvenido)
        self.add_spacer(self.entHbox1)
        #
        pregunta = QLabel("¿Es asociado?")
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
        self.entNo.clicked.connect(self.go_to_ced)
        self.entSi.clicked.connect(self.go_to_ced)

        self.entHbox2.addWidget(self.entNo)
        self.entHbox2.addWidget(self.entSi)
        #
        self.layoutEnt.addLayout(self.entHbox1)
        self.layoutEnt.addWidget(pregunta)
        self.layoutEnt.addLayout(self.entHbox2)

####### Layout CÉDULA #######
        self.ced = QWidget()
        self.layoutCed = QVBoxLayout(self.ced)
        self.layoutCed.setAlignment(Qt.AlignTop)
        #
        self.cedHbox1 = QHBoxLayout()
        self.cedHbox1.setContentsMargins(0, 0, 0, self.screen_height(5))

        labelCedula = QLabel("Ingrese su cédula")
        self.style_label(labelCedula, 5)

        self.add_logo(self.cedHbox1)
        self.cedHbox1.addWidget(labelCedula)
        self.add_spacer(self.cedHbox1)
        #
        self.cedHbox2 = QHBoxLayout()
        self.cedHbox2.setAlignment(Qt.AlignCenter)

        self.lineID = QLineEdit()
        self.lineID.setFixedWidth(self.screen_width(60))
        self.style_line_edit(self.lineID, 8)
        self.lineID.setReadOnly(True)

        self.cedHbox2.addWidget(self.lineID)
        #
        self.cedHbox3 = QHBoxLayout()

        self.kpadLayout = QGridLayout()
        self.kpadLayout.setAlignment(Qt.AlignCenter)
        self.kpadLayout.setSpacing(0)
        kpadButtons = [('7',0,0), ('8',0,1), ('9',0,2),
                        ('4',1,0), ('5',1,1), ('6',1,2),
                        ('1',2,0), ('2',2,1), ('3',2,2),
                        ('',3,0), ('0',3,1), ('',3,2)]
        for text,row,col in kpadButtons:
            kpadButton = QPushButton(text)
            kpadButton.setFixedWidth(self.screen_width(10))
            self.style_button(kpadButton, 5, 15, 2)
            kpadButton.clicked.connect(self.kpad_pressed)
            self.kpadLayout.addWidget(kpadButton, row, col)

        self.add_spacer(self.cedHbox3)
        self.cedHbox3.addLayout(self.kpadLayout)
        self.add_spacer(self.cedHbox3)
        #
        self.cedHbox4 = QHBoxLayout()
        self.cedHbox4.setSpacing(0)

        cedReturn = QPushButton(" Volver")
        cedReturn.setFixedSize(self.screen_width(15), self.screen_height(11))
        self.style_button(cedReturn, 3, 15, 2, "return.png",4)
        cedReturn.clicked.connect(self.ced_return)

        cedDel = QPushButton("Borrar")
        cedDel.setFixedSize(self.screen_width(15), cedReturn.height())
        self.style_button(cedDel, 3, 15, 2, "delete.png",5, True)
        cedDel.clicked.connect(self.kpad_pressed)

        nomOk = QPushButton("Confirmar")
        nomOk.setFixedSize(self.screen_width(15), cedReturn.height())
        self.style_button(nomOk, 2.3, 15, 2, "ok.png", 3.5)
        nomOk.clicked.connect(self.confirm_ced)

        self.cedHbox4.addWidget(cedReturn)
        self.add_spacer(self.cedHbox4)
        self.cedHbox4.addWidget(cedDel)
        self.cedHbox4.addWidget(nomOk)
        self.add_spacer(self.cedHbox4)
        self.add_spacer(self.cedHbox4, cedReturn.width())
        #
        self.layoutCed.addLayout(self.cedHbox1)
        self.layoutCed.addLayout(self.cedHbox2)
        self.layoutCed.addLayout(self.cedHbox3)
        self.layoutCed.addLayout(self.cedHbox4)
        
####### Layout NOMBRE (no asociado)
        
        self.nom = QWidget()
        self.layoutNom = QVBoxLayout(self.nom)
        self.layoutNom.setAlignment(Qt.AlignTop)
        #
        self.nomHbox1 = QHBoxLayout()
        self.nomHbox1.setContentsMargins(0,0,0, self.screen_height(8))

        labelNombre = QLabel("Ingrese su nombre:")
        self.style_label(labelNombre, 5)

        self.add_logo(self.nomHbox1)
        self.nomHbox1.addWidget(labelNombre)
        self.add_spacer(self.nomHbox1)
        #
        self.nomHbox2 = QHBoxLayout()
        self.nomHbox2.setAlignment(Qt.AlignCenter)

        self.lineNom = QLineEdit()
        self.lineNom.setFixedWidth(self.screen_width(92))
        self.style_line_edit(self.lineNom, 4.7)
        self.lineNom.setReadOnly(True)
        self.lineNom.textChanged.connect(self.capitalize_words)

        self.nomHbox2.addWidget(self.lineNom)
        #
        kboardWidget = QWidget()
        kboardLayout = QVBoxLayout(kboardWidget)
        kboardWidget.setLayout(kboardLayout)
        kboardWidget.setStyleSheet("""
            QWidget {
                background-color: #3E7B27;
                border-radius: 20px;
                border: 2px solid white;
            }
        """)

        keyboardRows = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'Ñ'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M', 'Borrar'],
            ['⎵']
        ]

        for row in keyboardRows:
            hbox = QHBoxLayout()
            hbox.setAlignment(Qt.AlignCenter)
            #hbox.setSpacing(0)
            for key in row:
                kboardButton = QPushButton(key)
                if kboardButton.text()=="Borrar":
                    self.style_button(kboardButton, 3, 15, 2, "delete.png", 5, True)
                    kboardButton.setFixedSize(self.screen_width(15), cedReturn.height())
                elif kboardButton.text()=="⎵":
                    self.style_button(kboardButton, 5, 15, 2)
                    kboardButton.setFixedSize(self.screen_width(40), cedReturn.height())
                else:
                    kboardButton.setFixedWidth(self.screen_width(9.3))
                    self.style_button(kboardButton, 5, 15, 2)
                kboardButton.clicked.connect(self.kboard_pressed)
                hbox.addWidget(kboardButton)
            kboardLayout.addLayout(hbox)
        #
        self.nomHbox3 = QHBoxLayout()
        
        nomReturn = QPushButton(" Volver")
        nomReturn.setFixedSize(self.screen_width(15), self.screen_height(11))
        self.style_button(nomReturn, 3, 15, 2, "return.png",4)
        nomReturn.clicked.connect(self.nom_return)

        nomLimpiar = QPushButton("Limpiar")
        nomLimpiar.setFixedSize(self.screen_width(17), self.screen_height(11))
        self.style_button(nomLimpiar, 3, 15, 2, "clear.png", 5, True)
        nomLimpiar.clicked.connect(self.kboard_pressed)

        nomOk = QPushButton(" Confirmar")
        nomOk.setFixedSize(self.screen_width(20), self.screen_height(11))
        self.style_button(nomOk, 3, 15, 2, "ok.png", 3.5)

        self.nomHbox3.addWidget(nomReturn)
        self.add_spacer(self.nomHbox3)
        self.nomHbox3.addWidget(nomLimpiar)
        self.nomHbox3.addWidget(nomOk)
        self.add_spacer(self.nomHbox3)
        self.add_spacer(self.nomHbox3, nomReturn.width())
        #
        self.layoutNom.addLayout(self.nomHbox1)
        self.layoutNom.addLayout(self.nomHbox2)
        self.layoutNom.addWidget(kboardWidget)
        self.layoutNom.addLayout(self.nomHbox3)

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
        self.stackedWidget.addWidget(self.ced)
        self.stackedWidget.addWidget(self.nom)
        self.stackedWidget.addWidget(self.serv)

        self.init_db()
        self.showFullScreen()

    # Called when a button from the keypad is pressed
    def kpad_pressed(self):
        button = self.sender()
        if button.text() == "Borrar":
            self.lineID.setText(self.lineID.text()[:-1])
        else:
            current_number = self.lineID.text()
            new_number = current_number + button.text()
            self.lineID.setText(new_number)
    
    def confirm_ced(self):
        if self.isAsc:
            self.stackedWidget.setCurrentIndex(3)
        else: self.stackedWidget.setCurrentIndex(2)
    
    # Called when a button from the keyboard is pressed
    def kboard_pressed(self):
        button = self.sender()
        current_text = self.lineNom.text()
        if button.text() == "Borrar":
            self.lineNom.setText(self.lineNom.text()[:-1])
        elif button.text() == "Limpiar":
            self.lineNom.setText("")
            print("limpiar")
        elif button.text() == "⎵":
            if current_text != "" and current_text[-1] != " ":
                new_text = current_text + " "
                self.lineNom.setText(new_text)
        else:
            lowCased = chr(ord(button.text())+32)
            new_text = current_text + lowCased
            self.lineNom.setText(new_text)
    
    # Used to capitalize the first letter of each word
    def capitalize_words(self):
        text = self.lineNom.text()
        if len(text) > 0:
            # Split the text into words
            words = text.split(' ')
            # Capitalize the first letter of each word
            capitalized_words = [word.capitalize() for word in words]
            # Join the words back into a single string
            capitalized_text = ' '.join(capitalized_words)
            # Block signals to prevent recursive calls
            self.lineNom.blockSignals(True)
            # Set the capitalized text
            self.lineNom.setText(capitalized_text)
            # Unblock signals
            self.lineNom.blockSignals(False)

    def ced_return(self):
        self.stackedWidget.setCurrentIndex(0)
        self.lineID.setText("")
    
    def nom_return(self):
        self.stackedWidget.setCurrentIndex(1)
        self.lineNom.setText("")

    def go_to_ced(self):
        if self.sender().text() == "Sí":
            self.isAsc = True
        else: self.isAsc = False
        self.stackedWidget.setCurrentIndex(1)

    def go_to_nom(self):
        self.stackedWidget.setCurrentIndex(2)
    
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
    def style_button(self, button, fontSize, radius, border, img=None, imgSize=None, red=False):
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
        if red:
            styleSheet += """
            QPushButton {
                background: qlineargradient(
                    x1:0.5, y1:0, x2:0.5, y2:1,
                    stop:0 #CD5120, stop:1 #722506
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0.5, y1:0, x2:0.5, y2:1,
                    stop:0 #FF7038, stop:1 #CD5120
                )
            }
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

    def add_spacer(self, layout, width=None, height=None):
        label = QLabel()
        if width:
            label.setFixedWidth(width)
        if height:
            label.setFixedHeight(height)
        layout.addWidget(label)

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