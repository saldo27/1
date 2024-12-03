import csv
import logging
from datetime import datetime, timedelta
from collections import defaultdict

logging.basicConfig(level=logging.DEBUG)

class Worker:
    def __init__(self, identification, work_dates=None, percentage=100.0, group='1', incompatible_job=None, group_incompatibility=None, obligatory_coverage=None, unavailable_dates=None):
        self.identification = identification
        self.work_dates = work_dates if work_dates else []
        self.percentage_shifts = float(percentage) if percentage else 100.0
        self.group = group if group else '1'
        self.incompatible_job = incompatible_job if incompatible_job else []
        self.group_incompatibility = group_incompatibility if group_incompatibility else []
        self.obligatory_coverage = obligatory_coverage if obligatory_coverage else []
        self.unavailable_dates = unavailable_dates if unavailable_dates else []

def import_workers_from_csv(filename):
    workers = []
    with open(filename, mode='r') as file:
        reader = csv.DictReader(file)
        logging.debug(f"CSV Headers: {reader.fieldnames}")
        for row in reader:
            logging.debug(f"CSV Row: {row}")
            work_dates = [(datetime.strptime(start.strip(), "%d/%m/%Y"), datetime.strptime(end.strip(), "%d/%m/%Y")) 
                          for period in row['Work Dates'].split(',') if '-' in period for start, end in [period.split('-')]]
            worker = Worker(
                identification=row['Identification'],
                work_dates=work_dates,
                percentage=float(row['Percentage']) if row['Percentage'] else 100.0,
                group=row['Group'],
                incompatible_job=row['Incompatible Job'].split(','),
                group_incompatibility=row['Group Incompatibility'].split(','),
                obligatory_coverage=row['Obligatory Coverage'].split(','),
                unavailable_dates=row['Unavailable Dates'].split(',')
            )
            workers.append(worker)
    return workers

