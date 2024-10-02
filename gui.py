import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QLineEdit, QPushButton, QTextEdit, QFormLayout
)
from worker import Worker
from shift_scheduler import schedule_shifts

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Shift Scheduler")

        # Initialize widgets for general input
        self.work_periods_input = QLineEdit()
        self.holidays_input = QLineEdit()
        self.jobs_input = QLineEdit()
        self.num_workers_input = QLineEdit()
        self.previous_shifts_input = QLineEdit()
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.schedule_button = QPushButton("Schedule Shifts")

        # Initialize widgets for worker input
        self.worker_id_input = QLineEdit()
        self.worker_work_periods_input = QLineEdit()
        self.worker_percentage_input = QLineEdit()
        self.worker_group_input = QLineEdit()
        self.worker_job_incompatibilities_input = QLineEdit()
        self.worker_group_incompatibilities_input = QLineEdit()
        self.worker_mandatory_shifts_input = QLineEdit()
        self.worker_unavailable_shifts_input = QLineEdit()
        self.add_worker_button = QPushButton("Add Worker")

        # Connect buttons to functions
        self.schedule_button.clicked.connect(self.schedule_shifts)
        self.add_worker_button.clicked.connect(self.add_worker)

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

        layout.addWidget(QLabel("Worker Details:"))
        form_layout = QFormLayout()
        form_layout.addRow("Worker ID:", self.worker_id_input)
        form_layout.addRow("Work Periods:", self.worker_work_periods_input)
        form_layout.addRow("Work Percentage:", self.worker_percentage_input)
        form_layout.addRow("Group:", self.worker_group_input)
        form_layout.addRow("Job Incompatibilities:", self.worker_job_incompatibilities_input)
        form_layout.addRow("Group Incompatibilities:", self.worker_group_incompatibilities_input)
        form_layout.addRow("Mandatory Shifts:", self.worker_mandatory_shifts_input)
        form_layout.addRow("Unavailable Shifts:", self.worker_unavailable_shifts_input)
        layout.addLayout(form_layout)
        layout.addWidget(self.add_worker_button)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        # Initialize worker list
        self.workers = []

    def add_worker(self):
        worker_id = self.worker_id_input.text()
        work_periods = self.worker_work_periods_input.text().split(',')
        work_percentage = int(self.worker_percentage_input.text() or 100)
        group = int(self.worker_group_input.text() or 0)
        job_incompatibilities = self.worker_job_incompatibilities_input.text().split(',')
        group_incompatibilities = self.worker_group_incompatibilities_input.text().split(',')
        mandatory_shifts = self.worker_mandatory_shifts_input.text().split(',')
        unavailable_shifts = self.worker_unavailable_shifts_input.text().split(',')

        worker = Worker(worker_id, work_periods, work_percentage, group, job_incompatibilities, group_incompatibilities, mandatory_shifts, unavailable_shifts)
        self.workers.append(worker)

        # Clear input fields after adding worker
        self.worker_id_input.clear()
        self.worker_work_periods_input.clear()
        self.worker_percentage_input.clear()
        self.worker_group_input.clear()
        self.worker_job_incompatibilities_input.clear()
        self.worker_group_incompatibilities_input.clear()
        self.worker_mandatory_shifts_input.clear()
        self.worker_unavailable_shifts_input.clear()

    def schedule_shifts(self):
        # Get inputs
        work_periods = self.work_periods_input.text().split(',')
        holidays = self.holidays_input.text().split(',')
        jobs = self.jobs_input.text().split(',')
        previous_shifts_input = self.previous_shifts_input.text().split(',')

        # Convert previous shifts input
        previous_shifts = [datetime.strptime(shift.strip(), "%d/%m/%Y") for shift in previous_shifts_input if shift]

        # Schedule shifts
        schedule = schedule_shifts(work_periods, holidays, jobs, self.workers, previous_shifts)

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
