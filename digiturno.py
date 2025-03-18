import sys
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

####### Layout ENTRADA #######
        self.ent = QWidget()
        self.layoutEnt = QVBoxLayout(self.ent)
        self.layoutEnt.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        bluleibel = QLabel("ENTRADA")
        boton = QPushButton("testststet")
        boton.setFixedSize(int(self.screenGeometry.width()*0.2), int(self.screenGeometry.height()*0.2))
        self.layoutEnt.addWidget(bluleibel)
        self.layoutEnt.addWidget(boton)

####### Layout ASOCIADO #######
        self.asc = QWidget()
        self.layoutAsc = QVBoxLayout(self.asc)
        self.layoutAsc.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        asos = QLabel("ASOCIADO")
        self.layoutAsc.addWidget(asos)
        
####### Layout NO ASOCIADO #######
        self.noAsc = QWidget()
        self.layoutNoAsc = QVBoxLayout(self.noAsc)
        
####### Layout SERVICIO #######
        self.serv = QWidget()
        self.layoutServ = QVBoxLayout(self.serv)

####### Stack layouts #######
        self.stackedWidget.addWidget(self.ent)
        self.stackedWidget.addWidget(self.asc)
        self.stackedWidget.addWidget(self.noAsc)
        self.stackedWidget.addWidget(self.serv)

        # Navigation buttons
        self.create_navigation_buttons(main_layout)
        self.showFullScreen()

    def create_navigation_buttons(self, main_layout):
        nav_layout = QHBoxLayout()

        # Create buttons for each layout
        button1 = QPushButton("Go to ENTRADA")
        button2 = QPushButton("Go to ASOCIADO")
        button3 = QPushButton("Go to NO ASOCIADO")
        button4 = QPushButton("Go to SERVICIO")

        # Connect buttons to switch layouts
        button1.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        button2.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        button3.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        button4.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))

        # Add buttons to the navigation layout
        nav_layout.addWidget(button1)
        nav_layout.addWidget(button2)
        nav_layout.addWidget(button3)
        nav_layout.addWidget(button4)

        # Add the navigation layout to the main layout
        main_layout.addLayout(nav_layout)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())