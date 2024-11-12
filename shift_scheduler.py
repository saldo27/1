import logging
logging.basicConfig(level=logging.DEBUG)
# Existing imports
from datetime import timedelta, datetime
from collections import defaultdict
import csv

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
        self.unavailable_dates = [date.strip() for date in (unavailable_dates or []) if date.strip()]
        
        # Debug print when worker is created
        if self.unavailable_dates:
            logging.debug(f"Created Worker {self.identification} with unavailable dates: {self.unavailable_dates}")
        
        # Standardize unavailable dates format
        if unavailable_dates:
            self.unavailable_dates = []
            for date in unavailable_dates:
                try:
                    # Convert to datetime and back to string to ensure consistent format
                    formatted_date = datetime.strptime(date.strip(), "%d/%m/%Y").strftime("%d/%m/%Y")
                    self.unavailable_dates.append(formatted_date)
                except ValueError as e:
                    logging.error(f"Invalid date format for {date}: {e}")
        else:
            self.unavailable_dates = []

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
    # 4 represents Friday, 5 represents Saturday, and 6 represents Sunday
    return date.weekday() >= 4

def is_holiday(date_str, holidays_set):
    if isinstance(date_str, str) and date_str:  # Check if date_str is a non-empty string
        return date_str in holidays_set
    else:
        return False

def can_work_on_date(worker, date_str, last_shift_dates, weekend_tracker, holidays_set, weekly_tracker, job, job_count, min_distance, max_shifts_per_week, override=False, schedule=None, workers=None):
    if isinstance(date_str, str) and date_str:  # Check if date is a non-empty string
        date = datetime.strptime(date_str.strip(), "%d/%m/%Y")  # Ensure date is a datetime object
        formatted_date_str = date.strftime("%d/%m/%Y")  # Standardize date format
        
        # Check unavailable dates first
        if date_str in worker.unavailable_dates:
        logging.debug(f"Worker {worker.identification} is unavailable on {date_str}")
        return False

    if date_str in [day.strip() for day in worker.unavailable_dates if day]:
        logging.debug(f"Worker {worker.identification} cannot work on {date_str} due to unavailability.")
        return False

    # Check if the date is within the worker's working dates range
    for start_date, end_date in worker.work_dates:
        if start_date <= date <= end_date:
            break
    else:
        logging.debug(f"Worker {worker.identification} cannot work on {date_str} because it is outside their working dates.")
        return False

    if not override:
        # Adjust the minimum distance for workers performing less than 100% of shifts
        adjusted_min_distance = min_distance * 100 / worker.percentage_shifts

        # Check across all workstations for the current worker
        if last_shift_dates[worker.identification]:
            last_date = last_shift_dates[worker.identification][-1]
            days_diff = (date - last_date).days
            logging.debug(f"Worker {worker.identification} last worked on {last_date.strftime('%d/%m/%Y')}, {days_diff} days ago.")
            if days_diff < adjusted_min_distance:
                logging.debug(f"Worker {worker.identification} cannot work on {date_str} due to adjusted minimum distance.")
                return False
            if days_diff in {7, 14, 21, 28}:
                logging.debug(f"Worker {worker.identification} cannot work on {date_str} due to 7, 14, 21 or 28 days constraint.")
                return False
            if last_date.date() == date.date():
                logging.debug(f"Worker {worker.identification} cannot work on {date_str} because they already have a shift on this day.")

        if is_weekend(date) or is_holiday(date_str, holidays_set):
            if weekend_tracker[worker.identification] >= 4:
                logging.debug(f"Worker {worker.identification} cannot work on {date_str} due to weekend/holiday limit.")
                return False

        week_number = date.isocalendar()[1]
        if weekly_tracker[worker.identification][week_number] >= max_shifts_per_week:
            logging.debug(f"Worker {worker.identification} cannot work on {date_str} due to weekly quota limit.")
            return False

        if job in job_count[worker.identification] and job_count[worker.identification][job] > 0 and (date - last_shift_dates[worker.identification][-1]).days == 1:
            logging.debug(f"Worker {worker.identification} cannot work on {date_str} due to job repetition limit.")
            return False

    return True

