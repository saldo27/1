import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QLineEdit, QPushButton, QTextEdit, QFileDialog, QGridLayout
)
from PySide6.QtGui import QAction
from worker import Worker
from shift_scheduler import schedule_shifts
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
        self.previous_shifts_input = QLineEdit()
        self.worker_inputs = []
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.schedule_button = QPushButton("Schedule Shifts")
        self.export_ical_button = QPushButton("Export to iCalendar")
        self.export_pdf_button = QPushButton("Export to PDF")
        # Connect buttons to functions
        self.schedule_button.clicked.connect(self.schedule_shifts)
        self.export_ical_button.clicked.connect(self.export_to_ical)
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        # Setup layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Enter work periods (comma-separated, e.g., '01/10/2024-10/10/2024'):"))
        layout.addWidget(self.work_periods_input)
        layout.addWidget(QLabel("Enter holidays (comma-separated, e.g., '05/10/2024'):"))
        layout.addWidget(self.holidays_input)
        layout.addWidget(QLabel("Enter jobs (comma-separated, e.g., 'A,B,C'):"))
        layout.addWidget(self.jobs_input)
        layout.addWidget(QLabel("Enter number of workers:"))
        layout.addWidget(self.num_workers_input)
        layout.addWidget(QLabel("Enter previous shifts if any (optional, leave blank if none):"))
        layout.addWidget(self.previous_shifts_input)
        
        # Worker inputs layout
        self.worker_layout = QGridLayout()
        layout.addLayout(self.worker_layout)
        
        self.num_workers_input.textChanged.connect(self.update_worker_inputs)
        
        layout.addWidget(self.schedule_button)
        layout.addWidget(self.export_ical_button)
        layout.addWidget(self.export_pdf_button)
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
            working_dates_input = QLineEdit()
            percentage_shifts_input = QLineEdit()
            group_input = QLineEdit()
            position_incompatibility_input = QLineEdit()
            group_incompatibility_input = QLineEdit()
            mandatory_guard_duty_input = QLineEdit()
            unavailable_dates_input = QLineEdit()

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
            self.worker_layout.addWidget(QLabel("Mandatory Guard Duty (comma-separated dates):"), i, 12)
            self.worker_layout.addWidget(mandatory_guard_duty_input, i, 13)
            self.worker_layout.addWidget(QLabel("Unavailable Dates (comma-separated dates):"), i, 14)
            self.worker_layout.addWidget(unavailable_dates_input, i, 15)

            self.worker_inputs.append({
                'identification': identification_input,
                'working_dates': working_dates_input,
                'percentage_shifts': percentage_shifts_input,
                'group': group_input,
                'position_incompatibility': position_incompatibility_input,
                'group_incompatibility': group_incompatibility_input,
                'mandatory_guard_duty': mandatory_guard_duty_input,
                'unavailable_dates': unavailable_dates_input
            })

    def schedule_shifts(self):
        # Get inputs
        work_periods = self.work_periods_input.text().split(',')
        holidays = self.holidays_input.text().split(',')
        jobs = self.jobs_input.text().split(',')
        num_workers = int(self.num_workers_input.text())
        previous_shifts_input = self.previous_shifts_input.text().split(',')
        # Create workers list from user input
        workers = [
            Worker.from_user_input(
                input['identification'].text(),
                input['working_dates'].text(),
                int(input['percentage_shifts'].text() or 0),
                int(input['group'].text() or 0),
                input['position_incompatibility'].text(),
                input['group_incompatibility'].text(),
                input['mandatory_guard_duty'].text(),
                input['unavailable_dates'].text()
            )
            for input in self.worker_inputs
        ]
        # Convert previous shifts input
        previous_shifts = [datetime.strptime(shift.strip(), "%d/%m/%Y") for shift in previous_shifts_input if shift]
        # Schedule shifts
        schedule = schedule_shifts(work_periods, holidays, jobs, workers, previous_shifts)
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
            cal = Calendar()
            for job, shifts in self.schedule.items():
                for date, worker in shifts.items():
                    event = Event()
                    event.add('summary', f'Job {job}: {worker}')
                    event.add('dtstart', datetime.strptime(date, "%d/%m/%Y"))
                    event.add('dtend', datetime.strptime(date, "%d/%m/%Y"))
                    cal.add_component(event)
            with open(filePath, 'wb') as file:
                file.write(cal.to_ical())

    def export_to_pdf(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(self, "Save Schedule as PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if filePath:
            export_schedule_to_pdf(self.schedule, filename=filePath)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
