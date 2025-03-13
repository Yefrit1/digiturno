import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from reports import ReportGenerator

class ReportWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digiturno Reports")
        self.setGeometry(100, 100, 1000, 800)
        self.report_gen = ReportGenerator()
        self.init_ui()
        
    def init_ui(self):
        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Report selection
        self.report_combo = QComboBox()
        self.report_combo.addItems([
            "Daily Summary",
            "Employee Productivity", 
            "Station Load"
        ])
        self.report_combo.currentIndexChanged.connect(self.update_date_inputs)
        layout.addWidget(QLabel("Tipo de reporte:"))
        layout.addWidget(self.report_combo)

        # Date selection
        date_layout = QHBoxLayout()
        date_layout.setAlignment(Qt.AlignCenter)
        self.single_date_radio = QRadioButton("Un día")
        self.date_range_radio = QRadioButton("Rango de días")
        self.single_date_radio.setChecked(True)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setEnabled(False)
        
        date_layout.addWidget(self.single_date_radio)
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel(" - "))
        date_layout.addWidget(self.end_date)
        date_layout.addWidget(self.date_range_radio)
        
        self.date_range_radio.toggled.connect(self.toggle_date_range)
        layout.addLayout(date_layout)

        # Generate button
        self.btn_generate = QPushButton("Generate Report")
        self.btn_generate.clicked.connect(self.generate_report)
        layout.addWidget(self.btn_generate)

        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Export button
        self.btn_export = QPushButton("Export to CSV")
        self.btn_export.clicked.connect(self.export_report)
        layout.addWidget(self.btn_export)

        self.update_date_inputs()

    def toggle_date_range(self, checked):
        self.end_date.setEnabled(checked)
        if not checked:
            self.end_date.setDate(self.start_date.date())

    def update_date_inputs(self):
        report_type = self.report_combo.currentText()
        if report_type == "Daily Summary":
            self.date_range_radio.setEnabled(False)
            self.single_date_radio.setChecked(True)
        else:
            self.date_range_radio.setEnabled(True)

    def generate_report(self):
        report_type = self.report_combo.currentText()
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd") if self.date_range_radio.isChecked() else start_date

        try:
            with ReportGenerator() as reporter:
                if report_type == "Daily Summary":
                    data = reporter.daily_summary(start_date)
                    headers = ["Total Turns", "Attended", "Canceled", "Avg Wait (min)"]
                    self.populate_table([data], headers)
                    
                elif report_type == "Employee Productivity":
                    data = reporter.employee_productivity(start_date)
                    headers = ["Employee", "Turns Handled"]
                    self.populate_table(data, headers)
                    
                elif report_type == "Station Load":
                    data = reporter.station_load(start_date)
                    headers = ["Station", "Service Type", "Turns Processed"]
                    self.populate_table(data, headers)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report:\n{str(e)}")

    def populate_table(self, data, headers):
        self.table.clear()
        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)

        self.table.resizeColumnsToContents()

    def export_report(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Report", "", "CSV Files (*.csv)")
        
        if file_name:
            try:
                headers = [self.table.horizontalHeaderItem(i).text() 
                          for i in range(self.table.columnCount())]
                
                data = []
                for row in range(self.table.rowCount()):
                    data.append([
                        self.table.item(row, col).text()
                        for col in range(self.table.columnCount())
                    ])
                
                with ReportGenerator() as reporter:
                    success = reporter.export_to_csv(data, headers, file_name)
                    
                if success:
                    QMessageBox.information(self, "Success", 
                        f"Report exported to:\n{file_name}")
                else:
                    QMessageBox.warning(self, "Warning", 
                        "Failed to export report")

            except Exception as e:
                QMessageBox.critical(self, "Error", 
                    f"Export failed:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReportWindow()
    window.show()
    sys.exit(app.exec_())