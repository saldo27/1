from datetime import datetime

class Worker:
    def __init__(self, identification, working_dates=None, percentage_shifts=0, group=0, position_incompatibility=None,
                 group_incompatibility=None, mandatory_guard_duty=None, unavailable_dates=None):
        self.identification = identification
        self.working_dates = working_dates if working_dates else []
        self.percentage_shifts = percentage_shifts
        self.group = group
        self.position_incompatibility = position_incompatibility if position_incompatibility else []
        self.group_incompatibility = group_incompatibility if group_incompatibility else []
        self.mandatory_guard_duty = mandatory_guard_duty if mandatory_guard_duty else []
        self.unavailable_dates = unavailable_dates if unavailable_dates else []

    @staticmethod
    def from_user_input(identification, working_dates, percentage_shifts, group, position_incompatibility,
                        group_incompatibility, mandatory_guard_duty, unavailable_dates):
        working_dates = [datetime.strptime(date.strip(), "%d/%m/%Y-%d/%m/%Y") for date in working_dates.split(',') if date]
        position_incompatibility = position_incompatibility.split(',') if position_incompatibility else []
        group_incompatibility = group_incompatibility.split(',') if group_incompatibility else []
        mandatory_guard_duty = [datetime.strptime(date.strip(), "%d/%m/%Y") for date in mandatory_guard_duty.split(',') if date]
        unavailable_dates = [datetime.strptime(date.strip(), "%d/%m/%Y") for date in unavailable_dates.split(',') if date]
        return Worker(identification, working_dates, percentage_shifts, group, position_incompatibility,
                      group_incompatibility, mandatory_guard_duty, unavailable_dates)
