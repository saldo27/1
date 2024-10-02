from worker import Worker
from shift_scheduler import schedule_shifts
from datetime import datetime

def run_cli():
    print("Enter work periods (comma-separated, e.g., '01/10/2024-10/10/2024'): ")
    work_periods_input = input().split(',')
    work_periods = [{'start': period.split('-')[0].strip(), 'end': period.split('-')[1].strip()} for period in work_periods_input]

    print("Enter holidays (comma-separated, e.g., '05/10/2024'): ")
    holidays = input().split(',')

    print("Enter jobs (comma-separated, e.g., 'A,B,C'): ")
    jobs = input().split(',')

    print("Enter number of workers: ")
    num_workers = int(input())

    workers = []
    for _ in range(num_workers):
        workers.append(Worker.from_user_input())

    print("Enter previous shifts if any (optional, leave blank if none): ")
    previous_shifts_input = input().split(',')
    previous_shifts = [datetime.strptime(shift.strip(), "%d/%m/%Y") for shift in previous_shifts_input if shift]

    schedule = schedule_shifts(work_periods, holidays, jobs, workers, previous_shifts)
    
    print("Shifts scheduled successfully.")
    for job, shifts in schedule.items():
        print(f"Job {job}:")
        for date, worker in shifts.items():
            print(f"  {date}: {worker}")

if __name__ == "__main__":
    run_cli()
