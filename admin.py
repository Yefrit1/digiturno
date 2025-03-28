import sys, socket, sqlite3, time, traceback, io
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

db_path = "digiturno.db"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.screenGeometry = QApplication.primaryScreen().geometry()
        self.host = '192.168.0.54'
        self.port = 47529
        self.current_user = None
        self.init_db()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Control Digiturno")
        self.setGeometry(int(self.screenGeometry.width()/2 - 568),
                         int(self.screenGeometry.height()/2 - 300), 1136, 600)
        
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
        vBox01 = QVBoxLayout()

        self.tableStaff = QTableWidget()
        self.tableStaff.setColumnCount(7)
        self.tableStaff.setHorizontalHeaderLabels(["Nombre", "Cédula", "Usuario",
                                                   "Contraseña", "Rol", "Estado", "Seleccionar"])
        self.tableStaff.setEditTriggers(QTableWidget.NoEditTriggers)
        self.load_users()

        vBox01.addWidget(self.tableStaff)
        layout0.addLayout(vBox01)

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
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nombre, identificacion, usuario, contrasena, rol, estado FROM funcionarios")
                users = cursor.fetchall()

            self.tableStaff.setRowCount(len(users))
            for row, user in enumerate(users):
                for col, data in enumerate(user):
                    self.tableStaff.setItem(row, col, QTableWidgetItem(str(data)))
                self.tableStaff.setItem(row, 6, QTableWidgetItem(str("X")))
            conn.close()
        except Exception as e:
            str_io = io.StringIO()
            traceback.print_exc(file=str_io)
            error_str = str_io.getvalue()
            QMessageBox.warning(None, "Error loading users", error_str)

    def show_login(self):
        dialog = LoginDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.current_user = dialog.user_id
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
        self.loginButton.clicked.connect(self.verify_credentials)
        
        self.layout.addWidget(self.username)
        self.layout.addWidget(self.password)
        self.layout.addWidget(self.loginButton)
        self.setLayout(self.layout)

    def verify_credentials(self):
        conn = sqlite3.connect('digiturno.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, rol FROM funcionarios 
            WHERE usuario = ? AND contrasena = ?
        ''', (self.username.text(), self.password.text()))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[1]:
            self.user_id = result[0]
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Credenciales inválidas/usuario no admin")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = MainWindow()
    client.show_login()
    if client.current_user:
        client.show()
    sys.exit(app.exec_())