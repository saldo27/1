from fpdf import FPDF
from datetime import datetime, timedelta
import calendar

class PDFCalendar(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Shift Schedule Calendar', 0, 1, 'C')

    def add_month(self, year, month, schedule):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f'{calendar.month_name[month]} {year}', 0, 1, 'C')
        self.ln(10)

        # Create a table for the calendar
        self.set_font('Arial', 'B', 8)  # Set font size to 7
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for day in days:
            self.cell(25, 10, day, 1, 0, 'C')
        self.ln()

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(year, month)
        self.set_font('Arial', '', 8)  # Set font size to 7

        for week in month_days:
            for day in week:
                if day == 0:
                    self.cell(25, 20, '', 1, 0, 'C')  # Adjusted height for content
                else:
                    date_str = datetime(year, month, day).strftime("%d/%m/%Y")
                    shifts = [worker for job, dates in schedule.items() for d, worker in dates.items() if d == date_str]
                    cell_content = ", ".join(shifts)  # Insert commas between values
                    self.cell(25, 20, cell_content, 1, 0, 'C')  # Adjusted height for content

            self.ln()

            # Check if the next row will fit on the page, if not, add a new page
            if self.get_y() + 20 > self.page_break_trigger:  # Adjusted height for content
                self.add_page()
                self.set_y(self.t_margin)
                self.set_font('Arial', 'B', 8)
                for day in days:
                    self.cell(25, 10, day, 1, 0, 'C')
                self.ln()

def export_schedule_to_pdf(schedule, filename='shift_schedule.pdf'):
    pdf = PDFCalendar()
    start_date = min(datetime.strptime(date, "%d/%m/%Y") for job, dates in schedule.items() for date in dates.keys())
    end_date = max(datetime.strptime(date, "%d/%m/%Y") for job, dates in schedule.items() for date in dates.keys())

    current_date = start_date
    while current_date <= end_date:
        pdf.add_page()
        pdf.add_month(current_date.year, current_date.month, schedule)
        current_date += timedelta(days=32)
        current_date = current_date.replace(day=1)

    pdf.output(filename)
