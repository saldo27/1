from datetime import datetime, timedelta
import random

def generate_date_range(start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)

def is_weekend(date):
    return date.weekday() >= 4

def is_holiday(date_str, holidays):
    return date_str in holidays

def can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set):
    if worker.worker_id in last_shift_date:
        last_date = last_shift_date[worker.worker_id]
        if last_date and (date - last_date).days < 3:
            return False
    if is_weekend(date) or is_holiday(date.strftime("%d/%m/%Y"), holidays_set):
        if weekend_tracker[worker.worker_id] >= 3:
            return False
    return True

def calculate_shift_quota(workers, total_days):
    total_percentage = sum(worker.work_percentage for worker in workers)
    for worker in workers:
        worker.shift_quota = (worker.work_percentage / total_percentage) * total_days

def schedule_shifts(work_periods, holidays, jobs, workers, previous_shifts=[]):
    schedule = {job: {} for job in jobs}
    holidays_set = set(holidays)

    weekend_tracker = {worker.worker_id: 0 for worker in workers}
    last_shift_date = {worker.worker_id: None for worker in workers}

    total_days = sum((datetime.strptime(period['end'], "%d/%m/%Y") - datetime.strptime(period['start'], "%d/%m/%Y")).days + 1 for period in work_periods)
    calculate_shift_quota(workers, total_days)

    for period in work_periods:
        start_date = datetime.strptime(period['start'], "%d/%m/%Y")
        end_date = datetime.strptime(period['end'], "%d/%m/%Y")
        for date in generate_date_range(start_date, end_date):
            date_str = date.strftime("%d/%m/%Y")
            is_weekend_day = is_weekend(date) or is_holiday(date_str, holidays_set)

            for job in jobs:
                daily_schedule = {}
                if date_str in schedule[job]:
                    continue

                mandatory_workers = [worker for worker in workers if date_str in worker.mandatory_shifts and job not in worker.job_incompatibilities]
                if mandatory_workers:
                    worker = mandatory_workers[0]
                else:
                    available_workers = [worker for worker in workers if worker.shift_quota > 0 and job not in worker.job_incompatibilities and date_str not in worker.unavailable_shifts]

                    available_workers = [worker for worker in available_workers if can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set)]

                    if not available_workers:
                        print(f"No available workers for job {job} on {date_str}")
                        continue

                    worker = random.choice(available_workers)

                daily_schedule[job] = worker.worker_id
                worker.shift_quota -= 1
                schedule[job][date_str] = daily_schedule

                if is_weekend_day:
                    weekend_tracker[worker.worker_id] += 1
                last_shift_date[worker.worker_id] = date

    return schedule
