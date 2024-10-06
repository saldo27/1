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
        self.obligatory_coverage = obligatory_coverage  # Ensure this attribute is initialized
        self.day_off = day_off

def schedule_shifts(work_periods, holidays, jobs, workers, previous_shifts=[]):
    schedule = {job: {} for job in jobs}
    holidays_set = set(holidays)
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
                # Assign mandatory guard duty shifts first
                for worker in workers:
                    if date.strftime("%d/%m/%Y") in worker.obligatory_coverage:
                        assign_worker_to_shift(worker, date, job, schedule, last_shift_date, weekend_tracker, weekly_tracker, job_count, holidays_set)
                        break
                else:
                    assigned = False
                    while not assigned:
                        available_workers = [worker for worker in workers if worker.shift_quota > 0 and can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set, weekly_tracker, job, job_count)]
                        if not available_workers:
                            available_workers = [worker for worker in workers if worker.shift_quota > 0 and can_work_on_date(worker, date, last_shift_date, weekend_tracker, holidays_set, weekly_tracker, job, job_count, override=True)]
                            if available_workers:
                                worker = available_workers[0]
                                if propose_exception(worker, date, "override constraints"):
                                    break
                                else:
                                    # Stop the allocation process until confirmation is received
                                    print(f"Shift allocation stopped for {job} on {date}. Awaiting confirmation for proposed exception.")
                                    return schedule
                            else:
                                logging.error(f"No available workers for job {job} on {date.strftime('%d/%m/%Y')}.")
                                continue
                        worker = min(available_workers, key=lambda w: (job_count[w.identification][job], (date - last_shift_date[w.identification]).days * -1, w.shift_quota, w.percentage_shifts))
                        last_shift_date[worker.identification] = date
                        schedule[job][date.strftime("%d/%m/%Y")] = worker.identification
                        job_count[worker.identification][job] += 1
                        weekly_tracker[worker.identification][date.isocalendar()[1]] += 1
                        if is_weekend(date) or is_holiday(date.strftime("%d/%m/%Y"), holidays_set):
                            weekend_tracker[worker.identification] += 1
                        worker.shift_quota -= 1
                        assigned = True

    return schedule

def assign_worker_to_shift(worker, date, job, schedule, last_shift_date, weekend_tracker, weekly_tracker, job_count, holidays_set):
    last_shift_date[worker.identification] = date
    schedule[job][date.strftime("%d/%m/%Y")] = worker.identification
    job_count[worker.identification][job] += 1
    weekly_tracker[worker.identification][date.isocalendar()[1]] += 1
    if is_weekend(date) or is_holiday(date.strftime("%d/%m/%Y"), holidays_set):
        weekend_tracker[worker.identification] += 1
    worker.shift_quota -= 1
