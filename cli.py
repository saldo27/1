from worker import Worker
from shift_scheduler import schedule_shifts, import_workers_from_csv, export_schedule_to_csv
from datetime import datetime

def run_cli():
    print("Do you want to import workers from a CSV file? (yes/no): ")
    import_csv = input().strip().lower()
    if import_csv == 'yes':
        print("Enter the CSV file path: ")
        csv_file = input().strip()
        # Initialize necessary parameters for schedule
        work_periods = []
        holidays = []
        jobs = []
        min_distance = 0
        max_shifts_per_week = 0
        schedule = {job: {} for job in jobs}
        holidays_set = set(holidays)
        weekend_tracker = defaultdict(int)
        last_shift_dates = defaultdict(list)
        job_count = defaultdict(lambda: defaultdict(int))
        weekly_tracker = defaultdict(lambda: defaultdict(int))
        workers = import_workers_from_csv(csv_file, schedule, last_shift_dates, weekend_tracker, weekly_tracker, job_count, holidays_set, min_distance, max_shifts_per_week)
    else:
        print("Enter number of workers: ")
        num_workers = int(input())
        
        workers = []
        for _ in range(num_workers):
            workers.append(Worker.from_user_input())
    
    print("Enter work periods (comma-separated, e.g., '01/10/2024-10/10/2024'): ")
    work_periods_input = input().split(',')
    work_periods = [period.strip() for period in work_periods_input]

    print("Enter holidays (comma-separated, e.g., '05/10/2024'): ")
    holidays = input().split(',')

    print("Enter workstations (comma-separated, e.g., 'A,B,C'): ")
    jobs = input().split(',')

    print("Enter minimum distance between work shifts (in days): ")
    min_distance = int(input())

    print("Enter maximum shifts that can be assigned per week: ")
    max_shifts_per_week = int(input())

    schedule = schedule_shifts(work_periods, holidays, jobs, workers, min_distance, max_shifts_per_week)
    
    print("Shifts scheduled successfully.")
    for job, shifts in schedule.items():
        print(f"Job {job}:")
        for date, worker in shifts.items():
            print(f"  {date}: {worker}")

    print("Do you want to export the schedule to a CSV file? (yes/no): ")
    export_csv = input().strip().lower()
    if export_csv == 'yes':
        export_schedule_to_csv(schedule)
        print("Schedule exported to CSV successfully.")

if __name__ == "__main__":
    run_cli()
