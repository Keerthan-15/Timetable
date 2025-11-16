from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from django.db.models import Count, Q
from timetable_app.models import (
    Subject, TimetableEntry, Teacher, Classroom, Branch, Semester
)


class ConstraintViolation:
    def __init__(self, constraint_name: str, message: str, severity: str = 'error'):
        self.constraint_name = constraint_name
        self.message = message
        self.severity = severity  # 'error', 'warning', 'info'

    def to_dict(self):
        return {
            'constraint': self.constraint_name,
            'message': self.message,
            'severity': self.severity
        }


class ConstraintEngine:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.violations: List[ConstraintViolation] = []
        self.warnings: List[ConstraintViolation] = []

    def validate_all_constraints(self, entries: List[TimetableEntry]) -> Dict:
        """
        Validate all 6 constraints specified in the requirements
        """
        self.violations.clear()
        self.warnings.clear()

        # Constraint 1: First period priority for high-credit subjects (3-4 credits)
        self._validate_first_period_priority(entries)

        # Constraint 2: Lab/Activity/Mini-project continuous 2-hour blocks
        self._validate_continuous_blocks(entries)

        # Constraint 3: One lab per day maximum
        self._validate_one_lab_per_day(entries)

        # Constraint 4: Tutorial/Remedial/Proctor in last period, alternating days
        self._validate_last_period_specialists(entries)

        # Constraint 5: Saturday activities (NSS/Sports/Yoga in 2-hour blocks)
        self._validate_saturday_activities(entries)

        # Constraint 6: Exact credit hours allocation
        self._validate_credit_hours(entries)

        return self._generate_compliance_report()

    def _validate_first_period_priority(self, entries: List[TimetableEntry]):
        """
        Constraint i: All subjects with 3+ credits should get first period on weekdays (Monday-Friday)
        """
        # Group subjects by code and check if they have 3+ credits
        high_credit_subjects = Subject.objects.filter(
            credits__gte=3,
            subject_type='theory'
        ).values_list('code', flat=True)

        entries_by_subject = defaultdict(list)
        for entry in entries:
            entries_by_subject[entry.subject.code].append(entry)

        for subject_code in high_credit_subjects:
            subject_entries = entries_by_subject.get(subject_code, [])
            if not subject_entries:
                continue

            # Check if subject has first period (period 1) on Monday-Friday (days 1-5)
            first_periods = [
                entry for entry in subject_entries
                if entry.period == 1 and 1 <= entry.day_of_week <= 5
            ]

            if not first_periods:
                self.violations.append(ConstraintViolation(
                    constraint_name="first_period_priority",
                    message=f"High-credit subject {subject_code} (3+ credits) missing first period allocation on weekdays",
                    severity='error'
                ))

    def _validate_continuous_blocks(self, entries: List[TimetableEntry]):
        """
        Constraint ii: Lab, activity, mini-project classes should be 2 hours continuously
        Allowed slots: 2-3, 4-5, 6-7 (after lunch)
        """
        continuous_subject_types = ['lab', 'activity', 'mini_project']

        for entry in entries:
            if entry.subject.subject_type in continuous_subject_types:
                # Check if it's in allowed continuous block slots
                allowed_blocks = [(2, 3), (4, 5), (6, 7)]  # Period pairs

                is_in_allowed_block = False
                for start, end in allowed_blocks:
                    if entry.period == start and entry.duration >= 2:
                        is_in_allowed_block = True
                        break

                # Also check for single period entries that should be continuous
                if entry.duration == 1 and entry.subject.subject_type in ['lab', 'mini_project']:
                    self.violations.append(ConstraintViolation(
                        constraint_name="continuous_blocks",
                        message=f"{entry.subject.code} ({entry.subject.subject_type}) should be 2-hour continuous block, found single period",
                        severity='error'
                    ))
                    continue

                if not is_in_allowed_block:
                    self.violations.append(ConstraintViolation(
                        constraint_name="continuous_blocks",
                        message=f"{entry.subject.code} ({entry.subject.subject_type}) not in allowed continuous block slots",
                        severity='error'
                    ))

    def _validate_one_lab_per_day(self, entries: List[TimetableEntry]):
        """
        Constraint iii: Only one lab subject per day
        Multiple labs should be on different days
        """
        lab_entries_by_day = defaultdict(list)

        for entry in entries:
            if entry.subject.subject_type == 'lab':
                lab_entries_by_day[entry.day_of_week].append(entry)

        for day, lab_entries in lab_entries_by_day.items():
            if len(lab_entries) > 1:
                lab_codes = [entry.subject.code for entry in lab_entries]
                self.violations.append(ConstraintViolation(
                    constraint_name="one_lab_per_day",
                    message=f"Multiple labs on {self._get_day_name(day)}: {', '.join(lab_codes)}. Only one lab per day allowed.",
                    severity='error'
                ))

    def _validate_last_period_specialists(self, entries: List[TimetableEntry]):
        """
        Constraint iv: Tutorial, remedial, proctor classes in last period only
        Should be on alternate days, not consecutive
        """
        specialist_types = ['tutorial', 'remedial', 'proctor']
        specialist_entries_by_day = {}

        for entry in entries:
            if entry.subject.subject_type in specialist_types:
                # Check if it's in last period (period 8)
                if entry.period != 8:
                    self.violations.append(ConstraintViolation(
                        constraint_name="last_period_specialists",
                        message=f"{entry.subject.code} ({entry.subject.subject_type}) must be in last period (period 8), found in period {entry.period}",
                        severity='error'
                    ))

                specialist_entries_by_day[entry.day_of_week] = entry.subject.subject_type

        # Check for consecutive days
        days_with_specialists = sorted(specialist_entries_by_day.keys())
        consecutive_count = 1

        for i in range(1, len(days_with_specialists)):
            if days_with_specialists[i] == days_with_specialists[i-1] + 1:
                consecutive_count += 1
                if consecutive_count > 2:  # More than 2 consecutive days
                    self.violations.append(ConstraintViolation(
                        constraint_name="last_period_specialists",
                        message=f"Specialist classes on {consecutive_count} consecutive days. Should be alternating.",
                        severity='warning'
                    ))
            else:
                consecutive_count = 1

    def _validate_saturday_activities(self, entries: List[TimetableEntry]):
        """
        Constraint v: Saturday should have NSS/Sports/Yoga activities
        2-2 hour straight after break (periods 3-4 and 5-6)
        Morning slots (1-2) can be theory or 2-hour lab blocks
        """
        saturday_entries = [entry for entry in entries if entry.day_of_week == 6]  # Saturday is day 6

        if not saturday_entries:
            self.warnings.append(ConstraintViolation(
                constraint_name="saturday_activities",
                message="No entries found for Saturday",
                severity='warning'
            ))
            return

        # Check for NSS/Sports/Yoga in periods 3-4 and 5-6
        activity_blocks = [(3, 4), (5, 6)]
        activities_found = []

        for entry in saturday_entries:
            for start, end in activity_blocks:
                if entry.period == start and entry.duration >= 2:
                    activities_found.append(entry.subject.code)

        if len(activities_found) < 2:  # Should have at least 2 activity blocks
            self.violations.append(ConstraintViolation(
                constraint_name="saturday_activities",
                message=f"Saturday missing required activity blocks. Found: {', '.join(activities_found)}",
                severity='error'
            ))

    def _validate_credit_hours(self, entries: List[TimetableEntry]):
        """
        Constraint vi: All subjects must be allocated based on number of classes mentioned
        Exact hours per week based on subject credits
        """
        # Calculate allocated hours per subject
        allocated_hours_by_subject = defaultdict(int)

        for entry in entries:
            allocated_hours_by_subject[entry.subject.code] += entry.duration

        # Compare with required hours
        subjects = Subject.objects.filter(code__in=allocated_hours_by_subject.keys())

        for subject in subjects:
            allocated = allocated_hours_by_subject[subject.code]
            required = subject.hours_per_week

            if allocated != required:
                self.violations.append(ConstraintViolation(
                    constraint_name="credit_hours",
                    message=f"Subject {subject.code}: Required {required} hours/week, allocated {allocated} hours",
                    severity='error'
                ))

    def _generate_compliance_report(self) -> Dict:
        total_constraints = 6
        violated_constraints = len(set(v.constraint_name for v in self.violations))
        satisfied_constraints = total_constraints - violated_constraints

        compliance_percentage = (satisfied_constraints / total_constraints) * 100 if total_constraints > 0 else 0

        return {
            'total_constraints': total_constraints,
            'satisfied': satisfied_constraints,
            'violated': violated_constraints,
            'compliance_percentage': round(compliance_percentage, 2),
            'violations': [v.to_dict() for v in self.violations],
            'warnings': [w.to_dict() for w in self.warnings],
            'is_compliant': len(self.violations) == 0
        }

    def _get_day_name(self, day_number: int) -> str:
        day_names = {
            1: 'Monday', 2: 'Tuesday', 3: 'Wednesday',
            4: 'Thursday', 5: 'Friday', 6: 'Saturday'
        }
        return day_names.get(day_number, 'Unknown')