def assign_worker_to_shift(worker, date_str, job, schedule, last_shift_dates, weekend_tracker, weekly_tracker, job_count, holidays_set, min_distance, max_shifts_per_week):
    date = datetime.strptime(date_str.strip(), "%d/%m/%Y")
    logging.debug(f"Assigning worker {worker.identification} to job {job} on {date_str}")
    last_shift_dates[worker.identification].append(date)
    schedule[job][date_str] = worker.identification
    job_count[worker.identification][job] += 1
    weekly_tracker[worker.identification][date.isocalendar()[1]] += 1
    if is_weekend(date) or is_holiday(date_str, holidays_set):
        weekend_tracker[worker.identification] += 1
    worker.shift_quota -= 1
    logging.debug(f"Worker {worker.identification} assigned to job {job} on {date_str}. Updated schedule: {schedule[job][date_str]}")

def schedule_shifts(work_periods, holidays, jobs, workers, min_distance, max_shifts_per_week, previous_shifts=[]):
    logging.debug(f"Workers: {workers}")
    logging.debug(f"Work Periods: {work_periods}")
    logging.debug(f"Holidays: {holidays}")
    logging.debug(f"Jobs: {jobs}")

    # Print unavailable dates for each worker
    for worker in workers:
        print(f"Worker {worker.identification} unavailable dates: {worker.unavailable_dates}")

    schedule = {job: {} for job in jobs}
    holidays_set = set(holidays)
    weekend_tracker = {worker.identification: 0 for worker in workers}
    last_shift_dates = {worker.identification: [] for worker in workers}
    job_count = {worker.identification: {job: 0 for job in jobs} for worker in workers}
    weekly_tracker = defaultdict(lambda: defaultdict(int))
    last_assigned_job = {worker.identification: None for worker in workers}
    last_assigned_day = {worker.identification: None for worker in workers}
    day_rotation_tracker = {worker.identification: {i: False for i in range(7)} for worker in workers}

    valid_work_periods = []
    for period in work_periods:
        try:
            start_date_str, end_date_str = period.split('-')
            start_date = datetime.strptime(start_date_str.strip(), "%d/%m/%Y")
            end_date = datetime.strptime(end_date_str.strip(), "%d/%m/%Y")
            valid_work_periods.append((start_date, end_date))
        except ValueError as e:
            logging.error(f"Invalid period '{period}': {e}")

    total_days = sum((end_date - start_date).days + 1 for start_date, end_date in valid_work_periods)
    jobs_per_day = len(jobs)
    calculate_shift_quota(workers, total_days, jobs_per_day)

    # First, assign obligatory coverage shifts
    for worker in workers:
        if not worker.work_dates:
            worker.work_dates = valid_work_periods

        for date_str in worker.obligatory_coverage:
            if isinstance(date_str, str) and date_str.strip():
                logging.debug(f"Trying to assign obligatory coverage shift for Worker {worker.identification} on {date_str} for jobs {jobs}")
                for job in jobs:
                    # Consider the minimum distance constraint for obligatory shifts
                    if can_work_on_date(worker, date_str, last_shift_dates, weekend_tracker, holidays_set, weekly_tracker, job, job_count, min_distance, max_shifts_per_week, schedule=schedule, workers=workers):
                        assign_worker_to_shift(worker, date_str, job, schedule, last_shift_dates, weekend_tracker, weekly_tracker, job_count, holidays_set, min_distance, max_shifts_per_week)
                        last_assigned_job[worker.identification] = job
                        last_assigned_day[worker.identification] = datetime.strptime(date_str.strip(), "%d/%m/%Y").weekday()
                        day_rotation_tracker[worker.identification][datetime.strptime(date_str.strip(), "%d/%m/%Y").weekday()] = True
                        logging.debug(f"Assigned obligatory coverage shift for Worker {worker.identification} on {date_str} for job {job}")
                        break
                else:
                    logging.debug(f"Worker {worker.identification} cannot be assigned for obligatory coverage on {date_str} for any job.")
                    continue

    # Continue with the rest of the scheduling logic
    for start_date, end_date in valid_work_periods:
        for date in generate_date_range(start_date, end_date):
            date_str = date.strftime("%d/%m/%Y")
            for job in jobs:
                logging.debug(f"Processing job '{job}' on date {date_str}")

                assigned = False
                iteration_count = 0
                max_iterations = len(workers) * 2

                while not assigned and iteration_count < max_iterations:
                    available_workers = [worker for worker in workers if worker.shift_quota > 0 and can_work_on_date(worker, date_str, last_shift_dates, weekend_tracker, holidays_set, weekly_tracker, job, job_count, min_distance, max_shifts_per_week, schedule=schedule, workers=workers)]
                    if not available_workers:
                        logging.error(f"No available workers for job {job} on {date_str}. Stopping assignment.")
                        return schedule

                    worker = max(available_workers, key=lambda w: (
                        (datetime.strptime(date_str.strip(), "%d/%m/%Y") - last_shift_dates[w.identification][-1]).days if last_shift_dates[w.identification] else float('inf'),
                        w.shift_quota,
                        w.percentage_shifts,
                        last_assigned_job[w.identification] != job,
                        last_assigned_day[w.identification] != datetime.strptime(date_str.strip(), "%d/%m/%Y").weekday(),
                        not day_rotation_tracker[w.identification][datetime.strptime(date_str.strip(), "%d/%m/%Y").weekday()]
                    ))
                    assign_worker_to_shift(worker, date_str, job, schedule, last_shift_dates, weekend_tracker, weekly_tracker, job_count, holidays_set, min_distance, max_shifts_per_week)
                    last_assigned_job[worker.identification] = job
                    last_assigned_day[worker.identification] = datetime.strptime(date_str.strip(), "%d/%m/%Y").weekday()
                    day_rotation_tracker[worker.identification][datetime.strptime(date_str.strip(), "%d/%m/%Y").weekday()] = True
                    logging.debug(f"Assigned shift for Worker {worker.identification} on {date_str} for job {job}")
                    assigned = True

                    iteration_count += 1
                    if iteration_count >= max_iterations:
                        logging.error(f"Exceeded maximum iterations for job {job} on {date_str}. Exiting to prevent infinite loop.")
                        return schedule

    logging.debug(f"Final schedule: {schedule}")
    return schedule
    
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

