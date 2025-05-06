import sys, pika, traceback, json
from dotenv import load_dotenv
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
load_dotenv()

class MainWindow(QMainWindow):
    commandSignal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.screenGeometry = QApplication.primaryScreen().geometry()
        self.init_ui()
        #self.setup_rabbitmq()
        #self.commandSignal.connect(self.handle_command)
        
    def init_ui(self):
        self.setWindowTitle("Digiturno reportes")
        self.setGeometry(int(self.screenGeometry.width()/2 - 569),
                         int(self.screenGeometry.height()/2 - 350), 1138, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.set_background_color(central_widget, "#EFE3C2")
        
        mainLayout = QVBoxLayout(central_widget)
        self.stackedWidget = QStackedWidget()
        mainLayout.addWidget(self.stackedWidget)
        
####### Layout 0 #######
        widget0 = QWidget()
        layout0 = QVBoxLayout(widget0)
        widget0.setLayout(layout0)
        #
        hWidget0 = QWidget()
        hBox0 = QHBoxLayout(hWidget0)
        hWidget0.setLayout(hBox0)
        
        self.startTxt = QLineEdit()
        labelHypen = QLabel('---')
        self.endTxt = QLineEdit()
        self.startTxt.editingFinished.connect(self.validate_date_input)
        self.endTxt.editingFinished.connect(self.validate_date_input)
        self.startTxt.focusInEvent = lambda e: self.set_active_field('start')
        self.endTxt.focusInEvent = lambda e: self.set_active_field('end')
        
        hBox0.addWidget(self.startTxt)
        hBox0.addWidget(labelHypen)
        hBox0.addWidget(self.endTxt)
        #
        self.calendar = QCalendarWidget()
        self.lastDate1 = self.calendar.selectedDate()
        self.lastDate2 = self.calendar.selectedDate()
        self.calendar_changed()
        self.calendar.selectionChanged.connect(self.calendar_changed)
        
        hWidget1 = QWidget()
        hBox1 = QHBoxLayout(hWidget1)
        hWidget1.setLayout(hBox1)
        
        vWidget0 = QWidget()
        vBox0 = QVBoxLayout(vWidget0)
        vWidget0.setLayout(vBox0)
        
        labelRange = QLabel('Rango de tiempo:')
        btnDay = QRadioButton('Día')
        btnWeek = QRadioButton('Semana')
        btnMonth = QRadioButton('Mes')
        btnYear = QRadioButton('Año')
        btnCustom = QRadioButton('Entre...')
        btnGroup = QButtonGroup()
        btnGroup.addButton(btnDay)
        btnGroup.addButton(btnWeek)
        btnGroup.addButton(btnMonth)
        btnGroup.addButton(btnYear)
        btnGroup.addButton(btnCustom)
        
        vBox0.addWidget(labelRange)
        vBox0.addWidget(btnDay)
        vBox0.addWidget(btnWeek)
        vBox0.addWidget(btnMonth)
        vBox0.addWidget(btnYear)
        vBox0.addWidget(btnCustom)
        
        vWidget1 = QWidget()
        vBox1 = QVBoxLayout(vWidget1)
        vWidget1.setLayout(vBox1)
        
        btnGenerate = QPushButton('Generar reporte')
        
        vBox1.addWidget(btnGenerate)
        
        hBox1.addWidget(vWidget0)
        hBox1.addWidget(vWidget1)
        #
        layout0.addWidget(hWidget0)
        layout0.addWidget(self.calendar)
        layout0.addWidget(hWidget1)
        
####### Stack widgets #######
        self.stackedWidget.addWidget(widget0)
    
    def set_active_field(self, field):
        self.activeField = field
        if field == 'start':
            self.endTxt.setStyleSheet('')
            self.startTxt.setStyleSheet('border: 2px solid black; background-color: #efffec;')
            self.calendar.setSelectedDate(self.lastDate1)
            self.calendar.setMinimumDate(QDate(1, 1, 1))
            self.calendar.setMaximumDate(self.lastDate2)
        else:
            self.startTxt.setStyleSheet('')
            self.endTxt.setStyleSheet('border: 2px solid black; background-color: #efffec;')
            self.calendar.setSelectedDate(self.lastDate2)
            self.calendar.setMaximumDate(QDate(9999, 12, 31))
            self.calendar.setMinimumDate(self.lastDate1)
    
    def validate_date_input(self):
        try:
            date1 = QDate.fromString(self.startTxt.text(), 'yyyy-MM-dd')
            date2 = QDate.fromString(self.endTxt.text(), 'yyyy-MM-dd')
            if date1.isValid() and date2.isValid():
                self.lastDate1 = date1
                self.lastDate2 = date2
                if self.activeField == 'start':
                    self.calendar.setSelectedDate(date1)
                else: self.calendar.setSelectedDate(date2)
            else: raise ValueError('Invalid date format')
        except ValueError:
            self.startTxt.setText(self.lastDate1.toString('yyyy-MM-dd'))
            self.endTxt.setText(self.lastDate2.toString('yyyy-MM-dd'))
    
    def calendar_changed(self):
        selected = self.calendar.selectedDate()
        if hasattr(self, 'activeField'):
            if self.activeField == 'start':
                self.lastDate1 = selected
            else:
                self.lastDate2 = selected
        else:
            self.lastDate1 = self.lastDate2 = selected
        self.startTxt.setText(self.lastDate1.toString('yyyy-MM-dd'))
        self.endTxt.setText(self.lastDate2.toString('yyyy-MM-dd'))
    
    def set_background_color(self, widget, color):
        palette = widget.palette()
        palette.setColor(QPalette.Background, QColor(color))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())