class ConstraintValidator:
    """
    Public interface for constraint validation
    """

    @staticmethod
    def validate_timetable(session_id: str, entries: List[TimetableEntry]) -> Dict:
        """
        Validate a complete timetable against all constraints
        """
        engine = ConstraintEngine(session_id)
        return engine.validate_all_constraints(entries)

    @staticmethod
    def validate_single_entry(entry: TimetableEntry, existing_entries: List[TimetableEntry]) -> List[ConstraintViolation]:
        """
        Validate a single entry against constraints
        """
        violations = []

        # Check for teacher conflicts
        teacher_conflicts = [
            e for e in existing_entries
            if e.teacher.id == entry.teacher.id
            and e.day_of_week == entry.day_of_week
            and not (e.period + e.duration <= entry.period or entry.period + entry.duration <= e.period)
        ]

        if teacher_conflicts:
            violations.append(ConstraintViolation(
                constraint_name="teacher_conflict",
                message=f"Teacher {entry.teacher.name} already scheduled at this time",
                severity='error'
            ))

        # Check for room conflicts
        room_conflicts = [
            e for e in existing_entries
            if e.room.id == entry.room.id
            and e.day_of_week == entry.day_of_week
            and not (e.period + e.duration <= entry.period or entry.period + entry.duration <= e.period)
        ]

        if room_conflicts:
            violations.append(ConstraintViolation(
                constraint_name="room_conflict",
                message=f"Room {entry.room.number} already occupied at this time",
                severity='error'
            ))

        return violations