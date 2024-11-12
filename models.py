class Worker:
    def __init__(self, id, work_dates, percentage, group, incompatible_job, group_incompatibility, obligatory_coverage, day_off):
        self.id = id
        self.work_dates = work_dates
        self.percentage = percentage if percentage != "" else 100.0
        self.group = group
        self.incompatible_job = incompatible_job
        self.group_incompatibility = group_incompatibility
        self.obligatory_coverage = obligatory_coverage
        self.day_off = day_off
        self.has_exception = False  # Add this line to track exceptions

class Shift:
    def __init__(self, date, job, worker_id):
        self.date = date
        self.job = job
        self.worker_id = worker_id

    def __str__(self):
        return f"Shift on {self.date} for job {self.job}: Worker {self.worker_id}"
