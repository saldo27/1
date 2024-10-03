import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QLineEdit, QPushButton, QTextEdit, QFileDialog
)
from PySide6.QtGui import QAction
from worker import Worker
from shift_scheduler import schedule_shifts
from icalendar import Calendar, Event
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
        layout.addWidget(self.schedule_button)
        layout.addWidget(self.export_ical_button)
        layout.addWidget(self.export_pdf_button)
        layout.addWidget(QLabel("Schedule Output:"))
        layout.addWidget(self.output_display)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def schedule_shifts(self):
        # Get inputs
        work_periods = self.work_periods_input.text().split(',')
        holidays = self.holidays_input.text().split(',')
        jobs = self.jobs_input.text().split(',')
        num_workers = int(self.num_workers_input.text())
        previous_shifts_input = self.previous_shifts_input.text().split(',')
        # Create workers list from user input
        workers = [Worker.from_user_input() for _ in range(num_workers)]
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
            c = canvas.Canvas(filePath, pagesize=letter)
            width, height = letter
            y = height - 40
            c.setFont("Helvetica", 12)
            for job, shifts in self.schedule.items():
                c.drawString(40, y, f"Job {job}:")
                y -= 20
                for date, worker in shifts.items():
                    c.drawString(60, y, f"{date}: {worker}")
                    y -= 20
                y -= 20
                if y < 40:
                    c.showPage()
                    y = height - 40
            c.save()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()

