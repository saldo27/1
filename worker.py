from datetime import datetime

class Worker:
    def __init__(self, identification, work_dates=None, percentage=100.0, group='1', incompatible_job=None, group_incompatibility=None, obligatory_coverage=None, day_off=None, unavailable_dates=None):
        self.identification = identification
        self.work_dates = work_dates if work_dates else []
        self.percentage_shifts = float(percentage) if percentage else 100.0
        self.group = group if group else '1'
        self.incompatible_job = incompatible_job if incompatible_job else []
        self.group_incompatibility = group_incompatibility if group_incompatibility else []
        self.obligatory_coverage = obligatory_coverage if obligatory_coverage else []
        self.day_off = day_off if day_off else []
        self.unavailable_dates = unavailable_dates if unavailable_dates else []

        self.shift_quota = 0
        self.weekly_shift_quota = 0
        self.has_exception = False  # Add this line to track exceptions

    def __lt__(self, other):
        return (self.shift_quota, self.identification) < (other.shift_quota, other.identification)

    def __le__(self, other):
        return (self.shift_quota, self.identification) <= (other.shift_quota, other.identification)

    def __eq__(self, other):
        return (self.shift_quota, self.identification) == (other.shift_quota, other.identification)

    @staticmethod
    def from_user_input(identification, working_dates, percentage_shifts, group, position_incompatibility,
                        group_incompatibility, obligatory_coverage, unavailable_dates):
        working_dates = [datetime.strptime(date.strip(), "%d/%m/%Y-%d/%m/%Y") for date in working_dates.split(',') if date]
        position_incompatibility = position_incompatibility.split(',') if position_incompatibility else []
        group_incompatibility = group_incompatibility.split(',') if group_incompatibility else []
        obligatory_coverage = [datetime.strptime(date.strip(), "%d/%m/%Y") for date in obligatory_coverage.split(',') if date]
        unavailable_dates = [datetime.strptime(date.strip(), "%d/%m/%Y") for date in unavailable_dates.split(',') if date]
        return Worker(identification, working_dates, percentage_shifts, group, position_incompatibility,
                      group_incompatibility, obligatory_coverage, unavailable_dates)
