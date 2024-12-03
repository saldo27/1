import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QLineEdit, QPushButton, QTextEdit, QFileDialog, QGridLayout, QScrollArea
)

from PySide6.QtGui import QAction
from worker import Worker
from shift_scheduler import schedule_shifts, prepare_breakdown, export_breakdown, export_schedule_to_csv
from icalendar import Calendar, Event
from pdf_exporter import export_schedule_to_pdf
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shift Scheduler")
        # Initialize widgets
        self.work_periods_input = QLineEdit()
        self.holidays_input = QLineEdit()
        self.jobs_input = QLineEdit()
        self.num_workers_input = QLineEdit()
        self.min_distance_input = QLineEdit()
        self.max_shifts_per_week_input = QLineEdit()
        self.previous_shifts_input = QLineEdit()
        self.worker_inputs = []
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.schedule_button = QPushButton("Schedule Shifts")
        self.export_ical_button = QPushButton("Export to iCalendar")
        self.export_pdf_button = QPushButton("Export to PDF")
        self.export_csv_button = QPushButton("Export to CSV")
        self.breakdown_button = QPushButton("Breakdown by Worker")
        # Connect buttons to functions
        self.schedule_button.clicked.connect(self.schedule_shifts)
        self.export_ical_button.clicked.connect(self.export_to_ical)
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        self.export_csv_button.clicked.connect(self.export_to_csv)
        self.breakdown_button.clicked.connect(self.display_breakdown)
        # Setup layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Enter work periods (comma-separated, e.g., '01/10/2024-10/10/2024'):"))
        layout.addWidget(self.work_periods_input)
        layout.addWidget(QLabel("Enter holidays (comma-separated, e.g., '05/10/2024'):"))
        layout.addWidget(self.holidays_input)
        layout.addWidget(QLabel("Enter workstations (comma-separated, e.g., 'A,B,C'):"))
        layout.addWidget(self.jobs_input)
        layout.addWidget(QLabel("Enter minimum distance between work shifts (in days):"))
        layout.addWidget(self.min_distance_input)
        layout.addWidget(QLabel("Enter maximum shifts that can be assigned per week:"))
        layout.addWidget(self.max_shifts_per_week_input)
        layout.addWidget(QLabel("Enter number of workers:"))
        layout.addWidget(self.num_workers_input)
        layout.addWidget(self.breakdown_button)
                
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
        layout.addWidget(self.export_csv_button)  # Add the CSV button to the layout
        layout.addWidget(QLabel("Schedule Output:"))
        layout.addWidget(self.output_display)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_worker_inputs(self):
        num_workers = int(self.num_workers_input.text()) if self.num_workers_input.text().isdigit() else 0
        # Clear existing inputs
        for i in reversed(range(self.worker_layout.count())):
            self.worker_layout.itemAt(i).widget().setParent(None)
        self.worker_inputs = []
        for i in range(num_workers):
            identification_input = QLineEdit()
            identification_input.setFixedWidth(150)
            working_dates_input = QLineEdit()
            working_dates_input.setFixedWidth(150)
            percentage_shifts_input = QLineEdit()
            percentage_shifts_input.setFixedWidth(150)
            group_input = QLineEdit()
            group_input.setFixedWidth(150)
            position_incompatibility_input = QLineEdit()
            position_incompatibility_input.setFixedWidth(150)
            group_incompatibility_input = QLineEdit()
            group_incompatibility_input.setFixedWidth(150)
            obligatory_coverage_input = QLineEdit()
            obligatory_coverage_input.setFixedWidth(150)
            unavailable_dates_input = QLineEdit()
            unavailable_dates_input.setFixedWidth(150)

            self.worker_layout.addWidget(QLabel(f"Worker {i+1} Identification:"), i, 0)
            self.worker_layout.addWidget(identification_input, i, 1)
            self.worker_layout.addWidget(QLabel("Working Dates (comma-separated periods):"), i, 2)
            self.worker_layout.addWidget(working_dates_input, i, 3)
            self.worker_layout.addWidget(QLabel("Percentage of Shifts Performed:"), i, 4)
            self.worker_layout.addWidget(percentage_shifts_input, i, 5)
            self.worker_layout.addWidget(QLabel("Group:"), i, 6)
            self.worker_layout.addWidget(group_input, i, 7)
            self.worker_layout.addWidget(QLabel("Position Incompatibility (comma-separated):"), i, 8)
            self.worker_layout.addWidget(position_incompatibility_input, i, 9)
            self.worker_layout.addWidget(QLabel("Group Incompatibility (comma-separated):"), i, 10)
            self.worker_layout.addWidget(group_incompatibility_input, i, 11)
            self.worker_layout.addWidget(QLabel("Obligatory coverage (comma-separated dates):"), i, 12)
            self.worker_layout.addWidget(obligatory_coverage_input, i, 13)
            self.worker_layout.addWidget(QLabel("Unavailable Dates (comma-separated dates):"), i, 14)
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
                [date.strip() for date in input['unavailable_dates'].text().split(',')] if input['unavailable_dates'].text() else []
            )
            for input in self.worker_inputs
        ]
        # Schedule shifts
        schedule = schedule_shifts(work_periods, holidays, jobs, workers, min_distance, max_shifts_per_week)
        # Display the schedule
        output = ""
        self.schedule = schedule  # Save the schedule for exporting
        for job, shifts in schedule.items():
            output += f"Job {job}:\n"
            for date, worker in shifts.items():
                output += f"  {date}: {worker}\n"
        self.output_display.setText(output)

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
        
        # Create a table widget
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Worker", "Shifts Assigned"])
        
        # Populate the table with data from the breakdown
        table.setRowCount(len(breakdown))
        for row, (worker_id, shifts) in enumerate(breakdown.items()):
            worker_item = QTableWidgetItem(worker_id)
            shifts_item = QTableWidgetItem(", ".join([f"{date}: {job}" for date, job in shifts]))
            table.setItem(row, 0, worker_item)
            table.setItem(row, 1, shifts_item)
        
        # Replace the output display with the table
        self.output_display.setParent(None)
        self.output_display = table
        layout = self.centralWidget().layout()
        layout.addWidget(self.output_display)

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
