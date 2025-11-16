from django.core.management.base import BaseCommand
from django.db import transaction
from timetable_app.models import Branch, Semester, Subject, Teacher, Classroom
import random


class Command(BaseCommand):
    help = 'Create sample data for testing the timetable system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        with transaction.atomic():
            # Create branches
            branches_data = [
                ('CS', 'Computer Science Engineering', 4),
                ('EC', 'Electronics and Communication Engineering', 3),
                ('ME', 'Mechanical Engineering', 3),
                ('CE', 'Civil Engineering', 2),
                ('EE', 'Electrical Engineering', 2),
            ]

            branches = []
            for code, name, sections in branches_data:
                branch, created = Branch.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'sections': sections
                    }
                )
                branches.append(branch)
                self.stdout.write(f'Branch: {branch.name} ({"created" if created else "exists"})')

            # Create semesters
            semesters = []
            academic_years = ['2024-25', '2025-26']
            semester_types = ['odd', 'even']

            for year in academic_years:
                for sem_type in semester_types:
                    for num in range(1, 9):
                        semester, created = Semester.objects.get_or_create(
                            academic_year=year,
                            semester_type=sem_type,
                            number=num
                        )
                        semesters.append(semester)
                        self.stdout.write(f'Semester: {semester} ({"created" if created else "exists"})')

            # Create teachers
            teachers_data = [
                ('Dr. Smith', 'T001', ['CS', 'EC'], 6, 24),
                ('Dr. Johnson', 'T002', ['CS'], 6, 24),
                ('Dr. Williams', 'T003', ['CS', 'ME'], 5, 20),
                ('Dr. Brown', 'T004', ['EC', 'EE'], 6, 24),
                ('Dr. Davis', 'T005', ['ME', 'CE'], 5, 20),
                ('Dr. Miller', 'T006', ['CE', 'EE'], 6, 24),
                ('Dr. Wilson', 'T007', ['CS'], 4, 16),
                ('Dr. Moore', 'T008', ['EC'], 5, 20),
                ('Dr. Taylor', 'T009', ['ME'], 6, 24),
                ('Dr. Anderson', 'T010', ['CE'], 5, 20),
                ('Dr. Thomas', 'T011', ['EE'], 6, 24),
                ('Dr. Jackson', 'T012', ['CS', 'EC'], 4, 16),
            ]

            teachers = []
            for name, emp_id, dept_branches, max_day, max_week in teachers_data:
                teacher, created = Teacher.objects.get_or_create(
                    employee_id=emp_id,
                    defaults={
                        'name': name,
                        'max_hours_per_day': max_day,
                        'max_hours_per_week': max_week
                    }
                )
                if created:
                    dept_objects = [Branch.objects.get(code=code) for code in dept_branches]
                    teacher.departments.set(dept_objects)
                teachers.append(teacher)
                self.stdout.write(f'Teacher: {teacher.name} ({"created" if created else "exists"})')

            # Create classrooms
            classrooms_data = [
                ('C101', 'Main Building', 60, 'theory'),
                ('C102', 'Main Building', 60, 'theory'),
                ('C103', 'Main Building', 80, 'theory'),
                ('C104', 'Main Building', 80, 'theory'),
                ('C105', 'Main Building', 120, 'theory'),
                ('Lab-101', 'Science Block', 30, 'lab'),
                ('Lab-102', 'Science Block', 30, 'lab'),
                ('Lab-201', 'Engineering Block', 25, 'lab'),
                ('Lab-202', 'Engineering Block', 25, 'lab'),
                ('Lab-301', 'Computer Center', 40, 'lab'),
                ('Activity-Hall-1', 'Student Center', 100, 'activity'),
                ('Activity-Hall-2', 'Student Center', 150, 'activity'),
                ('Seminar-Hall', 'Main Building', 200, 'activity'),
                ('Conference-Room', 'Admin Block', 50, 'activity'),
            ]

            classrooms = []
            for room, building, capacity, room_type in classrooms_data:
                classroom, created = Classroom.objects.get_or_create(
                    room_number=room,
                    defaults={
                        'building': building,
                        'capacity': capacity,
                        'room_type': room_type
                    }
                )
                classrooms.append(classroom)
                self.stdout.write(f'Classroom: {classroom.room_number} ({"created" if created else "exists"})')

            # Create subjects
            subjects_data = [
                # Computer Science subjects
                ('CS101', 'Introduction to Programming', 'theory', 3, 4, True, ['CS'], [1, 2]),
                ('CS102', 'Data Structures', 'theory', 4, 5, True, ['CS'], [2, 3]),
                ('CS103', 'Algorithms', 'theory', 4, 5, True, ['CS'], [3, 4]),
                ('CS201', 'Database Systems', 'theory', 3, 4, True, ['CS'], [3, 4]),
                ('CS202', 'Operating Systems', 'theory', 4, 5, True, ['CS'], [4, 5]),
                ('CS301', 'Computer Networks', 'theory', 4, 5, True, ['CS'], [5, 6]),
                ('CS302', 'Web Technologies', 'theory', 3, 4, False, ['CS'], [5, 6]),
                ('CS303', 'Machine Learning', 'theory', 4, 5, False, ['CS'], [7, 8]),

                # Lab subjects
                ('CSL101', 'Programming Lab', 'lab', 2, 3, True, ['CS'], [1, 2]),
                ('CSL201', 'Data Structures Lab', 'lab', 2, 3, True, ['CS'], [2, 3]),
                ('CSL301', 'Database Lab', 'lab', 2, 3, True, ['CS'], [3, 4]),
                ('CSL401', 'Networks Lab', 'lab', 2, 3, True, ['CS'], [5, 6]),

                # Activity subjects
                ('ACT101', 'Technical Communication', 'activity', 1, 2, False, ['CS', 'EC', 'ME', 'CE', 'EE'], [1, 2]),
                ('ACT201', 'Professional Ethics', 'activity', 1, 2, False, ['CS', 'EC', 'ME', 'CE', 'EE'], [3, 4]),
                ('ACT301', 'Entrepreneurship', 'activity', 2, 3, False, ['CS', 'EC', 'ME', 'CE', 'EE'], [5, 6]),

                # Mini projects
                ('MP201', 'Mini Project I', 'mini_project', 2, 3, False, ['CS'], [3]),
                ('MP301', 'Mini Project II', 'mini_project', 3, 4, False, ['CS'], [5]),

                # Tutorial subjects
                ('TUT101', 'Mathematics Tutorial', 'tutorial', 1, 2, False, ['CS', 'EC', 'ME', 'CE', 'EE'], [1, 2]),
                ('TUT201', 'Physics Tutorial', 'tutorial', 1, 2, False, ['CS', 'EC', 'ME', 'CE', 'EE'], [1, 2]),

                # Remedial subjects
                ('REM101', 'Remedial Mathematics', 'remedial', 1, 2, False, ['CS', 'EC', 'ME', 'CE', 'EE'], [1, 2]),
                ('REM201', 'Remedial Programming', 'remedial', 1, 2, False, ['CS'], [2, 3]),

                # Proctor subjects
                ('PRO101', 'Proctorial Examination I', 'proctor', 1, 2, False, ['CS', 'EC', 'ME', 'CE', 'EE'], [1, 2]),
                ('PRO201', 'Proctorial Examination II', 'proctor', 1, 2, False, ['CS', 'EC', 'ME', 'CE', 'EE'], [3, 4]),

                # Electronics subjects
                ('EC101', 'Basic Electronics', 'theory', 3, 4, True, ['EC'], [1, 2]),
                ('EC102', 'Digital Logic', 'theory', 4, 5, True, ['EC'], [2, 3]),
                ('EC201', 'Analog Circuits', 'theory', 4, 5, True, ['EC'], [3, 4]),
                ('EC301', 'Microprocessors', 'theory', 4, 5, True, ['EC'], [5, 6]),
                ('ECL101', 'Electronics Lab I', 'lab', 2, 3, True, ['EC'], [1, 2]),
                ('ECL201', 'Electronics Lab II', 'lab', 2, 3, True, ['EC'], [3, 4]),

                # Mechanical Engineering subjects
                ('ME101', 'Engineering Mechanics', 'theory', 3, 4, True, ['ME'], [1, 2]),
                ('ME102', 'Thermodynamics', 'theory', 4, 5, True, ['ME'], [2, 3]),
                ('ME201', 'Fluid Mechanics', 'theory', 4, 5, True, ['ME'], [3, 4]),
                ('ME301', 'Heat Transfer', 'theory', 4, 5, True, ['ME'], [5, 6]),
                ('MEL101', 'Mechanics Lab', 'lab', 2, 3, True, ['ME'], [1, 2]),
                ('MEL201', 'Thermodynamics Lab', 'lab', 2, 3, True, ['ME'], [3, 4]),

                # Civil Engineering subjects
                ('CE101', 'Engineering Drawing', 'theory', 2, 3, True, ['CE'], [1]),
                ('CE102', 'Strength of Materials', 'theory', 4, 5, True, ['CE'], [2, 3]),
                ('CE201', 'Structural Analysis', 'theory', 4, 5, True, ['CE'], [3, 4]),
                ('CE301', 'Concrete Technology', 'theory', 4, 5, True, ['CE'], [5, 6]),
                ('CEL101', 'Surveying Lab', 'lab', 2, 3, True, ['CE'], [2, 3]),

                # Electrical Engineering subjects
                ('EE101', 'Basic Electrical Engineering', 'theory', 3, 4, True, ['EE'], [1, 2]),
                ('EE102', 'Circuit Theory', 'theory', 4, 5, True, ['EE'], [2, 3]),
                ('EE201', 'Electrical Machines', 'theory', 4, 5, True, ['EE'], [3, 4]),
                ('EE301', 'Power Systems', 'theory', 4, 5, True, ['EE'], [5, 6]),
                ('EEL101', 'Electrical Lab I', 'lab', 2, 3, True, ['EE'], [1, 2]),
                ('EEL201', 'Electrical Lab II', 'lab', 2, 3, True, ['EE'], [3, 4]),
            ]

            subjects = []
            for code, name, subj_type, credits, hours, is_core, branch_codes, semester_numbers in subjects_data:
                subject, created = Subject.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'subject_type': subj_type,
                        'credits': credits,
                        'hours_per_week': hours,
                        'is_core': is_core
                    }
                )

                if created:
                    # Set branches
                    branch_objects = [Branch.objects.get(code=code) for code in branch_codes]
                    subject.branches.set(branch_objects)

                    # Set semesters (all semester types and years for given numbers)
                    semester_objects = []
                    for year in academic_years:
                        for sem_type in semester_types:
                            for num in semester_numbers:
                                semester_objects.append(
                                    Semester.objects.get(
                                        academic_year=year,
                                        semester_type=sem_type,
                                        number=num
                                    )
                                )
                    subject.semesters.set(semester_objects)

                subjects.append(subject)
                self.stdout.write(f'Subject: {subject.code} - {subject.name} ({"created" if created else "exists"})')

            # Assign teachers to subjects randomly
            for subject in subjects:
                if subject.branches.exists():
                    # Get teachers who can teach this subject
                    available_teachers = Teacher.objects.filter(
                        departments__in=subject.branches.all()
                    ).distinct()

                    if available_teachers.exists():
                        # Assign 1-3 teachers per subject
                        num_teachers = min(3, available_teachers.count())
                        selected_teachers = random.sample(
                            list(available_teachers),
                            num_teachers
                        )
                        self.stdout.write(f'  Assigned {len(selected_teachers)} teachers to {subject.code}')

        self.stdout.write(
            self.style.SUCCESS('Sample data created successfully!')
        )
        self.stdout.write(f'Created {Branch.objects.count()} branches')
        self.stdout.write(f'Created {Semester.objects.count()} semesters')
        self.stdout.write(f'Created {Subject.objects.count()} subjects')
        self.stdout.write(f'Created {Teacher.objects.count()} teachers')
        self.stdout.write(f'Created {Classroom.objects.count()} classrooms')