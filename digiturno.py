import sys, sqlite3, socket, traceback
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

        self.db_path = "digiturno.db"
        self.nombre = ""
        self.cedula = ""
        self.asociado = False
        self.queue = {'AS': [0], 'CA': [0], 'CO': [0], 'CT': [0]}
        self.host = '192.168.0.54'
        self.port = 47529

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT servicio, numero
                FROM turnos
                WHERE estado = 'pendiente' AND DATE(creado) = DATE('now')
                ORDER BY creado
            """)
        for servicio, numero in cursor.fetchall():
            self.queue[servicio].append(numero)

####### Layout 0: CÉDULA #######
        self.ced = QWidget()
        self.layoutCed = QVBoxLayout(self.ced)
        self.layoutCed.setAlignment(Qt.AlignTop)
        #
        self.cedHbox1 = QHBoxLayout()
        self.cedHbox1.setContentsMargins(0, 0, 0, self.screen_height(1))

        labelCedula = QLabel("Bienvenido<Br>Ingrese su cédula")
        self.style_label(labelCedula, 4)

        self.add_logo(self.cedHbox1)
        self.cedHbox1.addWidget(labelCedula)
        self.add_spacer(self.cedHbox1)
        #
        self.cedHbox2 = QHBoxLayout()
        self.cedHbox2.setAlignment(Qt.AlignCenter)

        self.lineID = QLineEdit()
        self.lineID.setFixedWidth(self.screen_width(60))
        self.style_line_edit(self.lineID, 7)
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

        cedDel = QPushButton("Borrar")
        cedDel.setFixedSize(self.screen_width(15), self.screen_height(12))
        self.style_button(cedDel, 3, 15, 2, "delete.png",5, True)
        cedDel.clicked.connect(self.kpad_pressed)

        nomOk = QPushButton("Confirmar")
        nomOk.setFixedSize(self.screen_width(15), self.screen_height(12))
        self.style_button(nomOk, 2.3, 15, 2, "ok.png", 3.5)
        nomOk.clicked.connect(self.ced_confirm)

        self.add_spacer(self.cedHbox4)
        self.cedHbox4.addWidget(cedDel)
        self.cedHbox4.addWidget(nomOk)
        self.add_spacer(self.cedHbox4)
        #
        self.layoutCed.addLayout(self.cedHbox1)
        self.layoutCed.addLayout(self.cedHbox2)
        self.layoutCed.addLayout(self.cedHbox3)
        self.layoutCed.addLayout(self.cedHbox4)
        
####### Layout 1: NOMBRE (no asociado) #######
        self.nom = QWidget()
        self.layoutNom = QVBoxLayout(self.nom)
        self.layoutNom.setAlignment(Qt.AlignTop)
        #
        self.nomHbox1 = QHBoxLayout()
        self.nomHbox1.setContentsMargins(0,0,0, self.screen_height(8))

        labelNombre = QLabel("Ingrese su nombre")
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
                    kboardButton.setFixedSize(self.screen_width(15), self.screen_height(12))
                elif kboardButton.text()=="⎵":
                    self.style_button(kboardButton, 5, 15, 2)
                    kboardButton.setFixedSize(self.screen_width(40), self.screen_height(12))
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
        nomOk.clicked.connect(self.nom_confirm)

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

####### Layout 2: SERVICIO #######
        self.serv = QWidget()
        self.layoutServ = QVBoxLayout(self.serv)
        self.layoutServ.setAlignment(Qt.AlignTop)
        #
        self.servHbox1 = QHBoxLayout()

        labelServicio = QLabel("Viene por:")
        self.style_label(labelServicio, 5)

        self.add_logo(self.servHbox1)
        self.servHbox1.addWidget(labelServicio)
        self.add_spacer(self.servHbox1)
        #
        self.servGrid = QGridLayout()
        self.servGrid.setContentsMargins(0, self.screen_height(20), 0, self.screen_height(10))
        self.servGrid.setHorizontalSpacing(self.screen_width(5))
        self.servGrid.setVerticalSpacing(self.screen_height(5))

        asesoria = QPushButton("Asesoría")
        caja = QPushButton("Caja")
        cobranza = QPushButton("Cobranza")
        cartera = QPushButton("Cartera")

        self.style_button(asesoria, 5, 15, 2)
        self.style_button(caja, 5, 15, 2)
        self.style_button(cobranza, 5, 15, 2)
        self.style_button(cartera, 5, 15, 2)

        asesoria.setFixedSize(self.screen_width(35), self.screen_height(15))
        caja.setFixedSize(self.screen_width(35), self.screen_height(15))
        cobranza.setFixedSize(self.screen_width(35), self.screen_height(15))
        cartera.setFixedSize(self.screen_width(35), self.screen_height(15))

        asesoria.clicked.connect(self.go_to_turn)
        caja.clicked.connect(self.go_to_turn)
        cobranza.clicked.connect(self.go_to_turn)
        cartera.clicked.connect(self.go_to_turn)

        self.servGrid.addWidget(asesoria, 0, 0)
        self.servGrid.addWidget(caja, 0, 1)
        self.servGrid.addWidget(cobranza, 1, 0)
        self.servGrid.addWidget(cartera, 1, 1)
        #
        self.servHbox2 = QHBoxLayout()

        servReturn = QPushButton(" Volver")
        servReturn.setFixedSize(self.screen_width(15), self.screen_height(11))
        self.style_button(servReturn, 3, 15, 2, "return.png",4)
        servReturn.clicked.connect(self.serv_return)

        self.servHbox2.addWidget(servReturn)
        self.add_spacer(self.servHbox2)
        #
        self.layoutServ.addLayout(self.servHbox1)
        self.layoutServ.addLayout(self.servGrid)
        self.layoutServ.addLayout(self.servHbox2)

####### Layout 3: TURNO #######
        self.turn = QWidget()
        self.layoutTurn = QVBoxLayout(self.turn)
        #
        turnHbox1 = QHBoxLayout()

        labelTurn = QLabel("Su turno es:")
        self.style_label(labelTurn, 7)

        self.add_logo(turnHbox1)
        turnHbox1.addWidget(labelTurn)
        self.add_spacer(turnHbox1)
        #
        turnHbox2 = QHBoxLayout()

        self.turno = QPushButton()
        self.style_button(self.turno, 10, 15, 3)

        self.add_spacer(turnHbox2)
        turnHbox2.addWidget(self.turno)
        self.add_spacer(turnHbox2)
        #
        turnHbox3 = QHBoxLayout()

        turnBack = QPushButton(" Salir")
        turnBack.setFixedSize(self.screen_width(14), self.screen_height(11))
        self.style_button(turnBack, 3, 15, 2, "exit.png",4)
        turnBack.clicked.connect(self.go_to_ent)

        turnHbox3.addWidget(turnBack)
        self.add_spacer(turnHbox3)
        #
        self.layoutTurn.addLayout(turnHbox1)
        self.add_spacer(self.layoutTurn)
        self.layoutTurn.addLayout(turnHbox2)
        self.add_spacer(self.layoutTurn)
        self.layoutTurn.addLayout(turnHbox3)

####### Stack layouts #######
        self.stackedWidget.addWidget(self.ced)
        self.stackedWidget.addWidget(self.nom)
        self.stackedWidget.addWidget(self.serv)
        self.stackedWidget.addWidget(self.turn)

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
            words = text.split(' ')
            capitalized_words = [word.capitalize() for word in words]
            capitalized_text = ' '.join(capitalized_words)
            self.lineNom.blockSignals(True)
            self.lineNom.setText(capitalized_text)
            self.lineNom.blockSignals(False)

    # Called when confirm button in CÉDULA layout is clicked
    def ced_confirm(self):
        self.cedula = self.lineID.text().strip()
        if self.cedula:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM clientes WHERE identificacion =  ?', (self.cedula,))
                customerInfo = cursor.fetchall()
            if customerInfo: # Sets self.asociado to True if the customer's ID exists in the DB and is asociado
                self.asociado = customerInfo[0][3] == 1
                self.stackedWidget.setCurrentIndex(2) # Sends to layout 2 (SERVICIO)
            else:
                self.stackedWidget.setCurrentIndex(1) # Sends to layout 1 (NOMBRE)
            self.prevIndex = 0
        else:
            pass # No number input
        self.lineID.setText("")
    
    # Called when confirm button in NOMBRE layout is clicked
    def nom_confirm(self):
        self.nombre = self.lineNom.text().strip()
        if self.nombre:
            try: # Insert new customer into DB
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO clientes (identificacion, nombre, asociado)
                        VALUES (?, ?, False)
                    ''', (self.cedula, self.nombre))
                    conn.commit()
            except Exception as e:
                traceback.print_exc()
                conn.rollback()
            self.stackedWidget.setCurrentIndex(2)
            self.prevIndex = 1
        else:
            pass # No name input
        self.lineNom.setText("")
    
    def nom_return(self):
        self.stackedWidget.setCurrentIndex(self.prevIndex)
        self.lineNom.setText("")
    
    # Button to return from SERVICIO layout
    def serv_return(self):
        self.stackedWidget.setCurrentIndex(self.prevIndex)
        self.prevIndex = 0 if self.prevIndex == 1 else self.prevIndex

    def go_to_ent(self):
        self.stackedWidget.setCurrentIndex(0)
        self.prevIndex = 0

    def go_to_turn(self):
        servicio = self.sender().text()
        match servicio:
            case 'Asesoría':
                turnNumber = self.queue['AS'][-1]+1
                self.queue['AS'].append(turnNumber)
                self.turno.setText(f"AS-{turnNumber}")
            case 'Caja':
                turnNumber = self.queue['CA'][-1] + 1
                self.queue['CA'].append(turnNumber)
                self.turno.setText(f"CA-{turnNumber}")
            case 'Cobranza':
                turnNumber = self.queue['CO'][-1] + 1
                self.queue['CO'].append(turnNumber)
                self.turno.setText(f"CO-{turnNumber}")
            case 'Cartera':
                turnNumber = self.queue['CT'][-1] + 1
                self.queue['CT'].append(turnNumber)
                self.turno.setText(f"CT-{turnNumber}")
        self.send_command(servicio)
        self.stackedWidget.setCurrentIndex(3)
        self.prevIndex = 2
    
    def send_command(self, servicio):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                match servicio:
                    case 'Asesoría': s.sendall(f"NEWTICKET_{self.cedula}_AS".encode('utf-8'))
                    case 'Caja': s.sendall(f"NEWTICKET_{self.cedula}_CA".encode('utf-8'))
                    case 'Cobranza': s.sendall(f"NEWTICKET_{self.cedula}_CO".encode('utf-8'))
                    case 'Cartera': s.sendall(f"NEWTICKET_{self.cedula}_CT".encode('utf-8'))
        except Exception as e:
            traceback.print_exc()
    
    # Sets stylesheet for a label
    def style_label(self, label, fontSize):
        label.setStyleSheet(f"""
            QLabel {{
                color: #284F1A;
                font-size: {self.screen_width(fontSize)}px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(label, blurRadius=20)
        shadow.setOffset(2, 2)
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
        shadow = QGraphicsDropShadowEffect(button, blurRadius=10)
        shadow.setOffset(2, 2)
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
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())