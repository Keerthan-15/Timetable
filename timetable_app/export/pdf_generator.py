from weasyprint import HTML, CSS
from django.template.loader import render_to_string
from django.conf import settings
from io import BytesIO
from ..models import TimetableSession, TimetableEntry


class PDFGenerator:
    def __init__(self):
        self.base_css = self._get_base_css()

    def generate_timetable_pdf(self, session: TimetableSession, entries: list) -> bytes:
        """
        Generate a professional PDF for the timetable
        """
        # Prepare data for template
        context = self._prepare_pdf_context(session, entries)

        # Render HTML template
        html_content = render_to_string('timetable/pdf_template.html', context)

        # Generate PDF
        html = HTML(string=html_content, base_url=settings.BASE_DIR)
        pdf_file = html.write_pdf(stylesheets=[CSS(string=self.base_css)])

        return pdf_file

    def _prepare_pdf_context(self, session: TimetableSession, entries: list) -> dict:
        """
        Prepare context data for PDF template
        """
        # Organize entries by day and period
        timetable_grid = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        periods = list(range(1, 9))  # Periods 1-8

        for day_name in days:
            timetable_grid[day_name] = {period: None for period in periods}

        # Fill grid with entries
        for entry in entries:
            day_name = entry.get_day_of_week_display()
            period = entry.period

            # Handle continuous blocks
            for p in range(period, period + entry.duration):
                if p <= 8:
                    timetable_grid[day_name][p] = {
                        'subject_code': entry.subject.code,
                        'subject_name': entry.subject.name,
                        'subject_type': entry.subject.subject_type,
                        'teacher_name': entry.teacher.name,
                        'room_number': entry.room.room_number,
                        'building': entry.room.building,
                        'duration': entry.duration,
                        'is_start': p == period,
                        'credits': entry.subject.credits
                    }

        # Subject summary
        subject_summary = {}
        for entry in entries:
            subject_key = entry.subject.code
            if subject_key not in subject_summary:
                subject_summary[subject_key] = {
                    'code': entry.subject.code,
                    'name': entry.subject.name,
                    'type': entry.subject.subject_type,
                    'credits': entry.subject.credits,
                    'hours_per_week': entry.subject.hours_per_week,
                    'teacher': entry.teacher.name,
                    'allocated_hours': 0
                }
            subject_summary[subject_key]['allocated_hours'] += entry.duration

        # Room utilization
        room_utilization = {}
        for entry in entries:
            room_key = f"{entry.room.room_number} ({entry.room.building})"
            if room_key not in room_utilization:
                room_utilization[room_key] = {
                    'room_number': entry.room.room_number,
                    'building': entry.room.building,
                    'capacity': entry.room.capacity,
                    'type': entry.room.room_type,
                    'utilized_hours': 0
                }
            room_utilization[room_key]['utilized_hours'] += entry.duration

        return {
            'session': session,
            'timetable_grid': timetable_grid,
            'days': days,
            'periods': periods,
            'subject_summary': subject_summary.values(),
            'room_utilization': room_utilization.values(),
            'constraint_compliance': session.constraint_compliance,
            'statistics': session.statistics,
            'institution_info': {
                'name': 'University Timetable Management System',
                'address': '123 Education Street, Academic City',
                'phone': '+91-123-456-7890',
                'email': 'timetable@university.edu',
                'website': 'www.university.edu'
            }
        }

    def _get_base_css(self) -> str:
        """
        Get CSS styling for PDF generation
        """
        return """
        @page {
            size: A4;
            margin: 1.5cm;
            @bottom-right {
                content: "Page " counter(page);
                font-size: 10pt;
                color: #666;
            }
        }

        body {
            font-family: 'Roboto', Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
        }

        .header {
            text-align: center;
            border-bottom: 3px solid #1976D2;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }

        .institution-name {
            font-size: 24px;
            font-weight: bold;
            color: #1976D2;
            margin-bottom: 10px;
        }

        .document-title {
            font-size: 20px;
            font-weight: 600;
            color: #424242;
            margin-bottom: 15px;
        }

        .session-info {
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }

        .info-label {
            font-weight: 600;
            color: #666;
        }

        .compliance-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: 600;
        }

        .compliance-success {
            background-color: #4CAF50;
            color: white;
        }

        .compliance-warning {
            background-color: #FF9800;
            color: white;
        }

        .compliance-error {
            background-color: #F44336;
            color: white;
        }

        .timetable-container {
            margin-bottom: 30px;
        }

        .timetable-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }

        .timetable-table th,
        .timetable-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
            vertical-align: top;
        }

        .timetable-table th {
            background-color: #1976D2;
            color: white;
            font-weight: 600;
            font-size: 11px;
        }

        .timetable-table td.day-header {
            background-color: #E3F2FD;
            font-weight: 600;
            color: #1976D2;
            min-width: 100px;
        }

        .timetable-table td.period-header {
            background-color: #F5F5F5;
            font-weight: 600;
            color: #666;
            min-width: 60px;
        }

        .subject-cell {
            padding: 4px;
            min-height: 40px;
        }

        .subject-theory {
            background-color: #E8F5E8;
            border-left: 4px solid #4CAF50;
        }

        .subject-lab {
            background-color: #FFF3E0;
            border-left: 4px solid #FF9800;
        }

        .subject-activity {
            background-color: #F3E5F5;
            border-left: 4px solid #9C27B0;
        }

        .subject-mini_project {
            background-color: #E0F7FA;
            border-left: 4px solid #00BCD4;
        }

        .subject-tutorial {
            background-color: #FCE4EC;
            border-left: 4px solid #E91E63;
        }

        .subject-remedial {
            background-color: #FFEBEE;
            border-left: 4px solid #F44336;
        }

        .subject-proctor {
            background-color: #E1F5FE;
            border-left: 4px solid #03A9F4;
        }

        .subject-code {
            font-weight: 600;
            font-size: 10px;
            color: #333;
        }

        .subject-name {
            font-size: 9px;
            color: #666;
            margin: 2px 0;
        }

        .subject-details {
            font-size: 8px;
            color: #888;
        }

        .continuous-block {
            background-color: rgba(25, 118, 210, 0.1);
        }

        .statistics-section {
            margin-bottom: 30px;
        }

        .section-title {
            font-size: 16px;
            font-weight: 600;
            color: #1976D2;
            border-bottom: 2px solid #1976D2;
            padding-bottom: 5px;
            margin-bottom: 15px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .stat-card {
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            text-align: center;
        }

        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #1976D2;
        }

        .stat-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }

        .summary-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }

        .summary-table th,
        .summary-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }

        .summary-table th {
            background-color: #424242;
            color: white;
            font-weight: 600;
        }

        .summary-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }

        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            font-size: 10px;
            color: #666;
        }

        .signature-section {
            margin-top: 30px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 50px;
        }

        .signature-box {
            text-align: center;
        }

        .signature-line {
            border-bottom: 1px solid #333;
            margin: 30px 0 10px 0;
            height: 40px;
        }

        .signature-label {
            font-size: 11px;
            color: #666;
        }

        @media print {
            body {
                font-size: 10px;
            }

            .header {
                margin-bottom: 20px;
            }

            .institution-name {
                font-size: 18px;
            }

            .document-title {
                font-size: 16px;
            }

            .timetable-table th,
            .timetable-table td {
                padding: 4px;
                font-size: 8px;
            }

            .stats-grid {
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
            }

            .stat-card {
                padding: 10px;
            }

            .stat-value {
                font-size: 18px;
            }
        }
        """