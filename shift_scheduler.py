import logging
import re
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
        self.monthly_shift_quota = 0  # Initialize monthly_shift_quota

def calculate_shift_quota(workers, total_shifts, total_days):
    if total_days == 0 or total_shifts == 0:
        logging.error("Total days or total shifts cannot be zero.")
        return

    total_percentage = sum(worker.percentage_shifts for worker in workers)
    total_months = max(total_days / 30, 1)  # Ensure total_months is at least 1
    for worker in workers:
        monthly_shifts = (worker.percentage_shifts / total_percentage) * (total_shifts / total_months)
        worker.monthly_shift_quota = max(monthly_shifts, 0)
        worker.shift_quota = max((worker.percentage_shifts / total_percentage) * (total_days * total_shifts), 0)
        worker.weekly_shift_quota = max(worker.shift_quota / total_days * 7, 0)
def generate_date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def is_weekend(date):
    return date.weekday() >= 5

def is_holiday(date_str, holidays_set):
    return date_str in holidays_set

def sanitize_date(date_str):
    return re.sub(r'[^0-9/]', '', date_str).strip()

def can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set, weekly_tracker, job, job_count, monthly_tracker, override=False):
    if isinstance(date, str) and date:
        date = datetime.strptime(sanitize_date(date), "%d/%m/%Y")

    if date in [datetime.strptime(sanitize_date(day), "%d/%m/%Y") for day in worker.unavailable_dates if day]:
        logging.debug(f"Worker {worker.identification} cannot work on {date} due to unavailability.")
        return False

    if not override:
        if worker.identification in last_shift_date:
            last_date = last_shift_date[worker.identification]
            if isinstance(last_date, str) and last_date:
                last_date = datetime.strptime(sanitize_date(last_date), "%d/%m/%Y")
            if last_date:
                if (date - last_date).days < 4:
                    logging.debug(f"Worker {worker.identification} cannot work on {date} due to recent shift on {last_date}.")
                    return False
                if last_date.date() == date.date():
                    logging.debug(f"Worker {worker.identification} cannot work on {date} because they already have a shift on this day.")
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
    
def propose_exception(worker, date, reason):
    logging.info(f"Proposing exception for Worker {worker.identification} on {date} due to {reason}.")
    confirmation = input(f"Confirm exception for Worker {worker.identification} on {date} (yes/no): ")
    return confirmation.lower() == 'yes'