if __name__ == "__main__":
    # User input for the required parameters
    work_periods = input("Enter work periods (e.g., 01/10/2024-31/10/2024, separated by commas): ").split(',')
    holidays = input("Enter holidays (e.g., 09/10/2024, separated by commas): ").split(',')
    jobs = input("Enter workstations (e.g., A, B, C, separated by commas): ").split(',')
    min_distance = int(input("Enter minimum distance between work shifts (in days): "))
    max_shifts_per_week = int(input("Enter maximum shifts that can be assigned per week: "))
    num_workers = int(input("Enter number of available workers: "))

    # Create workers list with unavailable dates
    workers = []
    for i in range(num_workers):
        worker_id = f"W{i+1}"
        print(f"\nSetting up Worker {worker_id}")
        unavailable_dates_str = input(f"Enter unavailable dates for Worker {worker_id} (DD/MM/YYYY, separated by commas) or press Enter if none: ").strip()
        
        # Process unavailable dates
        unavailable_dates = []
        if unavailable_dates_str:
            dates = unavailable_dates_str.split(',')
            for date in dates:
                date = date.strip()
                try:
                    # Validate date format
                    datetime.strptime(date, "%d/%m/%Y")
                    unavailable_dates.append(date)
                except ValueError:
                    print(f"Warning: Invalid date format '{date}'. Skipping this date.")
        
        # Create worker with unavailable dates
        worker = Worker(
            identification=worker_id,
            unavailable_dates=unavailable_dates
        )
        workers.append(worker)
        print(f"Created {worker_id} with unavailable dates: {worker.unavailable_dates}")

    # Debug print to verify unavailable dates are stored
    print("\nVerifying worker unavailable dates:")
    for worker in workers:
        print(f"Worker {worker.identification} unavailable dates: {worker.unavailable_dates}")

    schedule = schedule_shifts(work_periods, holidays, jobs, workers, min_distance, max_shifts_per_week)
    
    # Verify no worker is scheduled on their unavailable dates
    print("\nChecking schedule against unavailable dates:")
    for job, assignments in schedule.items():
        for date, worker_id in assignments.items():
            worker = next(w for w in workers if w.identification == worker_id)
            if date in worker.unavailable_dates:
                print(f"ERROR: Worker {worker_id} was scheduled on {date} despite being unavailable!")

    breakdown = prepare_breakdown(schedule)
    print("\nFinal Schedule:")
    print(export_breakdown(breakdown))
