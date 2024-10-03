from datetime import datetime, timedelta
import random
from collections import defaultdict
from icalendar import Calendar, Event

def generate_date_range(start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)

def is_weekend(date):
    return date.weekday() >= 4  # Friday, Saturday, or Sunday

def is_holiday(date_str, holidays):
    return date_str in holidays

def can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set, weekly_tracker):
    if worker.identification in last_shift_date:
        last_date = last_shift_date[worker.identification]
        if last_date and (date - last_date).days < 3:
            return False
    if is_weekend(date) or is_holiday(date.strftime("%d/%m/%Y"), holidays_set):
        if weekend_tracker[worker.identification] >= 3:  # No 3 consecutive weekends
            return False
    # Check weekly shift distribution
    week_number = date.isocalendar()[1]
    if weekly_tracker[worker.identification][week_number] >= worker.weekly_shift_quota:
        return False
    return True

def calculate_shift_quota(workers, total_shifts, total_weeks):
    total_percentage = sum(worker.percentage_shifts for worker in workers)
    for worker in workers:
        worker.shift_quota = (worker.percentage_shifts / total_percentage) * total_shifts
        worker.weekly_shift_quota = worker.shift_quota / total_weeks

def schedule_shifts(work_periods, holidays, jobs, workers, previous_shifts=[]):
    schedule = {job: {} for job in jobs}
    holidays_set = set(holidays)

    weekend_tracker = {worker.identification: 0 for worker in workers}
    past_date = datetime.strptime("01/01/1900", "%d/%m/%Y")
    last_shift_date = {worker.identification: past_date for worker in workers}
    job_count = {worker.identification: {job: 0 for job in jobs} for worker in workers}
    weekly_tracker = defaultdict(lambda: defaultdict(int))

    total_days = sum((datetime.strptime(period.split('-')[1].strip(), "%d/%m/%Y") - datetime.strptime(period.split('-')[0].strip(), "%d/%m/%Y")).days + 1 for period in work_periods)
    jobs_per_day = len(jobs)
    total_shifts = total_days * jobs_per_day
    total_weeks = (total_days // 7) + 1
    calculate_shift_quota(workers, total_shifts, total_weeks)

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

                # Assign mandatory workers first
                mandatory_workers = [worker for worker in workers if date_str in worker.mandatory_guard_duty and job not in worker.position_incompatibility]
                if mandatory_workers:
                    worker = mandatory_workers[0]
                else:
                    # Filter out unavailable jobs
                    available_workers = [worker for worker in workers if worker.shift_quota > 0 and job not in worker.position_incompatibility and date_str not in worker.unavailable_dates]
                    available_workers = [worker for worker in available_workers if can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set, weekly_tracker) and worker.identification not in daily_assigned_workers]

                    if not available_workers:
                        # Fill remaining shifts with any available worker
                        available_workers = [worker for worker in workers if job not in worker.position_incompatibility and date_str not in worker.unavailable_dates]
                        if not available_workers:
                            print(f"No available workers for job {job} on {date_str}")
                            continue

                        worker = random.choice(available_workers)
                    else:
                        # Select the worker who has the least number of shifts for this job and has the maximum gap from their last shift
                        worker = min(available_workers, key=lambda w: (job_count[w.identification][job], date - last_shift_date[w.identification]))
                        last_shift_date[worker.identification] = date

                schedule[job][date_str] = worker.identification
                daily_assigned_workers.add(worker.identification)
                job_count[worker.identification][job] += 1
                weekly_tracker[worker.identification][date.isocalendar()[1]] += 1

                if is_weekend_day:
                    weekend_tracker[worker.identification] += 1

            for worker_id in daily_assigned_workers:
                worker = next(w for w in workers if w.identification == worker_id)
                worker.shift_quota -= 1

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