def calculate_shift_quota(workers, total_days, jobs_per_day):
    total_percentage = sum(worker.percentage_shifts for worker in workers)
    total_shifts = total_days * jobs_per_day
    for worker in workers:
        worker.shift_quota = (worker.percentage_shifts / 100) * (total_days * jobs_per_day) / (total_percentage / 100)
        worker.weekly_shift_quota = worker.shift_quota / ((total_days // 7) + 1)

def generate_date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def is_weekend(date):
    return date.weekday() >= 4

def is_holiday(date_str, holidays_set):
    if isinstance(date_str, str) and date_str:
        return date_str in holidays_set
    else:
        return False

def can_work_on_date(worker, date, last_shift_dates, weekend_tracker, holidays_set, weekly_tracker, job, job_count, min_distance, max_shifts_per_week, override=False, schedule=None, workers=None):
    if isinstance(date, str) and date:
        date = datetime.strptime(date.strip(), "%d/%m/%Y")

    if schedule and workers and not override:
        for job_schedule in schedule.values():
            if date.strftime("%d/%m/%Y") in job_schedule:
                assigned_worker_id = job_schedule[date.strftime("%d/%m/%Y")]
                assigned_worker = next((w for w in workers if w.identification == assigned_worker_id), None)
                if assigned_worker:
                    if any(group == assigned_worker.group for group in worker.group_incompatibility):
                        return False

    if date in [datetime.strptime(day.strip(), "%d/%m/%Y") for day in worker.unavailable_dates if day]:
        return False

    if not override:
        for start_date, end_date in worker.work_dates:
            if start_date <= date <= end_date:
                break
        else:
            return False

    if not override:
        adjusted_min_distance = min_distance * 100 / worker.percentage_shifts
        if last_shift_dates[worker.identification]:
            last_date = last_shift_dates[worker.identification][-1]
            days_diff = (date - last_date).days
            if days_diff < adjusted_min_distance:
                return False
            if days_diff in {7, 14, 21, 28}:
                return False
            if last_date.date() == date.date():
                return False

        if is_weekend(date) or is_holiday(date.strftime("%d/%m/%Y"), holidays_set):
            if weekend_tracker[worker.identification] >= 4:
                return False

        week_number = date.isocalendar()[1]
        if weekly_tracker[worker.identification][week_number] >= max_shifts_per_week:
            return False

        if job in job_count[worker.identification] and job_count[worker.identification][job] > 0 and (date - last_shift_dates[worker.identification][-1]).days == 1:
            return False

    return True

def assign_worker_to_shift(worker, date, job, schedule, last_shift_dates, weekend_tracker, weekly_tracker, job_count, holidays_set, min_distance, max_shifts_per_week, obligatory=False):
    last_shift_dates[worker.identification].append(date)
    schedule[job][date.strftime("%d/%m/%Y")] = worker.identification
    job_count[worker.identification][job] += 1
    weekly_tracker[worker.identification][date.isocalendar()[1]] += 1
    if is_weekend(date) or is_holiday(date.strftime("%d/%m/%Y"), holidays_set):
        weekend_tracker[worker.identification] += 1
    worker.shift_quota -= 1
    if obligatory:
        worker.obligatory_coverage_shifts[date] = job

def schedule_shifts(work_periods, holidays, jobs, workers, min_distance, max_shifts_per_week):
    logging.basicConfig(level=logging.DEBUG)

    # Log imported workers and their shifts
    for worker in workers:
        logging.debug(f"Worker ID: {worker.identification}, Work Dates: {worker.work_dates}")

    schedule = defaultdict(dict)
    weekly_tracker = defaultdict(lambda: defaultdict(int))

    for period in work_periods:
        start_date, end_date = map(lambda date: datetime.strptime(date.strip(), "%d/%m/%Y"), period.split('-'))
        for date in generate_date_range(start_date, end_date):
            if date.strftime("%d/%m/%Y") in holidays:
                continue
            for job in jobs:
                assigned = False
                for worker in workers:
                    if can_assign(worker, date, job, weekly_tracker, min_distance, max_shifts_per_week):
                        schedule[job][date.strftime("%d/%m/%Y")] = worker.identification
                        weekly_tracker[worker.identification][date.isocalendar()[1]] += 1
                        assigned = True
                        break
                if not assigned:
                    logging.warning(f"No available worker for Job {job} on {date.strftime('%d/%m/%Y')}")
    
    return schedule

def can_assign(worker, date, job, weekly_tracker, min_distance, max_shifts_per_week):
    if any(start <= date <= end for start, end in worker.work_dates):
        if weekly_tracker[worker.identification][date.isocalendar()[1]] >= max_shifts_per_week:
            return False
        for assigned_date in weekly_tracker[worker.identification].keys():
            if abs((date - assigned_date).days) < min_distance:
                return False
        return True
    return False

def prepare_breakdown(schedule):
    breakdown = defaultdict(list)
    for job, shifts in schedule.items():
        for date, worker_id in shifts.items():
            breakdown[worker_id].append((date, job))
    return breakdown

def export_breakdown(breakdown):
    output = ""
    for worker_id, shifts in breakdown.items():
        output += f"Worker {worker_id}:\n"
        for date, job in shifts:
            output += f"  {date}: {job}\n"
    return output
    
def export_schedule_to_csv(schedule, filename='shift_schedule.csv'):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Identification', 'Work Dates', 'Percentage', 'Group', 'Incompatible Job', 'Group Incompatibility', 'Obligatory Coverage', 'Unavailable Dates'])
        for job, shifts in schedule.items():
            for date, worker in shifts.items():
                writer.writerow([worker, '', '', '', '', '', '', ''])  # Adjust the values based on your data structure
                
if __name__ == "__main__":
    work_periods = input("Enter work periods (e.g., 01/10/2024-31/10/2024, separated by commas): ").split(',')
    holidays = input("Enter holidays (e.g., 09/10/2024, separated by commas): ").split(',')
    jobs = input("Enter workstations (e.g., A, B, C, separated by commas): ").split(',')
    min_distance = int(input("Enter minimum distance between work shifts (in days): "))
    max_shifts_per_week = int(input("Enter maximum shifts that can be assigned per week: "))
    num_workers = int(input("Enter number of available workers: "))

    workers = [Worker(f"W{i+1}") for i in range(num_workers)]

    schedule = schedule_shifts(work_periods, holidays, jobs, workers, min_distance, max_shifts_per_week)
    breakdown = prepare_breakdown(schedule)
    export_breakdown(breakdown)
