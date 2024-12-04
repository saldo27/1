import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QLineEdit, QPushButton, QTextEdit, QFileDialog, QGridLayout, QScrollArea
)

from PySide6.QtGui import QAction
from worker import Worker
from shift_scheduler import import_workers_from_csv, schedule_shifts, prepare_breakdown, export_breakdown, export_schedule_to_csv
from icalendar import Calendar, Event
from pdf_exporter import export_schedule_to_pdf
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class ScheduleOutputWindow(QMainWindow):
    def __init__(self, schedule, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Distribución de Guardias")
        self.setGeometry(100, 100, 600, 400)
        self.schedule = schedule
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        output = QTextEdit()
        output.setReadOnly(True)
        schedule_text = self.format_schedule(self.schedule)
        output.setText(schedule_text)
        layout.addWidget(output)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def format_schedule(self, schedule):
        output = ""
        for job, shifts in schedule.items():
            output += f"Job {job}:\n"
            for date, worker in shifts.items():
                output += f"  {date}: {worker}\n"
        return output
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Distribución de Guardias")

        # Initialize widgets
        self.work_periods_input = QLineEdit()
        self.holidays_input = QLineEdit()
        self.jobs_input = QLineEdit()
        self.num_workers_input = QLineEdit()
        self.min_distance_input = QLineEdit()
        self.max_shifts_per_week_input = QLineEdit()
        self.previous_shifts_input = QLineEdit()
        self.worker_inputs = []
        self.schedule_button = QPushButton("Poner Guardias")
        self.export_ical_button = QPushButton("Exportar a iCalendar")
        self.export_pdf_button = QPushButton("Exportar a PDF")
        self.export_csv_button = QPushButton("Exportar a CSV")
        self.breakdown_button = QPushButton("Desglose por Médico")
        self.import_csv_button = QPushButton("Importar desde CSV")

        # Connect buttons to functions
        self.schedule_button.clicked.connect(self.schedule_shifts)
        self.export_ical_button.clicked.connect(self.export_to_ical)
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        self.export_csv_button.clicked.connect(self.export_to_csv)
        self.breakdown_button.clicked.connect(self.display_breakdown)
        self.import_csv_button.clicked.connect(self.import_from_csv)

        # Setup layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Periodos de trabajo (separados por comas, e.j., '01/10/2024-10/10/2024'):"))
        layout.addWidget(self.work_periods_input)
        layout.addWidget(QLabel("Festivos (separados por comas, e.j., '05/10/2024'):"))
        layout.addWidget(self.holidays_input)
        layout.addWidget(QLabel("Puestos de trabajo (e.j., 'A,B,C'):"))
        layout.addWidget(self.jobs_input)
        layout.addWidget(QLabel("Distancia minima entre guardias:"))
        layout.addWidget(self.min_distance_input)
        layout.addWidget(QLabel("Guardias máximas por semana:"))
        layout.addWidget(self.max_shifts_per_week_input)
        layout.addWidget(QLabel("Número de médicos:"))
        layout.addWidget(self.num_workers_input)
        layout.addWidget(self.breakdown_button)
        layout.addWidget(self.import_csv_button)  # Add the CSV import button to the layout

        # Worker inputs layout
        self.worker_layout = QGridLayout()

        # Scroll area for worker inputs
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget = QWidget()
        self.scroll_area_widget.setLayout(self.worker_layout)
        self.scroll_area.setWidget(self.scroll_area_widget)

        layout.addWidget(self.scroll_area)

        self.num_workers_input.textChanged.connect(self.update_worker_inputs)

        layout.addWidget(self.schedule_button)
        layout.addWidget(self.export_ical_button)
        layout.addWidget(self.export_pdf_button)
        layout.addWidget(self.export_csv_button)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_worker_inputs(self):
        num_workers = int(self.num_workers_input.text()) if self.num_workers_input.text().isdigit() else 0
        for i in reversed(range(self.worker_layout.count())):
            self.worker_layout.itemAt(i).widget().setParent(None)
        self.worker_inputs = []
        for i in range(num_workers):
            identification_input = QLineEdit()
            identification_input.setFixedWidth(50)
            working_dates_input = QLineEdit()
            working_dates_input.setFixedWidth(100)
            percentage_shifts_input = QLineEdit()
            percentage_shifts_input.setFixedWidth(30)
            group_input = QLineEdit()
            group_input.setFixedWidth(20)
            position_incompatibility_input = QLineEdit()
            position_incompatibility_input.setFixedWidth(20)
            group_incompatibility_input = QLineEdit()
            group_incompatibility_input.setFixedWidth(20)
            obligatory_coverage_input = QLineEdit()
            obligatory_coverage_input.setFixedWidth(100)
            unavailable_dates_input = QLineEdit()
            unavailable_dates_input.setFixedWidth(100)

            self.worker_layout.addWidget(QLabel(f"Identificación {i+1}:"), i, 0)
            self.worker_layout.addWidget(identification_input, i, 1)
            self.worker_layout.addWidget(QLabel("Cuando trabaja (separado por comas):"), i, 2)
            self.worker_layout.addWidget(working_dates_input, i, 3)
            self.worker_layout.addWidget(QLabel("Porcentaje de jornada:"), i, 4)
            self.worker_layout.addWidget(percentage_shifts_input, i, 5)
            self.worker_layout.addWidget(QLabel("Grupo:"), i, 6)
            self.worker_layout.addWidget(group_input, i, 7)
            self.worker_layout.addWidget(QLabel("No trabaja Rosell:"), i, 8)
            self.worker_layout.addWidget(position_incompatibility_input, i, 9)
            self.worker_layout.addWidget(QLabel("Incompatibilidad con grupo:"), i, 10)
            self.worker_layout.addWidget(group_incompatibility_input, i, 11)
            self.worker_layout.addWidget(QLabel("Guardias obligatorias (separadas por comas):"), i, 12)
            self.worker_layout.addWidget(obligatory_coverage_input, i, 13)
            self.worker_layout.addWidget(QLabel("Guardias No disponible (separado por comas):"), i, 14)
            self.worker_layout.addWidget(unavailable_dates_input, i, 15)

            self.worker_inputs.append({
                'identification': identification_input,
                'working_dates': working_dates_input,
                'percentage_shifts': percentage_shifts_input,
                'group': group_input,
                'position_incompatibility': position_incompatibility_input,
                'group_incompatibility': group_incompatibility_input,
                'obligatory_coverage': obligatory_coverage_input,
                'unavailable_dates': unavailable_dates_input
            })

    def schedule_shifts(self):
    # Get inputs
    work_periods = self.work_periods_input.text().split(',')
    holidays = self.holidays_input.text().split(',')
    jobs = self.jobs_input.text().split(',')
    num_workers = int(self.num_workers_input.text())
    min_distance = int(self.min_distance_input.text())
    max_shifts_per_week = int(self.max_shifts_per_week_input.text())
    # Create workers list from user input
    workers = [
        Worker(
            input['identification'].text(),
            [period.strip() for period in input['working_dates'].text().split(',')] if input['working_dates'].text() else [],
            float(input['percentage_shifts'].text() or 100),  # Default to 100 if blank
            input['group'].text() or '1',
            input['position_incompatibility'].text().split(',') if input['position_incompatibility'].text() else [],
            input['group_incompatibility'].text().split(',') if input['group_incompatibility'].text() else [],
            [date.strip() for date in input['obligatory_coverage'].text().split(',')] if input['obligatory_coverage'].text() else [],
            [date.strip() for date in input['unavailable_dates'].text().split(',')] if input['unavailable_dates'].text() else [],
            previously_assigned_shifts=[]  # Initialize with an empty list or load from CSV if available
        )
        for input in self.worker_inputs
    ]
    # Schedule shifts
    schedule = schedule_shifts(work_periods, holidays, jobs, workers, min_distance, max_shifts_per_week)
    self.schedule = schedule  # Save the schedule for exporting

    self.schedule_window = ScheduleOutputWindow(schedule)
    self.schedule_window.show()
                        
    def import_from_csv(self):
    options = QFileDialog.Options()
    filePath, _ = QFileDialog.getOpenFileName(self, "Import Workers from CSV", "", "CSV Files (*.csv);;All Files (*)", options=options)
    if filePath:
        workers = import_workers_from_csv(filePath)
        for worker in workers:
            # Update UI with imported worker data
            self.num_workers_input.setText(str(len(workers)))
            self.update_worker_inputs()
            for i, worker in enumerate(workers):
                self.worker_inputs[i]['identification'].setText(worker.identification)
                self.worker_inputs[i]['working_dates'].setText(','.join([f"{start.strftime('%d/%m/%Y')}-{end.strftime('%d/%m/%Y')}" for start, end in worker.work_dates]))
                self.worker_inputs[i]['percentage_shifts'].setText(str(worker.percentage_shifts))
                self.worker_inputs[i]['group'].setText(worker.group)
                self.worker_inputs[i]['position_incompatibility'].setText(','.join(worker.incompatible_job))
                self.worker_inputs[i]['group_incompatibility'].setText(','.join(worker.group_incompatibility))
                self.worker_inputs[i]['obligatory_coverage'].setText(','.join([date.strftime('%d/%m/%Y') for date in worker.obligatory_coverage]))
                self.worker_inputs[i]['unavailable_dates'].setText(','.join([date.strftime('%d/%m/%Y') for date in worker.unavailable_dates]))

    def export_to_ical(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(self, "Save Schedule as iCalendar", "", "iCalendar Files (*.ics);;All Files (*)", options=options)
        if filePath:
            self.export_icalendar(filePath)

    def export_to_pdf(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(self, "Save Schedule as PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if filePath:
            export_schedule_to_pdf(self.schedule, filePath)

    def export_icalendar(self, filePath):
        cal = Calendar()
        for job, shifts in self.schedule.items():
            for date_str, worker_id in shifts.items():
                date = datetime.strptime(date_str, "%d/%m/%Y")
                event = Event()
                event.add('summary', f'Shift for Job {job}')
                event.add('dtstart', date)
                event.add('dtend', date)
                event.add('description', f'Worker: {worker_id}')
                cal.add_component(event)
        with open(filePath, 'wb') as f:
            f.write(cal.to_ical())
            
    def display_breakdown(self):
        breakdown = prepare_breakdown(self.schedule)
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Worker", "Shifts Assigned"])
        table.setRowCount(len(breakdown))
        for row, (worker_id, shifts) in enumerate(breakdown.items()):
            worker_item = QTableWidgetItem(worker_id)
            shifts_item = QTableWidgetItem(", ".join([f"{date}: {job}" for date, job in shifts]))
            table.setItem(row, 0, worker_item)
            table.setItem(row, 1, shifts_item)
        layout = self.centralWidget().layout()
        layout.addWidget(table)

    # Implement the export_to_csv function
    def export_to_csv(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(self, "Save Schedule as CSV", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if filePath:
            export_schedule_to_csv(self.schedule, filePath)
             
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
