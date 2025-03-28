import sys, socket, sqlite3, time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

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
        conn = sqlite3.connect('digiturno.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, is_admin FROM funcionarios 
            WHERE usuario = ? AND contrasena = ?
        ''', (self.username.text(), self.password.text()))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[1]:
            self.user_id = result[0]
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Credenciales inválidas/usuario no admin")

class StaffClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.host = '192.168.0.54'
        self.port = 47529
        self.current_user = None
        self.init_db()
        self.init_ui()

    def init_db(self):
        conn = sqlite3.connect('digiturno.db')
        cursor = conn.cursor()
        # Add default admin if not exists
        cursor.execute('''
            INSERT OR IGNORE INTO funcionarios (nombre, identificacion, usuario, contrasena, is_admin)
            VALUES ('nombreAdmin', 'CC1094044402', 'admin', 'pass', 1)
        ''')
        conn.commit()
        conn.close()

    def init_ui(self):
        self.setWindowTitle("Control Digiturno")
        #self.setStyleSheet("background-color: #3D5E31;")
        self.setGeometry(600, 300, 500, 400)

    def show_login(self):
        dialog = LoginDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.current_user = dialog.user_id
            #self.station_label.setText(f"Estación: {self.current_user['estacion_id']}")
        elif not self.current_user: self.close()
        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = StaffClient()
    client.show_login()
    if client.current_user:
        client.show()
    sys.exit(app.exec_())