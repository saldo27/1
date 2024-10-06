from models import Shift
from datetime import timedelta, datetime
import random
from collections import defaultdict
from icalendar import Calendar, Event
import heapq

class Worker:
    def __init__(self, id, work_dates, percentage, group, incompatible_job, group_incompatibility, obligatory_coverage, day_off):
        self.id = id
        self.work_dates = work_dates
        self.percentage_shifts = float(percentage) if percentage else 100.0
        self.group = group
        self.incompatible_job = incompatible_job
        self.group_incompatibility = group_incompatibility
        self.obligatory_coverage = obligatory_coverage
        self.day_off = day_off

def calculate_shift_quota(workers, total_shifts, total_weeks):
    total_percentage = sum(worker.percentage_shifts for worker in workers)
    if total_percentage == 0:
        raise ValueError("Total percentage of shifts is zero, cannot distribute shifts.")
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

def can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set, weekly_tracker, job, job_count, last_job_date, last_day_of_week_date):
    if worker.id in last_shift_date:
        last_date = last_shift_date[worker.id]
        if last_date and (date - last_date).days < 4:
            return False
    
    if is_weekend(date) or is_holiday(date.strftime("%d/%m/%Y"), holidays_set):
        if weekend_tracker[worker.id] >= 3:
            return False

    week_number = date.isocalendar()[1]
    if weekly_tracker[worker.id][week_number] >= worker.weekly_shift_quota:
        return False
    
    if job in job_count[worker.id] and job_count[worker.id][job] > 0:
        return False

    if date.weekday() == last_day_of_week_date[worker.id].weekday():
        return False

    if job == last_job_date[worker.id]:
        return False

    return True

def schedule_shifts(work_periods, holidays, jobs, workers, previous_shifts=[]):
    schedule = {job: {} for job in jobs}
    holidays_set = set(holidays)
    weekend_tracker = {worker.id: 0 for worker in workers}
    past_date = datetime.strptime("01/01/1900", "%d/%m/%Y")
    last_shift_date = {worker.id: past_date for worker in workers}
    last_day_of_week_date = {worker.id: past_date for worker in workers}
    last_job_date = {worker.id: "" for worker in workers}
    job_count = {worker.id: {job: 0 for job in jobs} for worker in workers}
    weekly_tracker = defaultdict(lambda: defaultdict(int))
    total_days = sum((datetime.strptime(period.split('-')[1].strip(), "%d/%m/%Y") - datetime.strptime(period.split('-')[0].strip(), "%d/%m/%Y")).days + 1 for period in work_periods)
    jobs_per_day = len(jobs)
    total_shifts = total_days * jobs_per_day
    total_weeks = (total_days // 7) + 1
    calculate_shift_quota(workers, total_shifts, total_weeks)

    pq = [(datetime.strptime("01/01/1900", "%d/%m/%Y"), worker) for worker in workers]
    heapq.heapify(pq)

    for period in work_periods:
        start_date = datetime.strptime(period.split('-')[0].strip(), "%d/%m/%Y")
        end_date = datetime.strptime(period.split('-')[1].strip(), "%d/%m/%Y")
        for date in generate_date_range(start_date, end_date):
            date_str = date.strftime("%d/%m/%Y")
            is_weekend_day = is_weekend(date) or is_holiday(date_str, holidays_set)
            daily_assigned_workers = set()
            for job in jobs:
                if date_str not in schedule[job]:
                    schedule[job][date_str] = {}
                mandatory_workers = [worker for worker in workers if date_str in worker.mandatory_guard_duty and job not in worker.position_incompatibility]
                if mandatory_workers:
                    worker = mandatory_workers[0]
                else:
                    available_workers = [worker for worker in workers if worker.shift_quota > 0 and job not in worker.position_incompatibility and date_str not in worker.unavailable_dates]
                    available_workers = [worker for worker in available_workers if can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set, weekly_tracker, job, job_count, last_job_date, last_day_of_week_date) and worker.id not in daily_assigned_workers]
                    if not available_workers:
                        available_workers = [worker for worker in workers if job not in worker.position_incompatibility and date_str not in worker.unavailable_dates]
                        if not available_workers:
                            print(f"No available workers for job {job} on {date_str}")
                            continue
                        worker = random.choice(available_workers)
                    else:
                        worker = min(available_workers, key=lambda w: (job_count[w.id][job], date - last_shift_date[w.id]))
                        last_shift_date[worker.id] = date
                        last_day_of_week_date[worker.id] = date
                        last_job_date[worker.id] = job
                schedule[job][date_str] = worker.id
                daily_assigned_workers.add(worker.id)
                job_count[worker.id][job] += 1
                weekly_tracker[worker.id][date.isocalendar()[1]] += 1
                if is_weekend_day:
                    weekend_tracker[worker.id] += 1
            for worker_id in daily_assigned_workers:
                worker = next(w for w in workers if w.id == worker_id)
                worker.shift_quota -= 1
                heapq.heappush(pq, (date + timedelta(days=4), worker))
    return schedule

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
