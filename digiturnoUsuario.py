import sys, traceback, pika, threading, json, os, logging, time
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
load_dotenv()
handler = RotatingFileHandler('digiturnoUsuario.log', maxBytes=500000, backupCount=3)
logging.basicConfig(
    filename='digiturnoUsuario.log',
    level=logging.ERROR,
    format='%(asctime)s [%(levelname)s] %(message)s')

class MainWindow(QMainWindow):
    commandSignal = pyqtSignal(str)

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

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.go_to_ent)
        self.db_path = "digiturno.db"
        self.nombre = ""
        self.cedula = ""
        self.asociado = False
        self.queue = {'AS': [], 'CA': [], 'CO': [], 'CT': []}

####### Layout 0: CÉDULA #######
        self.ced = QWidget()
        self.layoutCed = QVBoxLayout(self.ced)
        self.layoutCed.setAlignment(Qt.AlignTop)
        #
        self.cedHbox1 = QHBoxLayout()
        self.cedHbox1.setContentsMargins(0, 0, 0, self.screen_height(1))

        labelCedula = QLabel("Bienvenido a Coohem<Br>Ingrese su cédula")
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
        self.style_button(self.turno, 12, 15, 3)
        self.turno.setFixedSize(self.screen_width(40), self.screen_height(30))

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
        self.setup_rabbitmq()
        self.commandSignal.connect(self.handle_command)
        self.request_queue()

    def kpad_pressed(self):
        """Called when a button from the keypad (numbers) is clicked"""
        button = self.sender()
        if button.text() == "Borrar":
            self.lineID.setText(self.lineID.text()[:-1])
        else:
            current_number = self.lineID.text()
            new_number = current_number + button.text()
            self.lineID.setText(new_number)
    
    def kboard_pressed(self):
        """Called when a button from the keyboard (letters) is clicked"""
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
    
    def capitalize_words(self):
        """Capitalize the first letter of each word"""
        text = self.lineNom.text()
        if len(text) > 0:
            words = text.split(' ')
            capitalized_words = [word.capitalize() for word in words]
            capitalized_text = ' '.join(capitalized_words)
            self.lineNom.blockSignals(True)
            self.lineNom.setText(capitalized_text)
            self.lineNom.blockSignals(False)

    def ced_confirm(self):
        """Called when confirm button in CÉDULA layout is clicked"""
        self.cedula = self.lineID.text().strip()
        if self.cedula:
            self.request_ID_check(self.cedula)
        else:
            pass # No number input
        self.lineID.setText("")
    
    def nom_confirm(self):
        """Called when confirm button in NOMBRE layout is clicked"""
        self.nombre = self.lineNom.text().strip()
        if self.nombre:
            self.send_customer_name(self.nombre)
        else:
            pass # No name input
        self.lineNom.setText("")
    
    def nom_return(self):
        """Called when return button in NOMBRE layout is clicked"""
        self.stackedWidget.setCurrentIndex(self.prevIndex)
        self.lineNom.setText("")
    
    def serv_return(self):
        """Called when return button from SERVICIO layout is clicked"""
        self.stackedWidget.setCurrentIndex(self.prevIndex)
        self.prevIndex = 0 if self.prevIndex == 1 else self.prevIndex

    def go_to_ent(self):
        """Go to first layout (CÉDULA)"""
        self.timer.stop()
        self.stackedWidget.setCurrentIndex(0)
        self.prevIndex = 0

    def go_to_turn(self):
        """Go to layout TURNO and send new turn command to server"""
        servicioTxt = self.sender().text()
        match servicioTxt:
            case 'Asesoría':
                servicio = 'AS'
                turnNumber = self.queue[servicio][-1]+1
                self.queue[servicio].append(turnNumber)
                self.turno.setText(f"{servicio}-{turnNumber}")
            case 'Caja':
                servicio = 'CA'
                turnNumber = self.queue[servicio][-1] + 1
                self.queue[servicio].append(turnNumber)
                self.turno.setText(f"{servicio}-{turnNumber}")
            case 'Cobranza':
                servicio = 'CO'
                turnNumber = self.queue[servicio][-1] + 1
                self.queue[servicio].append(turnNumber)
                self.turno.setText(f"{servicio}-{turnNumber}")
            case 'Cartera':
                servicio = 'CT'
                turnNumber = self.queue[servicio][-1] + 1
                self.queue[servicio].append(turnNumber)
                self.turno.setText(f"{servicio}-{turnNumber}")
        self.send_new_turn(servicio)
        self.stackedWidget.setCurrentIndex(3)
        self.prevIndex = 2
        self.timer.start(8000)
    
    def style_label(self, label, fontSize):
        """Set stylesheet for a label. Parameters:
        label (QLabel): Label to set stylesheet
        fontSize (int): Based on screen width %"""
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

    def style_button(self, button, fontSize, radius, border, img=None, imgSize=None, red=False):
        """Set stylesheet for a button. Parameters:
        button (QPushButton): Button to set stylesheet
        fontSize (int): Based on screen width %
        radius (int): Pixel value of border radius
        border (int): Pixel value of border girth
        img (Str): Path to img
        imgSize (int): Based on screen width %
        red (bool): Uses different background color
        """
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

    def style_line_edit(self, label, fontSize):
        """Set stylesheet for a line edit. Parameters:
        label (QLineEdit): Line edit to set stylesheet
        fontSize (int): Based on screen width %"""
        label.setStyleSheet(f"""
            QLineEdit {{
                color: #204114;
                border-radius:10px;
                font-size: {self.screen_width(fontSize)}px;
            }}
        """)
        label.setAlignment(Qt.AlignCenter)

    def add_spacer(self, layout, width=None, height=None):
        """Add QLabel to layout. Parameters:
        layout (QLayout): Any type of pyqt layout
        width (int): Pixel value of label width
        height (int): Pixel value of label height
        """
        label = QLabel()
        if width:
            label.setFixedWidth(width)
        if height:
            label.setFixedHeight(height)
        layout.addWidget(label)

    def add_logo(self, layout):
        """Add QLabel with logo img to layout"""
        label = QLabel()
        label.setAlignment(Qt.AlignTop)
        pixmap = QPixmap("logoCoohem.png")
        label.setPixmap(pixmap)
        shadow = QGraphicsDropShadowEffect(label, blurRadius=20)
        shadow.setOffset(5, 5)
        label.setGraphicsEffect(shadow)
        layout.addWidget(label)

    def set_background_color(self, widget, color):
        """Used on a widget to set background color"""
        palette = widget.palette()
        palette.setColor(QPalette.Background, QColor(color))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)

    def set_background_image(self, widget):
        """Used on a widget to set a background picture"""
        pixmap = QPixmap("logoCoohem.png")
        if not pixmap.isNull():
            palette = widget.palette()
            brush = QBrush(pixmap)
            palette.setBrush(QPalette.Window, brush)
            widget.setAutoFillBackground(True)
            widget.setPalette(palette)
    
    def screen_width(self, num):
        "Returns pixel value of screen width % based on parameter"
        return int(self.screenGeometry.width()*num/100)
    def screen_height(self, num):
        "Returns pixel value of screen height % based on parameter"
        return int(self.screenGeometry.height()*num/100)
    
    def setup_rabbitmq(self):
        """Setup connection to RabbitMQ server"""
        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER"),
            os.getenv("RABBITMQ_PASS"))
        parameters = pika.ConnectionParameters(
            host=os.getenv('LOCAL_IP'),
            port=int(os.getenv('PORT')),
            credentials=credentials)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        self.channel.exchange_declare(
            exchange='digiturno_direct',
            exchange_type='direct',
            durable=True)
        
        self.channel.queue_declare(queue='ack_queue_user', durable=True)
        self.channel.queue_bind(
            exchange='ack_exchange',
            queue='ack_queue_user',
            routing_key='user')
        
        self.channel.basic_consume(
            queue='ack_queue_user',
            on_message_callback=self.handle_msg,
            auto_ack=True)

        self.rabbitmq_thread = threading.Thread(
            target=self.start_consumer,
            daemon=True)
        self.rabbitmq_thread.start()
        
    def start_consumer(self):
        self.channel.start_consuming()
    
    def handle_msg(self, channel, method, properties, body):
        """Handle incoming messages through RabbitMQ"""
        try:
            message = body.decode('utf-8')
            self.commandSignal.emit(message)
        except:
            logging.exception('Exception handling message')
            traceback.print_exc()
    
    def handle_command(self, command):
        """Process incoming commands recieved via signal"""
        if command.startswith('ACK_CUSTOMER_ID_CHECK:'):
            _, reg, nom, asc = command.split(':')
            if reg == '1':
                self.nombre = nom
                self.asociado = asc == '1'
                self.stackedWidget.setCurrentIndex(2) # Sends to layout 2 (SERVICIO)
            else:
                self.stackedWidget.setCurrentIndex(1) # Sends to layout 1 (NOMBRE)
            self.prevIndex = 0
        elif command.startswith('ACK_NEW_CUSTOMER:'):
            _, ced, nom = command.split(':')
            self.nombre = nom
            self.stackedWidget.setCurrentIndex(2) # Sends to layout 2 (SERVICIO)
            self.prevIndex = 1
        else:
            listQueue = json.loads(command)
            self.queue = {'AS': [], 'CA': [], 'CO': [], 'CT': []}
            for serv, num in listQueue:
                if serv not in self.queue:
                    self.queue[serv] = []
                self.queue[serv].append(num)
            for serv in self.queue:
                if not self.queue[serv]:  # Checks if list is empty
                    self.queue[serv].append(0)
            print(f"Got queue:\n{self.queue}")

    def send_new_turn(self, servicio):
        try:
            self.channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=f'NEW_TURN:{self.cedula}:{servicio}',
                properties=pika.BasicProperties(delivery_mode=2))
        except:
            logging.exception('Exception sending new turn')
            traceback.print_exc()
    
    def request_queue(self):
        try:
            self.channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body='LAST_TURN_PER_SERVICE',
                properties=pika.BasicProperties(delivery_mode=2))
        except:
            logging.exception('Exception requesting queue')
            traceback.print_exc()
    
    def request_ID_check(self, cedula):
        try:
            self.channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=f'CUSTOMER_ID_CHECK:{cedula}',
                properties=pika.BasicProperties(delivery_mode=2))
        except:
            logging.exception('Exception requesting ID check')
            traceback.print_exc()
    
    def send_customer_name(self, nombre):
        try:
            self.channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=f'NEW_CUSTOMER:{self.cedula}:{nombre}',
                properties=pika.BasicProperties(delivery_mode=2))
        except:
            logging.exception('Exception sending new customer')
            traceback.print_exc()

    def closeEvent(self, event):
        """Clean up on window close"""
        try: self.channel.stop_consuming()
        except: pass
        try: self.rabbitmq_thread.join()
        except: pass
        super().closeEvent(event)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())