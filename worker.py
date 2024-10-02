class Worker:
    def __init__(self, worker_id, work_periods, work_percentage, group, job_incompatibilities, group_incompatibilities, mandatory_shifts, unavailable_shifts):
        self.worker_id = worker_id
        self.work_periods = work_periods
        self.work_percentage = work_percentage
        self.group = group
        self.job_incompatibilities = job_incompatibilities
        self.group_incompatibilities = group_incompatibilities
        self.mandatory_shifts = mandatory_shifts
        self.unavailable_shifts = unavailable_shifts

    @staticmethod
    def from_user_input():
        worker_id = input("Enter worker ID: ")
        work_periods = input("Enter work periods (comma-separated, e.g., '01/10/2024-10/10/2024'): ").split(',')
        work_percentage_input = input("Enter work percentage (leave blank for default 100): ")
        work_percentage = int(work_percentage_input) if work_percentage_input else 100
        group_input = input("Enter group (leave blank for default 0): ")
        group = int(group_input) if group_input else 0
        job_incompatibilities = input("Enter job incompatibilities (comma-separated, e.g., 'A,B'): ").split(',')
        group_incompatibilities = input("Enter group incompatibilities (comma-separated, e.g., '1,2'): ").split(',')
        mandatory_shifts = input("Enter mandatory shifts (comma-separated, e.g., '01/10/2024'): ").split(',')
        unavailable_shifts = input("Enter unavailable shifts (comma-separated, e.g., '05/10/2024'): ").split(',')
        return Worker(worker_id, work_periods, work_percentage, group, job_incompatibilities, group_incompatibilities, mandatory_shifts, unavailable_shifts)