def schedule_shifts(work_periods, holidays, jobs, workers, previous_shifts=[]):
    logging.debug(f"Workers: {workers}")
    logging.debug(f"Work Periods: {work_periods}")
    logging.debug(f"Holidays: {holidays}")
    logging.debug(f"Jobs: {jobs}")

    schedule = {job: {} for job in jobs}
    holidays_set = set(holidays)
    weekend_tracker = {worker.identification: 0 for worker in workers}
    past_date = datetime.strptime("01/01/1900", "%d/%m/%Y")
    last_shift_date = {worker.identification: past_date for worker in workers}
    job_count = {worker.identification: {job: 0 for job in jobs} for worker in workers}
    weekly_tracker = defaultdict(lambda: defaultdict(int))
    monthly_tracker = defaultdict(lambda: defaultdict(int))

    valid_work_periods = []
    for period in work_periods:
        try:
            start_date_str, end_date_str = period.split('-')
            start_date = datetime.strptime(sanitize_date(start_date_str), "%d/%m/%Y")
            end_date = datetime.strptime(sanitize_date(end_date_str), "%d/%m/%Y")
            valid_work_periods.append((start_date, end_date))
        except ValueError as e:
            logging.error(f"Invalid period '{period}': {e}")

    total_days = sum((end_date - start_date).days + 1 for start_date, end_date in valid_work_periods)
    jobs_per_day = len(jobs)
    total_shifts = total_days * jobs_per_day
    calculate_shift_quota(workers, jobs_per_day, total_days)

    for worker in workers:
        for date_str in worker.obligatory_coverage:
            sanitized_date_str = sanitize_date(date_str)
            if sanitized_date_str:
                date = datetime.strptime(sanitized_date_str, "%d/%m/%Y")
                for job in jobs:
                    if worker.identification not in schedule[job].get(date.strftime("%d/%m/%Y"), ''):
                        assign_worker_to_shift(worker, date, job, schedule, last_shift_date, weekend_tracker, weekly_tracker, job_count, holidays_set, monthly_tracker)

    for start_date, end_date in valid_work_periods:
        for date in generate_date_range(start_date, end_date):
            date_str = date.strftime("%d/%m/%Y")
            for job in jobs:
                logging.debug(f"Processing job '{job}' on date {date_str}")

                assigned = False
                while not assigned:
                    available_workers = [worker for worker in workers if worker.shift_quota > 0 and worker.monthly_shift_quota > 0 and can_work_on_date(worker, date_str, last_shift_date, weekend_tracker, holidays_set, weekly_tracker, job, job_count, monthly_tracker)]
                    if not available_workers:
                        # Consider override workers if no regular workers are available
                        available_workers = [worker for worker in workers if worker.shift_quota > 0 and worker.monthly_shift_quota > 0 and can_work_on_date(worker, date_str, last_shift_date, weekend_tracker, holidays_set, weekly_tracker, job, job_count, monthly_tracker, override=True)]
                        if available_workers:
                            worker = available_workers[0]
                            if propose_exception(worker, date_str, "override constraints"):
                                assign_worker_to_shift(worker, date, job, schedule, last_shift_date, weekend_tracker, weekly_tracker, job_count, holidays_set, monthly_tracker)
                                assigned = True
                            else:
                                logging.info(f"Shift allocation stopped for {job} on {date_str}. Awaiting confirmation for proposed exception.")
                                assigned = True  # Exit the loop as no shift can be assigned without exception approval
                        else:
                            logging.error(f"No available workers for job {job} on {date_str}.")
                            assigned = True  # Exit the loop as no workers are available
                    else:
                        worker = min(available_workers, key=lambda w: (job_count[w.identification][job], (date - last_shift_date[w.identification]).days * -1, w.shift_quota, w.percentage_shifts))
                        assign_worker_to_shift(worker, date, job, schedule, last_shift_date, weekend_tracker, weekly_tracker, job_count, holidays_set, monthly_tracker)
                        assigned = True

    return schedule

def assign_worker_to_shift(worker, date, job, schedule, last_shift_date, weekend_tracker, weekly_tracker, job_count, holidays_set, monthly_tracker):
    logging.debug(f"Assigning worker {worker.identification} to job {job} on date {date.strftime('%d/%m/%Y')}")
    
    last_shift_date[worker.identification] = date
    schedule[job][date.strftime("%d/%m/%Y")] = worker.identification
    job_count[worker.identification][job] += 1
    weekly_tracker[worker.identification][date.isocalendar()[1]] += 1
    monthly_tracker[worker.identification][date.month] += 1
    
    if is_weekend(date) or is_holiday(date.strftime("%d/%m/%Y"), holidays_set):
        weekend_tracker[worker.identification] += 1
    
    worker.shift_quota = max(worker.shift_quota - 1, 0)
    worker.monthly_shift_quota = max(worker.monthly_shift_quota - 1, 0)
    
    logging.debug(f"Updated last_shift_date: {last_shift_date}")
    logging.debug(f"Updated job_count: {job_count}")
    logging.debug(f"Updated weekly_tracker: {weekly_tracker}")
    logging.debug(f"Updated monthly_tracker: {monthly_tracker}")
    logging.debug(f"Updated weekend_tracker: {weekend_tracker}")
    logging.debug(f"Worker {worker.identification} shift_quota: {worker.shift_quota}")
    logging.debug(f"Worker {worker.identification} monthly_shift_quota: {worker.monthly_shift_quota}")
