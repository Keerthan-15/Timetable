import pandas as pd
from django.utils import timezone
from ..models import TimetableSession, TimetableEntry
import io


class CSVGenerator:
    def __init__(self):
        pass

    def generate_timetable_csv(self, session: TimetableSession, entries: list) -> str:
        """
        Generate CSV for timetable data
        """
        # Prepare data for main timetable
        timetable_data = []
        for entry in entries:
            for period_offset in range(entry.duration):
                actual_period = entry.period + period_offset
                if actual_period <= 8:
                    row = {
                        'Day': entry.get_day_of_week_display(),
                        'Period': actual_period,
                        'Subject_Code': entry.subject.code,
                        'Subject_Name': entry.subject.name,
                        'Subject_Type': entry.subject.subject_type,
                        'Credits': entry.subject.credits,
                        'Teacher_Name': entry.teacher.name,
                        'Teacher_ID': entry.teacher.employee_id,
                        'Room_Number': entry.room.room_number,
                        'Building': entry.room.building,
                        'Room_Type': entry.room.room_type,
                        'Duration': entry.duration,
                        'Is_Continuous': entry.is_continuous,
                        'Is_Period_Start': period_offset == 0,
                        'Section': session.section,
                        'Branch': session.branch.name,
                        'Branch_Code': session.branch.code,
                        'Semester': session.semester.__str__(),
                        'Academic_Year': session.academic_year
                    }
                    timetable_data.append(row)

        # Convert to DataFrame and then to CSV
        df = pd.DataFrame(timetable_data)

        # Create CSV content
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        csv_buffer.close()

        return csv_content

    def generate_subject_summary_csv(self, session: TimetableSession, entries: list) -> str:
        """
        Generate CSV for subject summary
        """
        # Aggregate data by subject
        subject_summary = {}
        for entry in entries:
            subject_key = entry.subject.code
            if subject_key not in subject_summary:
                subject_summary[subject_key] = {
                    'Subject_Code': entry.subject.code,
                    'Subject_Name': entry.subject.name,
                    'Subject_Type': entry.subject.subject_type,
                    'Credits': entry.subject.credits,
                    'Required_Hours_Per_Week': entry.subject.hours_per_week,
                    'Teacher_Name': entry.teacher.name,
                    'Teacher_ID': entry.teacher.employee_id,
                    'Is_Core_Subject': entry.subject.is_core,
                    'Allocated_Periods': 0,
                    'Allocated_Hours': 0,
                    'Assigned_Days': set(),
                    'Assigned_Rooms': set()
                }

            subject_summary[subject_key]['Allocated_Periods'] += 1
            subject_summary[subject_key]['Allocated_Hours'] += 1
            subject_summary[subject_key]['Assigned_Days'].add(entry.get_day_of_week_display())
            subject_summary[subject_key]['Assigned_Rooms'].add(f"{entry.room.room_number} ({entry.room.building})")

        # Convert sets to comma-separated strings
        for subject_data in subject_summary.values():
            subject_data['Assigned_Days'] = ', '.join(sorted(subject_data['Assigned_Days']))
            subject_data['Assigned_Rooms'] = ', '.join(sorted(subject_data['Assigned_Rooms']))

        # Convert to DataFrame
        df = pd.DataFrame(list(subject_summary.values()))

        # Reorder columns for better readability
        column_order = [
            'Subject_Code', 'Subject_Name', 'Subject_Type', 'Credits', 'Is_Core_Subject',
            'Required_Hours_Per_Week', 'Allocated_Hours', 'Allocated_Periods',
            'Teacher_Name', 'Teacher_ID', 'Assigned_Days', 'Assigned_Rooms'
        ]
        df = df.reindex(columns=column_order)

        # Generate CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        csv_buffer.close()

        return csv_content

    def generate_teacher_workload_csv(self, session: TimetableSession, entries: list) -> str:
        """
        Generate CSV for teacher workload analysis
        """
        # Aggregate data by teacher
        teacher_workload = {}
        for entry in entries:
            teacher_key = entry.teacher.employee_id
            if teacher_key not in teacher_workload:
                teacher_workload[teacher_key] = {
                    'Teacher_ID': entry.teacher.employee_id,
                    'Teacher_Name': entry.teacher.name,
                    'Departments': ', '.join([dept.code for dept in entry.teacher.departments.all()]),
                    'Max_Hours_Per_Day': entry.teacher.max_hours_per_day,
                    'Max_Hours_Per_Week': entry.teacher.max_hours_per_week,
                    'Assigned_Periods': 0,
                    'Assigned_Hours': 0,
                    'Assigned_Subjects': set(),
                    'Daily_Workload': {},
                    'Assigned_Rooms': set()
                }

            teacher_data = teacher_workload[teacher_key]
            teacher_data['Assigned_Periods'] += 1
            teacher_data['Assigned_Hours'] += 1
            teacher_data['Assigned_Subjects'].add(entry.subject.code)
            teacher_data['Assigned_Rooms'].add(f"{entry.room.room_number} ({entry.room.building})")

            # Track daily workload
            day_name = entry.get_day_of_week_display()
            if day_name not in teacher_data['Daily_Workload']:
                teacher_data['Daily_Workload'][day_name] = 0
            teacher_data['Daily_Workload'][day_name] += entry.duration

        # Process daily workload for each teacher
        for teacher_data in teacher_workload.values():
            teacher_data['Assigned_Subjects'] = ', '.join(sorted(teacher_data['Assigned_Subjects']))
            teacher_data['Assigned_Rooms'] = ', '.join(sorted(teacher_data['Assigned_Rooms']))

            # Calculate workload statistics
            daily_loads = list(teacher_data['Daily_Workload'].values())
            teacher_data['Average_Daily_Hours'] = sum(daily_loads) / len(daily_loads) if daily_loads else 0
            teacher_data['Max_Daily_Hours'] = max(daily_loads) if daily_loads else 0
            teacher_data['Min_Daily_Hours'] = min(daily_loads) if daily_loads else 0

            # Convert daily workload to separate columns
            for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
                teacher_data[f'{day}_Hours'] = teacher_data['Daily_Workload'].get(day, 0)

        # Remove temporary dictionary
        for teacher_data in teacher_workload.values():
            del teacher_data['Daily_Workload']

        # Convert to DataFrame
        df = pd.DataFrame(list(teacher_workload.values()))

        # Generate CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        csv_buffer.close()

        return csv_content

    def generate_room_utilization_csv(self, session: TimetableSession, entries: list) -> str:
        """
        Generate CSV for room utilization analysis
        """
        # Aggregate data by room
        room_utilization = {}
        for entry in entries:
            room_key = f"{entry.room.room_number}_{entry.room.building}"
            if room_key not in room_utilization:
                room_utilization[room_key] = {
                    'Room_Number': entry.room.room_number,
                    'Building': entry.room.building,
                    'Room_Type': entry.room.room_type,
                    'Capacity': entry.room.capacity,
                    'Utilized_Periods': 0,
                    'Utilized_Hours': 0,
                    'Assigned_Subjects': set(),
                    'Assigned_Teachers': set(),
                    'Daily_Utilization': {},
                    'Utilization_Percentage': 0
                }

            room_data = room_utilization[room_key]
            room_data['Utilized_Periods'] += 1
            room_data['Utilized_Hours'] += 1
            room_data['Assigned_Subjects'].add(entry.subject.code)
            room_data['Assigned_Teachers'].add(entry.teacher.name)

            # Track daily utilization
            day_name = entry.get_day_of_week_display()
            if day_name not in room_data['Daily_Utilization']:
                room_data['Daily_Utilization'][day_name] = 0
            room_data['Daily_Utilization'][day_name] += entry.duration

        # Calculate utilization percentages and process data
        total_periods_per_week = 48  # 8 periods × 6 days
        for room_data in room_utilization.values():
            room_data['Assigned_Subjects'] = ', '.join(sorted(room_data['Assigned_Subjects']))
            room_data['Assigned_Teachers'] = ', '.join(sorted(room_data['Assigned_Teachers']))

            # Calculate utilization percentage
            room_data['Utilization_Percentage'] = (room_data['Utilized_Periods'] / total_periods_per_week) * 100

            # Convert daily utilization to separate columns
            for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
                room_data[f'{day}_Hours'] = room_data['Daily_Utilization'].get(day, 0)

            # Remove temporary dictionary
            del room_data['Daily_Utilization']

        # Convert to DataFrame
        df = pd.DataFrame(list(room_utilization.values()))

        # Generate CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        csv_buffer.close()

        return csv_content

    def generate_constraint_compliance_csv(self, session: TimetableSession) -> str:
        """
        Generate CSV for constraint compliance report
        """
        constraint_data = session.constraint_compliance

        # Main compliance data
        compliance_summary = {
            'Metric': ['Total Constraints', 'Satisfied Constraints', 'Violated Constraints',
                      'Compliance Percentage', 'Overall Status'],
            'Value': [
                constraint_data.get('total_constraints', 0),
                constraint_data.get('satisfied', 0),
                constraint_data.get('violated', 0),
                f"{constraint_data.get('compliance_percentage', 0):.2f}%",
                'Compliant' if constraint_data.get('is_compliant', False) else 'Non-Compliant'
            ]
        }

        # Violations details
        violations = constraint_data.get('violations', [])
        violation_details = []
        for violation in violations:
            violation_details.append({
                'Constraint_Name': violation.get('constraint', ''),
                'Violation_Message': violation.get('message', ''),
                'Severity': violation.get('severity', 'error')
            })

        # Warnings details
        warnings = constraint_data.get('warnings', [])
        warning_details = []
        for warning in warnings:
            warning_details.append({
                'Constraint_Name': warning.get('constraint', ''),
                'Warning_Message': warning.get('message', ''),
                'Severity': warning.get('severity', 'warning')
            })

        # Combine all data into a single CSV with sections
        csv_buffer = io.StringIO()

        # Write compliance summary
        csv_buffer.write("CONSTRAINT COMPLIANCE SUMMARY\n")
        summary_df = pd.DataFrame(compliance_summary)
        summary_df.to_csv(csv_buffer, index=False)
        csv_buffer.write("\n\n")

        # Write violations if any
        if violation_details:
            csv_buffer.write("CONSTRAINT VIOLATIONS\n")
            violations_df = pd.DataFrame(violation_details)
            violations_df.to_csv(csv_buffer, index=False)
            csv_buffer.write("\n\n")

        # Write warnings if any
        if warning_details:
            csv_buffer.write("CONSTRAINT WARNINGS\n")
            warnings_df = pd.DataFrame(warning_details)
            warnings_df.to_csv(csv_buffer, index=False)
            csv_buffer.write("\n\n")

        # Write session metadata
        csv_buffer.write("SESSION METADATA\n")
        metadata = {
            'Field': ['Session ID', 'Branch', 'Semester', 'Section', 'Academic Year',
                     'Generated At', 'Is Valid'],
            'Value': [
                str(session.id),
                session.branch.name,
                str(session.semester),
                session.section,
                session.academic_year,
                session.generated_at.strftime('%Y-%m-%d %H:%M:%S') if session.generated_at else '',
                'Yes' if session.is_valid else 'No'
            ]
        }
        metadata_df = pd.DataFrame(metadata)
        metadata_df.to_csv(csv_buffer, index=False)

        csv_content = csv_buffer.getvalue()
        csv_buffer.close()

        return csv_content