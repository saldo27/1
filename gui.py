import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QLineEdit, QPushButton, QTextEdit
)
from worker import Worker
from shift_scheduler import schedule_shifts
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
        # Connect button to function
        self.schedule_button.clicked.connect(self.schedule_shifts)
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
        for job, shifts in schedule.items():
            output += f"Job {job}:\n"
            for date, worker in shifts.items():
                output += f"  {date}: {worker}\n"
        self.output_display.setText(output)
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
