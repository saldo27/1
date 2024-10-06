from models import Shift
from datetime import timedelta, datetime
import random
from collections import defaultdict
from icalendar import Calendar, Event
import heapq

class Worker:
    def __init__(self, identification, work_dates, percentage, group, incompatible_job, group_incompatibility, obligatory_coverage, day_off):
        self.identification = identification
        self.work_dates = work_dates
        self.percentage_shifts = float(percentage) if percentage else 100.0
        self.group = group
        self.incompatible_job = incompatible_job
        self.group_incompatibility = group_incompatibility
        self.obligatory_coverage = obligatory_coverage
        self.day_off = day_off

def calculate_shift_quota(workers, total_shifts, total_weeks):
    total_percentage = sum(worker.percentage_shifts for worker in workers)
    for worker in workers:
        worker.shift_quota = (worker.percentage_shifts / total_percentage) * total_shifts
        worker.weekly_shift_quota = worker.shift_quota / total_weeks

def generate_date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def is_weekend(date):
    return date.weekday() >= 5  # 5 for Saturday and 6 for Sunday

def is_holiday(date_str, holidays_set):
    return date_str in holidays_set

def can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set, weekly_tracker, job, job_count):
    if worker.identification in last_shift_date:
        last_date = last_shift_date[worker.identification]
        if last_date and (date - last_date).days < 3:
            return False
    
    if is_weekend(date) or is_holiday(date.strftime("%d/%m/%Y"), holidays_set):
        if weekend_tracker[worker.identification] >= 3:
            return False

    week_number = date.isocalendar()[1]
    if weekly_tracker[worker.identification][week_number] >= worker.weekly_shift_quota:
        return False
    
    if job in job_count[worker.identification] and job_count[worker.identification][job] > 0:
        return False
    if date.weekday() == last_date.weekday():
        return False

    return True
    
from PyQt5.QtWidgets import QMainWindow, QApplication
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setGeometry(100, 100, 800, 600)  # Set a default geometry within allowable limits
        self.setMinimumSize(800, 600)         # Set minimum size
        self.setMaximumSize(1920, 1080)       # Set maximum size (optional)
        self.setWindowTitle('MainWindowClassWindow')
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    sys.exit(app.exec_())

def export_to_ical(schedule_text):
    cal = Calendar()
    cal.add('prodid', '-//Shift Scheduler//')
    cal.add('version', '2.0')

    for line in schedule_text.split('\n'):
        if line.startswith("Job"):
            job = line.split()[1][:-1]
        elif line.strip():
            date_str, worker_id = line.strip().split(': ')
            date = datetime.strptime(date_str, "%d/%m/%Y")
            event = Event()
            event.add('summary', f"{job} shift & {worker_id}")
            event.add('dtstart', date)
            event.add('dtend', date + timedelta(days=1))
            event.add('description', f"Worker ID: {worker_id}")
            cal.add_component(event)

    with open('schedule.ics', 'wb') as f:
        f.write(cal.to_ical())

def generate_worker_report(schedule_text):
    report = ""
    worker_shifts = {}

    for line in schedule_text.split('\n'):
        if line.startswith("Job"):
            job = line.split()[1][:-1]
        elif line.strip():
            date_str, worker_id = line.strip().split(': ')
            if worker_id not in worker_shifts:
                worker_shifts[worker_id] = []
            worker_shifts[worker_id].append(f"{job} on {date_str}")

    for worker_id, shifts in worker_shifts.items():
        report += f"Worker ID: {worker_id}\n"
        for shift in shifts:
            report += f"  {shift}\n"
        report += "\n"

    return report
