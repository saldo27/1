import logging
from datetime import timedelta, datetime
from collections import defaultdict
from models import Shift
from icalendar import Calendar, Event
import heapq

logging.basicConfig(level=logging.DEBUG)

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
        self.has_exception = False  # Track if the worker has an accepted exception

def calculate_shift_quota(workers, total_shifts, total_weeks):
    total_percentage = sum(worker.percentage_shifts for worker in workers)
    for worker in workers:
        worker.shift_quota = (worker.percentage_shifts / total_percentage) * total_shifts
        worker.weekly_shift_quota = worker.shift_quota / total_weeks

def generate_date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def is_weekend(date):
    return date.weekday() >= 5

def is_holiday(date_str, holidays_set):
    return date_str in holidays_set

def can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set, weekly_tracker, job, job_count, override=False):
    if not override:
        if worker.identification in last_shift_date:
            last_date = last_shift_date[worker.identification]
            if last_date and (date - last_date).days < 3:
                logging.debug(f"Worker {worker.identification} cannot work on {date} due to recent shift on {last_date}.")
                return False

        if is_weekend(date) or is_holiday(date.strftime("%d/%m/%Y"), holidays_set):
            if weekend_tracker[worker.identification] >= 4:
                logging.debug(f"Worker {worker.identification} cannot work on {date} due to weekend/holiday limit.")
                return False

        week_number = date.isocalendar()[1]
        if weekly_tracker[worker.identification][week_number] >= 2:
            logging.debug(f"Worker {worker.identification} cannot work on {date} due to weekly quota limit.")
            return False

        if job in job_count[worker.identification] and job_count[worker.identification][job] > 0 and (date - last_shift_date[worker.identification]).days == 1:
            logging.debug(f"Worker {worker.identification} cannot work on {date} due to job repetition limit.")
            return False

    return True

def propose_exception(worker, date, reason, last_shift_date):
    # Check if the worker has worked on the 2 days before or the 2 days after
    for offset in [-2, -1, 1, 2]:
        check_date = date + timedelta(days=offset)
        if last_shift_date[worker.identification] == check_date:
            logging.info(f"Cannot propose exception for Worker {worker.identification} on {date} as they have worked on {check_date}.")
            return False
    if worker.has_exception:
        logging.info(f"Worker {worker.identification} already has an accepted exception and cannot be proposed for another.")
        return False
    logging.info(f"Proposing exception for Worker {worker.identification} on {date} due to {reason}.")
    confirmation = input(f"Confirm exception for Worker {worker.identification} on {date} (yes/no): ")
    if confirmation.lower() == 'yes':
        worker.has_exception = True
        return True
    return False

def schedule_shifts(work_periods, holidays, jobs, workers, previous_shifts=[]):
    schedule = {job: {} for job in jobs}
    holidays_set = set(holidays) if holidays else set()
    weekend_tracker = {worker.identification: 0 for worker in workers}
    past_date = datetime.strptime("01/01/1900", "%d/%m/%Y")
    last_shift_date = {worker.identification: past_date for worker in workers}
    job_count = {worker.identification: {job: 0 for job in jobs} for worker in workers}
    weekly_tracker = defaultdict(lambda: defaultdict(int))

    valid_work_periods = []
    for period in work_periods:
        try:
            start_date_str, end_date_str = period.split('-')
            start_date = datetime.strptime(start_date_str.strip(), "%d/%m/%Y")
            end_date = datetime.strptime(end_date_str.strip(), "%d/%m/%Y")
            valid_work_periods.append((start_date, end_date))
        except ValueError as e:
            print(f"Invalid period '{period}': {e}")

    total_days = sum((end_date - start_date).days + 1 for start_date, end_date in valid_work_periods)
    jobs_per_day = len(jobs)
    total_shifts = total_days * jobs_per_day
    total_weeks = (total_days // 7) + 1
    calculate_shift_quota(workers, total_shifts, total_weeks)

    for start_date, end_date in valid_work_periods:
        for date in generate_date_range(start_date, end_date):
            for job in jobs:
                assigned = False
                while not assigned:
                    available_workers = [worker for worker in workers if worker.shift_quota > 0 and can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set, weekly_tracker, job, job_count)]
                    if not available_workers:
                        available_workers = [worker for worker in workers if worker.shift_quota > 0 and can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set, weekly_tracker, job, job_count, override=True)]
                        if available_workers:
                            worker = available_workers[0]
                            if propose_exception(worker, date, "override constraints", last_shift_date):
                                assign_worker_to_shift(worker, date, job, schedule, last_shift_date, weekend_tracker, weekly_tracker, job_count, holidays_set)
                            else:
                                alternative_worker = find_alternative_worker(date, job, workers, last_shift_date, weekend_tracker, holidays_set, weekly_tracker, job_count)
                                if alternative_worker:
                                    logging.info(f"Alternative worker {alternative_worker.identification} assigned for job {job} on {date}.")
                                    assign_worker_to_shift(alternative_worker, date, job, schedule, last_shift_date, weekend_tracker, weekly_tracker, job_count, holidays_set)
                                else:
                                    logging.error(f"No alternative workers available for job {job} on {date.strftime('%d/%m/%Y')}.")
                                    return schedule
                        else:
                            logging.error(f"No available workers for job {job} on {date.strftime('%d/%m/%Y')}.")
                            continue
                    else:
                        worker = min(available_workers, key=lambda w: (job_count[w.identification][job], (date - last_shift_date[w.identification]).days * -1, w.shift_quota, w.percentage_shifts))
                        assign_worker_to_shift(worker, date, job, schedule, last_shift_date, weekend_tracker, weekly_tracker, job_count, holidays_set)
                    assigned = True

    return schedule

def find_alternative_worker(date, job, workers, last_shift_date, weekend_tracker, holidays_set, weekly_tracker, job_count):
    for worker in workers:
        if worker.shift_quota > 0 and can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set, weekly_tracker, job, job_count, override=True):
            return worker
    return None

def assign_worker_to_shift(worker, date, job, schedule, last_shift_date, weekend_tracker, weekly_tracker, job_count, holidays_set):
    last_shift_date[worker.identification] = date
    schedule[job][date.strftime("%d/%m/%Y")] = worker.identification
    job_count[worker.identification][job] += 1
    weekly_tracker[worker.identification][date.isocalendar()[1]] += 1
    if is_weekend(date) or is_holiday(date.strftime("%d/%m/%Y"), holidays_set):
        weekend_tracker[worker.identification] += 1
    worker.shift_quota -= 1
