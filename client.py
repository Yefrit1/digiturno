import sys
import socket
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class StaffClient(QWidget):
    def __init__(self):
        super().__init__()
        self.host = '192.168.0.54'  # Replace with server IP
        self.port = 47529
        self.usuario = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Control Digiturno")
        self.setStyleSheet("background-color: #3D5E31")
        self.mainLayout = QVBoxLayout()

        self.userLayout = QFrame(self)
        self.actionLayout = QFrame(self)
        self.actionLayout.hide()

        self.setup_user_screen()
        self.setup_action_screen()

        self.mainLayout.addWidget(self.userLayout)
        self.mainLayout.addWidget(self.actionLayout)

        self.setLayout(self.mainLayout)
        self.show()
    
    def setup_user_screen(self):
        layout = QVBoxLayout(self.userLayout)
        titleLabel = QLabel("Seleccione el usuario")
        titleLabel.setAlignment(Qt.AlignCenter)
        titleLabel.setStyleSheet("font-size: 20px; font-weight: bold; color: white")
        layout.addWidget(titleLabel)

        gridLayout = QGridLayout()

        tipoDeUsuario = [("Caja 1", "A"), ("Caja 2", "B"), ("Asesor 1", "C"),
                         ("Asesor 2", "D"), ("Asesor 3", "E"), ("Asesor 4", "F"),
                         ("Asesor 5", "G"), ("Cartera", "H"), ("Cobranza", "I")]
        row, col = 0, 0

        for displayName, code in tipoDeUsuario:
            button = QPushButton(displayName)
            button.setFixedSize(120, 80)
            button.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #3D5E31;
                    border-radius: 10px;
                    font-size: 15px;
                    font-weight: bold;}
                QPushButton:hover {
                    background-color: #758A76;
                    color: white;}
                QPushButton:pressed {
                    background-color: #9AB59C;}
                """)
            button.clicked.connect(lambda _, code=code: self.select_user(code))
            gridLayout.addWidget(button, row, col)
            col += 1
            if col == 3:
                row += 1
                col = 0
        
        layout.addLayout(gridLayout)
    
    def setup_action_screen(self):
        layout = QVBoxLayout(self.actionLayout)
        
        self.estacionActual = QLabel("")
        self.estacionActual.setAlignment(Qt.AlignCenter)
        self.estacionActual.setStyleSheet("font-size: 15px; color: white")
        layout.addWidget(self.estacionActual)

        buttonLayout = QHBoxLayout()

        # Botón siguiente
        self.nextButton = QPushButton("Siguiente")
        self.nextButton.setFixedSize(120, 80)
        self.nextButton.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #3D5E31;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;}
            QPushButton:hover {
                background-color: #758A76;
                color: white;}
            QPushButton:pressed {
                background-color: #9AB59C;}
                """)
        self.nextButton.clicked.connect(lambda: self.send_command("s"))

        # Botón cancelar
        self.cancelButton = QPushButton("Cancelar")
        self.cancelButton.setFixedSize(120, 80)
        self.cancelButton.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #380005;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;}
            QPushButton:hover {
                background-color: #875D64;}
            QPushButton:pressed {
                background-color: #C98B94;}
                """)
        self.cancelButton.clicked.connect(lambda: self.send_command("c"))

        # Botón de regresar
        self.backButton = QPushButton("Cambiar usuario")
        self.backButton.setFixedSize(160, 80)
        self.backButton.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #3D5E31;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;}
            QPushButton:hover {
                background-color: #758A76;
                color: white;}
            QPushButton:pressed {
                background-color: #9AB59C;}
                """)
        self.backButton.clicked.connect(self.return_to_user_screen)

        buttonLayout.addWidget(self.nextButton)
        buttonLayout.addWidget(self.cancelButton)
        layout.addLayout(buttonLayout)
        layout.addStretch()
        layout.addWidget(self.backButton)
        layout.addStretch()
    
    def select_user(self, userCode):
        self.usuario = userCode
        nombreEstacion = {
            "A": "Caja1", "B": "Caja2", "C": "Asesor1",
            "D": "Asesor2", "E": "Asesor3", "F": "Asesor4",
            "G": "Asesor5", "H": "Cartera", "I": "Cobranza"
        }
        self.estacionActual.setText(f"{nombreEstacion.get(userCode, userCode)}")

        self.userLayout.hide()
        self.actionLayout.show()
    
    def return_to_user_screen(self):
        self.actionLayout.hide()
        self.userLayout.show()
        self.usuario = None

    def send_command(self, action):
        if not self.usuario:
            return

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((self.host, self.port))
                if action == "s":
                    s.sendall(f"NEXT_{self.usuario}".encode('utf-8'))
                elif action == "c":
                    s.sendall(f"CANCEL_{self.usuario}".encode('utf-8'))
                else: print("Invalid action") # Debug
            except ConnectionRefusedError:
                print("Could not connect to server")
            except IOError as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = StaffClient()
    sys.exit(app.exec_())