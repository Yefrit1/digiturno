import sys, socket, sqlite3, traceback
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.db_path = "digiturno.db"
        self.host = '192.168.0.54'
        self.port = 47529
        self.queue = {'AS': [], 'CA': [], 'CO': [], 'CT': []}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Funcionario COOHEM")
        self.setGeometry(10, 50, 900, 500)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.set_background_color(central_widget, '#EFE3C2')
        layoutMain = QVBoxLayout(central_widget)
        layoutMain.setAlignment(Qt.AlignTop)

        # Logo and title #
        hBox1 = QHBoxLayout()
        hBox1.setContentsMargins(10, 0, 10, 20)

        labelLogo = QLabel()
        labelLogo.setAlignment(Qt.AlignTop)
        pixmapLogo = QPixmap("logoCoohem.png")
        labelLogo.setPixmap(pixmapLogo)
        shadowLogo = QGraphicsDropShadowEffect(labelLogo, blurRadius=20)
        shadowLogo.setOffset(5, 5)
        labelLogo.setGraphicsEffect(shadowLogo)

        labelTitle = QLabel("Funcionario")
        self.style_label(labelTitle, 50, "#1D3C12")

        hBox1.addWidget(labelLogo)
        hBox1.addWidget(labelTitle)
        self.add_spacer(hBox1)

        # Headers #
        hBox2 = QHBoxLayout()
        hBox2.setContentsMargins(10, 0, 10, 0)

        labelAsesoria = QLabel("Asesoría")
        labelCaja = QLabel("Caja")
        labelCobranza = QLabel("Cobranza")
        labelCartera = QLabel("Cartera")

        self.style_label(labelAsesoria, 30, "#1D3C12")
        self.style_label(labelCaja, 30, "#1D3C12")
        self.style_label(labelCobranza, 30, "#1D3C12")
        self.style_label(labelCartera, 30, "#1D3C12")

        hBox2.addWidget(labelAsesoria)
        hBox2.addWidget(labelCaja)
        hBox2.addWidget(labelCobranza)
        hBox2.addWidget(labelCartera)

        # Grid for turns #
        hBox3 = QHBoxLayout()
        hBox3Widget = QWidget()
        self.gridTurns = QGridLayout(hBox3Widget)
        self.gridTurns.setContentsMargins(10, 0, 10, 0)

        # Spacers
        for i in range(4):
            expanding_spacer = QSpacerItem(500, 20, QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.gridTurns.addItem(expanding_spacer, 0, i)
        
        # Load pending turns from DB
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT servicio, numero
                    FROM turnos
                    WHERE estado = 'pendiente'
                    AND DATE(creado) = DATE('now')
                    ORDER BY creado
                ''')
                for servicio, numero in cursor.fetchall():
                    self.queue[servicio].append(numero)
                    self.add_pending_turn(servicio, numero)
        except:
            traceback.print_exc()

        hBox3.addWidget(hBox3Widget)

        # Add layouts to main layout
        layoutMain.addLayout(hBox1)
        layoutMain.addLayout(hBox2)
        layoutMain.addLayout(hBox3)

    def add_pending_turn(self, servicio, numero, nombre=None):
        row = len(self.queue[servicio]) - 1
        if row < 5:
            gridWidget = QWidget()
            gridHbox = QHBoxLayout(gridWidget)
            gridHbox.setSpacing(0)
            gridWidget.setLayout(gridHbox)

            turno = QWidget()
            turno.setMinimumWidth(int(QApplication.primaryScreen().geometry().width()/20))
            turno.setMaximumWidth(int(QApplication.primaryScreen().geometry().width()/6))
            self.format_turn(turno, f"{servicio}-{numero}", "Nombre Nombre Nombre Nombre")

            llamar = QPushButton("Llamar")
            llamar.setMinimumWidth(70)
            llamar.setMaximumSize(90, 100)
            self.style_button(llamar)

            self.add_spacer(gridHbox)
            gridHbox.addWidget(turno)
            gridHbox.addWidget(llamar)
            self.add_spacer(gridHbox)
            match servicio:
                case 'AS': col = 0
                case 'CA': col = 1
                case 'CO': col = 2
                case 'CT': col = 3
            self.gridTurns.addWidget(gridWidget, row, col)
    
    def style_label(self, label, fontSize, color):
        styleSheet = f"""
            QLabel {{
                color: {color};
                font-size: {fontSize}px;
            }}
        """
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(styleSheet)
    
    def style_button(self, button):
        styleSheet = f"""
            QPushButton {{
                background-color: #669A0D;
                color: white;
                font-size: 20px;
            }}
        """
        button.setStyleSheet(styleSheet)

    def format_turn(self, widget, turn, name):
        widget.setStyleSheet("QWidget {background-color: #3E7B27;}")
        layout = QVBoxLayout(widget)
        label = QLabel(f"{turn}<br>{name}")
        label.setAlignment(Qt.AlignCenter)
        self.style_label(label, 30, "white")
        layout.addWidget(label)

    def add_spacer(self, layout, width=None, height=None, expanding=None):
        label = QLabel()
        if width:
            label.setFixedWidth(width)
        if height:
            label.setFixedHeight(height)
        if expanding:
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(label)

    def show_login(self):
        dialog = LoginDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.current_user = dialog.user_id
        elif not self.current_user: self.close()

    def set_background_color(self, widget, color):
        palette = widget.palette()
        palette.setColor(QPalette.Background, QColor(color))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Iniciar sesión")
        self.setStyleSheet("background-color: #EFE3C2;")
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
        
        if result:
            self.user_id = result[0]
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Credenciales inválidas.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = MainWindow()
    client.show_login()
    if client.current_user:
        client.show()
    sys.exit(app.exec_())