import sys, socket, sqlite3, time, traceback, io, pika, time, json, threading
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

db_path = "digiturno.db"

class MainWindow(QMainWindow):
    commandSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.screenGeometry = QApplication.primaryScreen().geometry()
        self.host = '192.168.0.54'
        self.port = 47529
        self.current_user = None
        self.init_db()
        self.init_ui()
        self.modedRows = set()
        self.setup_rabbitmq()
        self.commandSignal.connect(self.handle_command)
        self.request_users_list()

    def init_ui(self):
        self.setWindowTitle("Control Digiturno")
        self.setGeometry(int(self.screenGeometry.width()/2 - 569),
                         int(self.screenGeometry.height()/2 - 300), 1138, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.set_background_color(central_widget, "#EFE3C2")
        
        mainLayout = QVBoxLayout(central_widget)
        self.stackedWidget = QStackedWidget()
        mainLayout.addWidget(self.stackedWidget)

####### Layout 0: VISTA PRINCIPAL #######
        
        widget0 = QWidget()
        layout0 = QVBoxLayout(widget0)
        widget0.setLayout(layout0)
        #layout0.setAlignment(Qt.AlignTop)
        #
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)

        self.tableStaff = QTableWidget()
        self.tableStaff.setColumnCount(8)
        self.tableStaff.setColumnHidden(0, True)
        self.tableStaff.setHorizontalHeaderLabels(["ID", "Nombre", "Cédula", "Usuario",
            "Contraseña", "Rol", "Estado", "Seleccionar"])
        #self.tableStaff.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableStaff.cellChanged.connect(self.on_cell_change)
        
        scrollArea.setWidget(self.tableStaff)
        #
        hBox0 = QHBoxLayout()
        
        self.buttonCrear = QPushButton('Crear')
        self.buttonRevertir = QPushButton('Revertir')
        self.buttonAplicar = QPushButton('Aplicar')
        self.buttonEliminar = QPushButton('Eliminar')
        self.buttonDeselect = QPushButton('Deselect')
        
        self.buttonRevertir.setEnabled(False)
        self.buttonAplicar.setEnabled(False)
        self.buttonEliminar.setEnabled(False)
        self.buttonDeselect.setEnabled(False)
        
        self.buttonCrear.clicked.connect(self.crear_pressed)
        self.buttonRevertir.clicked.connect(self.revertir_pressed)
        self.buttonAplicar.clicked.connect(self.aplicar_pressed)
        self.buttonEliminar.clicked.connect(self.eliminar_pressed)
        self.buttonDeselect.clicked.connect(self.deselect_pressed)
        
        hBox0.addWidget(self.buttonCrear)
        hBox0.addWidget(self.buttonRevertir)
        hBox0.addWidget(self.buttonAplicar)
        hBox0.addWidget(self.buttonEliminar)
        hBox0.addWidget(self.buttonDeselect)
        #
        layout0.addWidget(scrollArea)
        layout0.addLayout(hBox0)

####### Layout 1: VISTA MODIFICACIÓN #######
        
