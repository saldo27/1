from datetime import datetime, timedelta
import random

def generate_date_range(start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)

def is_weekend(date):
    return date.weekday() >= 4  # Friday, Saturday, or Sunday

def is_holiday(date_str, holidays):
    return date_str in holidays

def can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set):
    if worker.worker_id in last_shift_date:
        last_date = last_shift_date[worker.worker_id]
        if last_date and (date - last_date).days < 3:
            return False
    if is_weekend(date) or is_holiday(date.strftime("%d/%m/%Y"), holidays_set):
        if weekend_tracker[worker.worker_id] >= 3:  # No 3 consecutive weekends
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

            daily_assigned_workers = set()
            for job in jobs:
                if date_str not in schedule[job]:
                    schedule[job][date_str] = {}

                mandatory_workers = [worker for worker in workers if date_str in worker.mandatory_shifts and job not in worker.job_incompatibilities]
                if mandatory_workers:
                    worker = mandatory_workers[0]
                else:
                    available_workers = [worker for worker in workers if worker.shift_quota > 0 and job not in worker.job_incompatibilities and date_str not in worker.unavailable_shifts]
                    available_workers = [worker for worker in available_workers if can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set) and worker.worker_id not in daily_assigned_workers]

                    if not available_workers:
                        print(f"No available workers for job {job} on {date_str}")
                        continue

                    # Select the worker who has the maximum gap from their last shift
                    worker = max(available_workers, key=lambda w: (date - last_shift_date.get(w.worker_id, date - timedelta(days=1000))).days)

                schedule[job][date_str] = worker.worker_id
                daily_assigned_workers.add(worker.worker_id)

                if is_weekend_day:
                    weekend_tracker[worker.worker_id] += 1
                last_shift_date[worker.worker_id] = date

            for worker_id in daily_assigned_workers:
                worker = next(w for w in workers if w.worker_id == worker_id)
                worker.shift_quota -= 1

    return schedule
