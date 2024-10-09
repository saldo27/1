from cli import run_cli
import sys
from PySide6.QtWidgets import QApplication
from gui import MainWindow
from worker import Worker
from shift_scheduler import schedule_shifts, prepare_breakdown, export_breakdown

if __name__ == "__main__":
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    else:
        print("QApplication instance already exists.")

    window = MainWindow()
    window.show()

    # User input for the required parameters
    work_periods = input("Enter work periods (e.g., 01/10/2024-31/10/2024, separated by commas): ").split(',')
    holidays = input("Enter holidays (e.g., 09/10/2024, separated by commas): ").split(',')
    jobs = input("Enter workstations (e.g., A, B, C, separated by commas): ").split(',')
    min_distance = int(input("Enter minimum distance between work shifts (in days): "))
    max_shifts_per_week = int(input("Enter maximum shifts that can be assigned per week: "))
    num_workers = int(input("Enter number of available workers: "))

    # Example worker data, replace with actual data as needed
    workers = [
        Worker.from_user_input(
            identification=f"W{i+1}",
            working_dates="01/10/2024-15/10/2024,20/10/2024-31/10/2024",
            percentage_shifts=100.0,
            group='1',
            position_incompatibility="",
            group_incompatibility="",
            obligatory_coverage="",
            unavailable_dates=""
        ) for i in range(num_workers)
    ]

    # Schedule shifts
    schedule = schedule_shifts(work_periods, holidays, jobs, workers, min_distance, max_shifts_per_week)
    breakdown = prepare_breakdown(schedule)
    export_breakdown(breakdown)

    sys.exit(app.exec())
