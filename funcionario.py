import sys, socket, sqlite3
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.db_path = "digiturno.db"
        self.host = '192.168.0.54'
        self.port = 47529
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Funcionario COOHEM")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.set_background_color(central_widget, '#EFE3C2')
        layoutMain = QVBoxLayout(central_widget)
        layoutMain.setAlignment(Qt.AlignTop)

        # Logo and title
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

        # Headers
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

        # Grid for turns
        hBox3 = QHBoxLayout()
        hBox3Widget = QWidget()
        self.gridTurns = QGridLayout(hBox3Widget)
        self.gridTurns.setContentsMargins(10, 0, 10, 0)

        # Spacers
        expanding_spacer = QSpacerItem(150, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        for i in range(4):
            self.gridTurns.addItem(expanding_spacer, 0, i)
        
        # Placeholder turns
        for j in range(5):
            for i in range(4):
                gridWidget = QWidget()
                gridHbox = QHBoxLayout(gridWidget)
                gridHbox.setSpacing(0)
                gridWidget.setLayout(gridHbox)
                
                turno = QWidget()
                turno.setMaximumWidth(int(QApplication.primaryScreen().geometry().width()/6))
                turno.setMinimumWidth(int(QApplication.primaryScreen().geometry().width()/20))
                self.format_turn(turno, f"AS-{4*j+i+1}", "IDK IDK IDK IDK")
                button2 = QPushButton("Llamar")
                button2.setMinimumWidth(60)
                button2.setMaximumSize(90, 100)

                self.add_spacer(gridHbox)
                gridHbox.addWidget(turno)
                gridHbox.addWidget(button2)
                self.add_spacer(gridHbox)
                self.gridTurns.addWidget(gridWidget, j, i)
        
        hBox3.addWidget(hBox3Widget)

        # Add layouts to main layout
        layoutMain.addLayout(hBox1)
        layoutMain.addLayout(hBox2)
        layoutMain.addLayout(hBox3)

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
                background-color: #3E7B27;
                color: white;
                font-size: 20px;
            }}
        """
        button.setFixedSize(90, 70)
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

    def set_background_color(self, widget, color):
        palette = widget.palette()
        palette.setColor(QPalette.Background, QColor(color))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)

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
        
        if result:
            self.user_info = {
                'id': result[0],
                'is_admin': bool(result[1])
            }
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Credenciales inválidas")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())