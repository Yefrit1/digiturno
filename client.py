import sys
import socket
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sqlite3

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Iniciar sesión")
        #self.setStyleSheet("background-color: #3D5E31;")
        self.setGeometry(600, 300, 400, 200)
        self.layout = QVBoxLayout()
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("Usuario")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Contraseña")
        self.password.setEchoMode(QLineEdit.Password)
        
        self.loginButton = QPushButton("Iniciar sesión")
        self.loginButton.clicked.connect(self.verify_credentials)
        
        self.layout.addWidget(self.username)
        self.layout.addWidget(self.password)
        self.layout.addWidget(self.loginButton)
        self.setLayout(self.layout)

    def verify_credentials(self):
        conn = sqlite3.connect('client_users.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT estacion_id, is_admin FROM usuarios 
            WHERE nombre = ? AND contrasena = ?
        ''', (self.username.text(), self.password.text()))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            self.user_info = {
                'estacion_id': result[0],
                'is_admin': bool(result[1])
            }
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Credenciales inválidas")

class UserManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de usuarios")
        self.setGeometry(610, 310, 900, 400)
        self.setup_ui()

    def setup_ui(self):
        # Users table
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Usuario", "Contraseña", "Estación", "Admin"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.load_users()

        # Button group 1
        self.buttonBox = QHBoxLayout()
        self.addUserButton = QPushButton("Añadir usuario")
        self.modifyUsersButton = QPushButton("Modificar usuarios")
        self.removeUsersButton = QPushButton("Eliminar usuarios")
        self.addUserButton.clicked.connect(lambda: AddUserDialog(self).exec_())
        self.modifyUsersButton.clicked.connect(self.toggle_ui)
        self.removeUsersButton.clicked.connect(self.toggle_ui)
        self.buttonBox.addWidget(self.modifyUsersButton)
        self.buttonBox.addWidget(self.addUserButton)
        # Button group 2
        self.cancelButton = QPushButton("Cancelar")
        self.confirmButton = QPushButton("Confirmar")
        self.cancelButton.clicked.connect(self.toggle_ui)
        self.confirmButton.clicked.connect(self.confirm_changes)
        # Add layouts
        layout.addWidget(self.table)
        layout.addLayout(self.buttonBox)
        self.setLayout(layout)

    def load_users(self):
        conn = sqlite3.connect('client_users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, contrasena, estacion_id, is_admin FROM usuarios")
        users = cursor.fetchall()
        
        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            for col, data in enumerate(user):
                self.table.setItem(row, col, QTableWidgetItem(str(data)))
        conn.close()

    def confirm_changes(self):
        conn = sqlite3.connect('client_users.db')
        cursor = conn.cursor()
        for row in range(self.table.rowCount()):
            nombre = self.table.item(row, 0).text()
            contrasena = self.table.item(row, 1).text()
            estacion_id = self.table.item(row, 2).text()
            is_admin = self.table.item(row, 3).text()
            
            cursor.execute('''
                UPDATE usuarios
                SET contrasena = ?, estacion_id = ?, is_admin = ?
                WHERE nombre = ?
            ''', (contrasena, estacion_id, is_admin, nombre))
        
        conn.commit()
        conn.close()
        self.toggle_ui()

    # Swaps button groups in buttonBox, enables/disables table editing and loads table from DB
    def toggle_ui(self):
        if self.modifyUsersButton.isVisible():
            # Remove current buttons
            self.buttonBox.removeWidget(self.modifyUsersButton)
            self.buttonBox.removeWidget(self.addUserButton)
            self.buttonBox.removeWidget(self.removeUsersButton)
            self.modifyUsersButton.setParent(None)
            self.addUserButton.setParent(None)
            self.removeUsersButton.setParent(None)
            # Add other buttons
            self.buttonBox.addWidget(self.cancelButton)
            self.buttonBox.addWidget(self.confirmButton)
            # Enable table editing
            self.table.setEditTriggers(QTableWidget.AllEditTriggers)
        else:
            # Remove current buttons
            self.buttonBox.removeWidget(self.cancelButton)
            self.buttonBox.removeWidget(self.confirmButton)
            self.cancelButton.setParent(None)
            self.confirmButton.setParent(None)
            # Add other buttons
            self.buttonBox.addWidget(self.modifyUsersButton)
            self.buttonBox.addWidget(self.addUserButton)
            # Disable table editing
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
            self.load_users()


class AddUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir usuario")
        self.parent = parent
        self.setGeometry(620, 320, 500, 150)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout()
        self.unInput = QLineEdit("")
        self.passInput = QLineEdit("")
        self.stIdInput = QLineEdit("")
        self.isAdminRB1 = QRadioButton("Sí")
        self.isAdminRB2 = QRadioButton("No")
        self.isAdminRB2.setChecked(True)
        self.isAdminRBG = QButtonGroup()
        self.isAdminRBG.addButton(self.isAdminRB1)
        self.isAdminRBG.addButton(self.isAdminRB2)
        isAdminLayout = QHBoxLayout()
        isAdminLayout.addWidget(self.isAdminRB1)
        isAdminLayout.addWidget(self.isAdminRB2)
        saveButton = QPushButton("Agregar")
        saveButton.clicked.connect(self.add_user)

        layout.addRow("Nombre:", self.unInput)
        layout.addRow("Contraseña", self.passInput)
        layout.addRow("Estación ID:", self.stIdInput)
        layout.addRow("Admin:", isAdminLayout)
        layout.addRow(saveButton)
        self.setLayout(layout)
    
    def add_user(self):
        conn = sqlite3.connect('client_users.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT estacion_id FROM usuarios
                       ''')
        if self.isAdminRB1.isChecked(): isAdminCheck = '1'
        else: isAdminCheck = '0'
        if not (self.unInput.text() and self.passInput.text() and self.stIdInput.text()):
            QMessageBox.warning(self, "Error", "Llene todos los campos")
            return
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO usuarios
                VALUES (?, ?, ?, ?)
                    ''', (self.unInput.text(), self.passInput.text(), self.stIdInput.text(), isAdminCheck))
            conn.commit()
            QMessageBox.warning(self, "", "Usuario registrado exitosamente")
            self.unInput.setText("")
            self.passInput.setText("")
            self.stIdInput.setText("")
            self.isAdminRB2.setChecked(True)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"{e}")
            conn.rollback()
        conn.close()

class ModifyUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modificar usuarios")
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout()

        self.setLayout(layout)

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()
        self.ipEdit = QLineEdit(self.parent.host)
        self.portEdit = QLineEdit(str(self.parent.port))
        
        saveButton = QPushButton("Guardar")
        saveButton.clicked.connect(self.save_config)
        
        layout.addRow("Servidor IP:", self.ipEdit)
        layout.addRow("Puerto:", self.portEdit)
        layout.addRow(saveButton)
        self.setLayout(layout)

    def save_config(self):
        self.parent.host = self.ipEdit.text()
        self.parent.port = int(self.portEdit.text())
        self.parent.save_config()
        self.accept()

class StaffClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.host = '192.168.0.54'
        self.port = 47529
        self.current_user = None
        self.init_db()
        self.init_ui()
        self.load_config()

    def init_db(self):
        conn = sqlite3.connect('client_users.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                nombre TEXT PRIMARY KEY,
                contrasena TEXT,
                estacion_id INTEGER,
                is_admin BOOLEAN
            )
        ''')
        # Add default admin if not exists
        cursor.execute('''
            INSERT OR IGNORE INTO usuarios VALUES 
            ('admin', 'admin', 0, 1)
        ''')
        conn.commit()
        conn.close()

    def init_ui(self):
        self.setWindowTitle("Control Digiturno")
        #self.setStyleSheet("background-color: #3D5E31;")
        self.setGeometry(600, 300, 500, 400)
        
        # Create menu bar
        self.menu_bar = QMenuBar()
        self.session_menu = QMenu("Sesión", self)
        self.login_action = QAction("Iniciar sesión", self)
        self.change_user_action = QAction("Cambiar usuario", self)
        self.logout_action = QAction("Cerrar sesión", self)
        
        self.config_menu = QMenu("Configuración", self)
        self.config_ip_action = QAction("Conexión", self)
        self.config_user_action = QAction("Modificar usuarios", self)
        
        # Setup menus
        self.session_menu.addAction(self.login_action)
        self.session_menu.addAction(self.change_user_action)
        self.session_menu.addAction(self.logout_action)
        self.config_menu.addAction(self.config_ip_action)
        self.config_menu.addAction(self.config_user_action)
        
        self.menu_bar.addMenu(self.session_menu)
        self.menu_bar.addMenu(self.config_menu)
        self.setMenuBar(self.menu_bar)
        
        # Connect actions
        self.login_action.triggered.connect(self.show_login)
        self.change_user_action.triggered.connect(self.show_login)
        self.logout_action.triggered.connect(self.logout)
        self.config_ip_action.triggered.connect(lambda: ConfigDialog(self).exec_())
        self.config_user_action.triggered.connect(lambda: UserManagerDialog(self).exec_())
        
        # Main widget
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)
        
        # Action UI components
        self.station_label = QLabel("Digiturno")
        self.station_label.setStyleSheet("color: #123524; font-size: 60px; font-weight: bold")
        self.layout.addWidget(self.station_label, alignment=Qt.AlignCenter)
        
        button_layout = QHBoxLayout()
        self.next_button = self.create_action_button("Siguiente", "s")
        self.cancel_button = self.create_action_button("Cancelar", "c")
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(button_layout)
        
        self.update_ui_state(False)

    def create_action_button(self, text, action):
        button = QPushButton(text)
        button.setFixedSize(120, 80)
        button.setStyleSheet("""
            QPushButton {
                background-color: #3E7B27;
                color: white;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;}
            QPushButton:hover {
                background-color: #85A947;
                color: white;}
        """)
        button.clicked.connect(lambda: self.send_command(action))
        return button

    def update_ui_state(self, logged_in):
        self.login_action.setVisible(not logged_in)
        self.change_user_action.setVisible(logged_in)
        self.logout_action.setVisible(logged_in)
        self.config_menu.setEnabled(logged_in and self.current_user and self.current_user.get('is_admin', False))
        self.next_button.setEnabled(logged_in)
        self.cancel_button.setEnabled(logged_in)

    def show_login(self):
        dialog = LoginDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.current_user = dialog.user_info
            #self.station_label.setText(f"Estación: {self.current_user['estacion_id']}")
            self.update_ui_state(True)
        elif not self.current_user: self.close()

    def logout(self):
        self.current_user = None
        self.station_label.clear()
        self.update_ui_state(False)

    def send_command(self, action):
        if not self.current_user or self.current_user['estacion_id'] == 0:
            return
        
        station = self.current_user['estacion_id']
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                if action == "s":
                    s.sendall(f"NEXT_{station}".encode('utf-8'))
                elif action == "c":
                    s.sendall(f"CANCEL_{station}".encode('utf-8'))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error de conexión: {str(e)}")

    def load_config(self):
        settings = QSettings("MyCompany", "Digiturno")
        self.host = settings.value("host", "192.168.0.54")
        self.port = int(settings.value("port", 47529))

    def save_config(self):
        settings = QSettings("MyCompany", "Digiturno")
        settings.setValue("host", self.host)
        settings.setValue("port", self.port)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = StaffClient()
    client.show_login()
    if client.current_user:
        client.show()
    sys.exit(app.exec_())