####### Stack widgets #######
        self.stackedWidget.addWidget(widget0)

    def init_db(self):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Add default admin if not exists
        cursor.execute('''
            INSERT OR IGNORE INTO funcionarios (nombre, identificacion, usuario, contrasena, rol)
            VALUES ('nombreAdmin', 'CC1094044402', 'admin', 'pass', 1)
        ''')
        conn.commit()
        conn.close()
        
    def load_users(self):
        self.tableStaff.blockSignals(True)
        self.tableStaff.setRowCount(len(self.users))
        self.buttonGroup = QButtonGroup()
        self.buttonGroup.setExclusive(False)
        self.buttonGroup.buttonToggled.connect(self.on_button_toggle)
        roles = ['Funcionario', 'Admin']
        estados = ['Bloqueado', 'Activo']
        for row, user in enumerate(self.users):
            for col, data in enumerate(user):
                if col > 4:
                    comBox = QComboBox()
                    comBox.addItems(roles if col==5 else estados)
                    self.tableStaff.setCellWidget(row, col, comBox)
                    comBox.setCurrentIndex(1 if data == 1 else 0)
                    comBox.currentIndexChanged.connect(lambda idx, r=row: self.on_comboBox_change(r))
                else:
                    self.tableStaff.setItem(row, col, QTableWidgetItem(str(data)))
                    self.tableStaff.item(row, col).setTextAlignment(Qt.AlignCenter)
            boton = QRadioButton()
            bw = QWidget()
            QHBoxLayout(bw).addWidget(boton)
            bw.layout().setContentsMargins(0,0,0,0)
            bw.layout().setAlignment(Qt.AlignCenter)
            self.buttonGroup.addButton(boton, int(self.users[row][0])) # Assign button ID based on user ID
            self.tableStaff.setCellWidget(row, 7, bw)
        self.tableStaff.blockSignals(False)
    
    def update_local_list(self):
        for changed_row in self.usersChanged:
            changed_id = str(changed_row[0])
            for i, user_row in enumerate(self.users):
                if str(user_row[0]) == changed_id:
                    self.users[i] = changed_row
                    break
    
    def clear_users(self, ids):
        ids = json.loads(ids)
        self.users = [user for user in self.users if user[0] not in ids]
        for row in reversed(range(self.tableStaff.rowCount())):
            item = self.tableStaff.item(row, 0)
            if item and item.text() in str(ids):
                self.tableStaff.removeRow(row)
        QMessageBox.warning(self, "", "Usuarios eliminados")
        
    def on_cell_change(self, row:int, col:int):
        "Called when one of the table's cells is modified, excuding radio buttons"
        self.modedRows.add(row)
        self.buttonRevertir.setEnabled(True)
        self.buttonAplicar.setEnabled(True)
    
    def on_comboBox_change(self, row):
        self.modedRows.add(row)
        self.buttonRevertir.setEnabled(True)
        self.buttonAplicar.setEnabled(True)
    
    def on_button_toggle(self, btn, checked): # If btn and checked are never used, replace them with *args
        "Called when one of the table's radio buttons is toggled"
        anyChecked = any(b.isChecked() for b in self.buttonGroup.buttons())
        self.buttonEliminar.setEnabled(anyChecked)
        self.buttonDeselect.setEnabled(anyChecked)
        
    def crear_pressed(self):
        pass
    
    def revertir_pressed(self):
        self.load_users()
        self.buttonRevertir.setEnabled(False)
        self.buttonAplicar.setEnabled(False)
    
    def aplicar_pressed(self):
        self.usersChanged = []
        for row in self.modedRows:
            rowData = []
            for col in range(self.tableStaff.columnCount()-1):
                if col == 5:
                    widget = self.tableStaff.cellWidget(row, col)
                    rowData.append(1 if widget.currentText()=='Admin' else 0)
                elif col == 6:
                    widget = self.tableStaff.cellWidget(row, col)
                    rowData.append(1 if widget.currentText()=='Activo' else 0)
                else:
                    item = self.tableStaff.item(row, col)
                    rowData.append(item.text() if item else "")
            self.usersChanged.append(rowData)
        print(self.usersChanged)
        self.update_users_list()
        self.buttonRevertir.setEnabled(False)
        self.buttonAplicar.setEnabled(False)
    
    def eliminar_pressed(self):
        checked_ids = [self.buttonGroup.id(b) for b in self.buttonGroup.buttons() if b.isChecked()]
        self.request_delete_users(checked_ids)
    
    def deselect_pressed(self):
        for btn in self.buttonGroup.buttons():
            btn.setChecked(False)

    def show_login(self):
        self.dialog = LoginDialog(self)
        if self.dialog.exec_() == QDialog.Accepted:
            self.current_user = self.dialog.userID
        elif not self.current_user: self.close()
        
    def log_out(self):
        self.close()
        self.current_user = None
        self.show_login()
        if self.current_user:
            self.show()

    def set_background_color(self, widget, color):
        palette = widget.palette()
        palette.setColor(QPalette.Background, QColor(color))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)
    
    def setup_rabbitmq(self):
        parameters = pika.ConnectionParameters(host='localhost')
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        self.channel.exchange_declare(
            exchange='digiturno_direct',
            exchange_type='direct',
            durable=True)
        
        self.channel.queue_declare(queue='ack_queue_admin', durable=True)
        self.channel.queue_bind(
            exchange='ack_exchange',
            queue='ack_queue_admin',
            routing_key='admin')
        
        self.channel.basic_consume(
            queue='ack_queue_admin',
            on_message_callback=self.handle_message,
            auto_ack=True)

        self.rabbitmq_thread = threading.Thread(
            target=self.start_consumer,
            daemon=True)
        self.rabbitmq_thread.start()
        
    def start_consumer(self):
        self.channel.start_consuming()

    def handle_message(self, channel, method, properties, body):
        try:
            message = body.decode('utf-8')
            self.commandSignal.emit(message)
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def handle_command(self, command):
        print(f"Handling command:\n{command}\n")
        if command.startswith('ACK_LOGIN_REQUEST:'):
            _, funID, isAdm = command.split(':')
            self.dialog.verify_credentials(funID, isAdm)
        elif command.startswith('ACK_FUNCIONARIOS_LIST_UPDATE:'):
            _, check = command.split(':')
            if check == 'good':
                self.update_local_list()
                QMessageBox.warning(self, "", "Cambios guardados")
            else:
                self.load_users()
                QMessageBox.warning(self, "Error", "No se pudieron guardar los cambios")
        elif command.startswith('ACK_DELETE_FUNCIONARIOS:'):
            _, ids = command.split(':')
            self.clear_users(ids)
        else:
            self.users = json.loads(command)
            self.load_users()
    
    def request_verification(self, username, password):
        try:
            self.channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=f'ADMIN_LOGIN_REQUEST:{username}:{password}',
                properties=pika.BasicProperties(delivery_mode=2))
        except:
            traceback.print_exc()

    def request_users_list(self):
        try:
            self.channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=f'FUNCIONARIOS_LIST_REQUEST',
                properties=pika.BasicProperties(delivery_mode=2))
        except: traceback.print_exc()
    
    def update_users_list(self):
        try:
            self.channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=f'FUNCIONARIOS_LIST_UPDATE:{json.dumps(self.usersChanged)}',
                properties=pika.BasicProperties(delivery_mode=2))
        except: traceback.print_exc()
    
    def request_delete_users(self, ids):
        try:
            self.channel.basic_publish(
                exchange='digiturno_direct',
                routing_key='server_command',
                body=f'DELETE_FUNCIONARIOS:{json.dumps(ids)}',
                properties=pika.BasicProperties(delivery_mode=2))
        except: traceback.print_exc()

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.screenGeometry = QApplication.primaryScreen().geometry()
        self.setWindowTitle("Iniciar sesión")
        self.setStyleSheet("background-color: #EFE3C2;")
        self.setGeometry(int(self.screenGeometry.width()/2 - 200),
                         int(self.screenGeometry.height()/2 - 100), 400, 200)
        self.layout = QVBoxLayout()
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("Usuario")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Contraseña")
        self.password.setEchoMode(QLineEdit.Password)
        
        self.loginButton = QPushButton("Iniciar sesión")
        self.loginButton.clicked.connect(self.request_verification_dialog)
        
        self.layout.addWidget(self.username)
        self.layout.addWidget(self.password)
        self.layout.addWidget(self.loginButton)
        self.setLayout(self.layout)
        
    def request_verification_dialog(self):
        if self.username.text() != "" and self.password.text() != "":
            client.request_verification(self.username.text(), self.password.text())
        else:
            QMessageBox.warning(self, "Error", "Llene ambos campos.")

    def verify_credentials(self, funID, isAdmin):
        if funID != 'NOT_FOUND':
            if funID != 'NO_ACCESS':
                if isAdmin == '1':
                    self.userID = funID
                    self.accept()
                else: QMessageBox.warning(self, "Error", "El usuario ingresado no es admin")
            else: QMessageBox.warning(self, "Error", "Usuario bloqueado")
        else: QMessageBox.warning(self, "Error", "Credenciales inválidas")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = MainWindow()
    client.show_login()
    if client.current_user:
        client.show()
    sys.exit(app.exec_())