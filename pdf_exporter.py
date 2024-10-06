from fpdf import FPDF
from datetime import datetime, timedelta
import calendar

class PDFCalendar(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Shift Schedule Calendar', 0, 1, 'C')

    def chapter_title(self, month, year):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f'{calendar.month_name[month]} {year}', 0, 1, 'C')
        self.ln(10)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_month(self, year, month, schedule):
        self.add_page()
        self.chapter_title(month, year)

        cal = calendar.monthcalendar(year, month)
        body = ""
        for week in cal:
            for day in week:
                if day == 0:
                    body += "    "
                else:
                    date_str = datetime(year, month, day).strftime("%d/%m/%Y")
                    shifts = [f"{job}: {worker}" for job, dates in schedule.items() if date_str in dates for date, worker in dates.items()]
                    body += f"{day:2d} " + ("; ".join(shifts) if shifts else "No Shifts") + "    "
            body += "\n"
        self.chapter_body(body)

def export_schedule_to_pdf(schedule, filename='shift_schedule.pdf'):
    pdf = PDFCalendar()
    start_date = min(datetime.strptime(date, "%d/%m/%Y") for job, dates in schedule.items() for date in dates.keys())
    end_date = max(datetime.strptime(date, "%d/%m/%Y") for job, dates in schedule.items() for date in dates.keys())

    current_date = start_date
    while current_date <= end_date:
        pdf.add_month(current_date.year, current_date.month, schedule)
        current_date += timedelta(days=32)
        current_date = current_date.replace(day=1)

    pdf.output(filename)
