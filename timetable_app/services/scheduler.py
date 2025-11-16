from typing import List, Dict, Tuple, Optional, Set
import random
from collections import defaultdict
from django.db import transaction
from timetable_app.models import (
    Subject, TimetableEntry, Teacher, Classroom, TimetableSession,
    TimetableGenerationLog, Branch, Semester
)
from .constraint_engine import ConstraintValidator


class TimetableScheduler:
    def __init__(self, branch: Branch, semester: Semester, section: str, academic_year: str):
        self.branch = branch
        self.semester = semester
        self.section = section
        self.academic_year = academic_year
        self.session = None
        self.generation_log = None

        # Time matrix: days x periods (6 days x 8 periods)
        self.timetable_matrix = [[None for _ in range(9)] for _ in range(7)]  # 1-indexed

        # Get subjects for this branch and semester
        self.subjects = list(Subject.objects.filter(
            branches=self.branch,
            semesters=self.semester
        ).order_by('-credits', 'subject_type'))

        # Get available teachers and rooms
        self.teachers = list(Teacher.objects.filter(
            departments=self.branch,
            is_active=True
        ))

        self.rooms = list(Classroom.objects.filter(is_active=True))

        # Track assignments for constraint validation
        self.teacher_assignments = defaultdict(list)  # teacher -> (day, period, duration)
        self.room_assignments = defaultdict(list)     # room -> (day, period, duration)
        self.subject_assignments = defaultdict(list)  # subject -> assigned hours

        # Maximum attempts before giving up
        self.max_attempts = 1000
        self.current_attempt = 0

    def generate_timetable(self) -> Dict:
        """
        Generate a complete timetable using backtracking with constraint propagation
        """
        try:
            with transaction.atomic():
                # Create session and log
                self.session = TimetableSession.objects.create(
                    branch=self.branch,
                    semester=self.semester,
                    section=self.section,
                    academic_year=self.academic_year,
                    is_valid=False
                )

                self.generation_log = TimetableGenerationLog.objects.create(
                    session=self.session,
                    status='started'
                )

                # Sort subjects by priority (high credits first, then theory, then others)
                sorted_subjects = self._sort_subjects_by_priority()

                # Generate timetable using backtracking
                success = self._backtrack_generate(sorted_subjects, 0)

                if success:
                    # Create timetable entries from matrix
                    entries = self._create_entries_from_matrix()

                    # Validate against constraints
                    validation_result = ConstraintValidator.validate_timetable(
                        str(self.session.id),
                        entries
                    )

                    if validation_result['is_compliant']:
                        # Save entries
                        TimetableEntry.objects.bulk_create(entries)

                        # Update session and log
                        self.session.is_valid = True
                        self.session.constraint_compliance = validation_result
                        self.session.statistics = self._calculate_statistics(entries)
                        self.session.save()

                        self.generation_log.status = 'success'
                        self.generation_log.completed_at = timezone.now()
                        self.generation_log.save()

                        return {
                            'success': True,
                            'session_id': str(self.session.id),
                            'entries': len(entries),
                            'constraint_compliance': validation_result,
                            'statistics': self.session.statistics
                        }
                    else:
                        # Not compliant, try again
                        self.timetable_matrix = [[None for _ in range(9)] for _ in range(7)]
                        self.teacher_assignments.clear()
                        self.room_assignments.clear()
                        self.subject_assignments.clear()

                        return self._retry_generation(sorted_subjects)
                else:
                    self.generation_log.status = 'failed'
                    self.generation_log.message = 'Failed to generate valid timetable'
                    self.generation_log.completed_at = timezone.now()
                    self.generation_log.save()

                    return {
                        'success': False,
                        'message': 'Failed to generate valid timetable'
                    }

        except Exception as e:
            if self.generation_log:
                self.generation_log.status = 'failed'
                self.generation_log.message = str(e)
                self.generation_log.completed_at = timezone.now()
                self.generation_log.save()

            return {
                'success': False,
                'message': f'Error during generation: {str(e)}'
            }

    def _sort_subjects_by_priority(self) -> List[Subject]:
        """
        Sort subjects for optimal allocation:
        1. High-credit theory subjects (first period priority)
        2. Lab subjects (continuous blocks)
        3. Other subjects by credits
        """
        def priority_key(subject):
            priority = 0
            if subject.subject_type == 'theory' and subject.credits >= 3:
                priority = 1000 - subject.credits * 100  # Higher credits = higher priority
            elif subject.subject_type == 'lab':
                priority = 500 - subject.credits * 50
            elif subject.subject_type in ['mini_project', 'activity']:
                priority = 300 - subject.credits * 30
            else:
                priority = 100 - subject.credits * 10
            return priority

        return sorted(self.subjects, key=priority_key)

    def _backtrack_generate(self, subjects: List[Subject], index: int) -> bool:
        """
        Backtracking algorithm with constraint propagation
        """
        if self.current_attempt >= self.max_attempts:
            return False

        if index >= len(subjects):
            return True  # All subjects assigned successfully

        subject = subjects[index]
        self.current_attempt += 1

        # Get all possible time slots for this subject
        possible_slots = self._get_possible_slots(subject)

        # Shuffle for variety in generation
        random.shuffle(possible_slots)

        for slot in possible_slots:
            if self._can_place_subject(subject, slot):
                # Place the subject
                self._place_subject(subject, slot)

                # Recursively try to place remaining subjects
                if self._backtrack_generate(subjects, index + 1):
                    return True

                # Backtrack - remove the subject
                self._remove_subject(subject, slot)

        return False

    def _get_possible_slots(self, subject: Subject) -> List[Tuple[int, int, int]]:
        """
        Get all possible time slots for a subject
        Returns list of (day, period, duration) tuples
        """
        slots = []

        if subject.subject_type == 'theory':
            # Theory subjects can be placed in any single period
            for day in range(1, 7):  # Monday-Saturday
                for period in range(1, 9):  # Periods 1-8
                    if subject.credits >= 3 and period == 1 and day <= 5:
                        # High-credit subjects get priority for first period on weekdays
                        slots.append((day, period, 1))
                    elif period > 1:
                        slots.append((day, period, 1))

        elif subject.subject_type in ['lab', 'mini_project']:
            # Lab and mini-project need 2-hour continuous blocks
            continuous_blocks = [(2, 2), (4, 2), (6, 2)]  # (start_period, duration)
            for day in range(1, 6):  # Monday-Friday only
                for start, duration in continuous_blocks:
                    if self._is_slot_available(day, start, duration):
                        slots.append((day, start, duration))

        elif subject.subject_type == 'activity':
            # Activities can be in 2-hour blocks or single periods
            continuous_blocks = [(2, 2), (4, 2), (6, 2)]
            for day in range(1, 7):  # Including Saturday
                for start, duration in continuous_blocks:
                    if self._is_slot_available(day, start, duration):
                        slots.append((day, start, duration))

        elif subject.subject_type in ['tutorial', 'remedial', 'proctor']:
            # These must be in last period only
            for day in range(1, 6):  # Monday-Friday
                if self._is_slot_available(day, 8, 1):
                    slots.append((day, 8, 1))

        # Saturday special handling for activities
        if subject.subject_type in ['activity'] and self._should_place_on_saturday(subject):
            # Add Saturday activity slots (periods 3-4 and 5-6)
            saturday_blocks = [(3, 2), (5, 2)]
            for start, duration in saturday_blocks:
                if self._is_slot_available(6, start, duration):  # Saturday is day 6
                    slots.append((6, start, duration))

        return slots

    def _can_place_subject(self, subject: Subject, slot: Tuple[int, int, int]) -> bool:
        """
        Check if subject can be placed in the given slot
        """
        day, period, duration = slot

        # Check if slot is available
        if not self._is_slot_available(day, period, duration):
            return False

        # Check teacher availability
        teacher = self._get_available_teacher(subject, day, period, duration)
        if not teacher:
            return False

        # Check room availability
        room = self._get_available_room(subject, day, period, duration)
        if not room:
            return False

        # Check constraint-specific rules
        return self._check_constraints(subject, slot)

    def _check_constraints(self, subject: Subject, slot: Tuple[int, int, int]) -> bool:
        """
        Check if placing subject in slot violates any constraints
        """
        day, period, duration = slot

        # Constraint 2: Lab blocks should be continuous
        if subject.subject_type in ['lab', 'mini_project'] and duration < 2:
            return False

        # Constraint 3: One lab per day
        if subject.subject_type == 'lab':
            existing_labs = [
                entry for entry in self._get_day_entries(day)
                if hasattr(entry, 'subject') and entry.subject.subject_type == 'lab'
            ]
            if existing_labs:
                return False

        # Constraint 4: Tutorial/Remedial/Proctor in last period only
        if subject.subject_type in ['tutorial', 'remedial', 'proctor'] and period != 8:
            return False

        # Constraint 1: High-credit subjects should get first period
        if (subject.credits >= 3 and subject.subject_type == 'theory' and
            period != 1 and day <= 5 and not self._has_first_period(subject)):
            # Allow if we can still place it in first period later
            first_period_available = self._is_slot_available(day, 1, 1)
            if first_period_available:
                return False

        return True

    def _is_slot_available(self, day: int, period: int, duration: int) -> bool:
        """
        Check if a time slot is completely available
        """
        for p in range(period, period + duration):
            if p > 8 or self.timetable_matrix[day][p] is not None:
                return False
        return True

    def _place_subject(self, subject: Subject, slot: Tuple[int, int, int]):
        """
        Place a subject in the timetable matrix
        """
        day, period, duration = slot

        # Get teacher and room
        teacher = self._get_available_teacher(subject, day, period, duration)
        room = self._get_available_room(subject, day, period, duration)

        # Place in matrix
        entry_data = {
            'subject': subject,
            'teacher': teacher,
            'room': room,
            'duration': duration,
            'is_continuous': duration > 1
        }

        for p in range(period, period + duration):
            self.timetable_matrix[day][p] = entry_data

        # Track assignments
        self.teacher_assignments[teacher.id].append((day, period, duration))
        self.room_assignments[room.id].append((day, period, duration))
        self.subject_assignments[subject.code].append(duration)

    def _remove_subject(self, subject: Subject, slot: Tuple[int, int, int]):
        """
        Remove a subject from the timetable matrix (backtracking)
        """
        day, period, duration = slot

        # Remove from matrix
        for p in range(period, period + duration):
            entry_data = self.timetable_matrix[day][p]
            if entry_data:
                teacher = entry_data['teacher']
                room = entry_data['room']

                # Remove from assignments
                self.teacher_assignments[teacher.id].remove((day, period, duration))
                self.room_assignments[room.id].remove((day, period, duration))

            self.timetable_matrix[day][p] = None

        # Remove from subject assignments
        self.subject_assignments[subject.code].remove(duration)

    def _get_available_teacher(self, subject: Subject, day: int, period: int, duration: int) -> Optional[Teacher]:
        """
        Get an available teacher for the subject and time slot
        """
        # Simple assignment - in a real system, you'd have subject-teacher mappings
        available_teachers = []

        for teacher in self.teachers:
            # Check if teacher is available at this time
            teacher_busy = False
            for assigned_day, assigned_period, assigned_duration in self.teacher_assignments[teacher.id]:
                if assigned_day == day and self._periods_overlap(
                    assigned_period, assigned_duration, period, duration
                ):
                    teacher_busy = True
                    break

            if not teacher_busy:
                available_teachers.append(teacher)

        return random.choice(available_teachers) if available_teachers else None

    def _get_available_room(self, subject: Subject, day: int, period: int, duration: int) -> Optional[Classroom]:
        """
        Get an available room for the subject and time slot
        """
        # Filter rooms by type
        if subject.subject_type == 'lab':
            suitable_rooms = [r for r in self.rooms if r.room_type == 'lab']
        elif subject.subject_type in ['theory', 'tutorial', 'remedial', 'proctor']:
            suitable_rooms = [r for r in self.rooms if r.room_type == 'theory']
        else:
            suitable_rooms = [r for r in self.rooms if r.room_type == 'activity']

        available_rooms = []

        for room in suitable_rooms:
            # Check if room is available at this time
            room_busy = False
            for assigned_day, assigned_period, assigned_duration in self.room_assignments[room.id]:
                if assigned_day == day and self._periods_overlap(
                    assigned_period, assigned_duration, period, duration
                ):
                    room_busy = True
                    break

            if not room_busy:
                available_rooms.append(room)

        return random.choice(available_rooms) if available_rooms else None

    def _periods_overlap(self, p1: int, d1: int, p2: int, d2: int) -> bool:
        """
        Check if two time periods overlap
        """
        return not (p1 + d1 <= p2 or p2 + d2 <= p1)

    def _has_first_period(self, subject: Subject) -> bool:
        """
        Check if subject already has a first period assignment
        """
        for day in range(1, 6):  # Monday-Friday
            if self.timetable_matrix[day][1] and self.timetable_matrix[day][1]['subject'] == subject:
                return True
        return False

    def _should_place_on_saturday(self, subject: Subject) -> bool:
        """
        Check if subject should be placed on Saturday (for activities)
        """
        return subject.subject_type == 'activity'

    def _get_day_entries(self, day: int) -> List:
        """
        Get all entries for a specific day
        """
        entries = []
        for period in range(1, 9):
            if self.timetable_matrix[day][period]:
                entries.append(self.timetable_matrix[day][period])
        return entries

    def _create_entries_from_matrix(self) -> List[TimetableEntry]:
        """
        Convert the timetable matrix to TimetableEntry objects
        """
        entries = []

        for day in range(1, 7):  # Monday-Saturday
            period = 1
            while period <= 8:
                if self.timetable_matrix[day][period]:
                    entry_data = self.timetable_matrix[day][period]

                    # Create entry
                    entry = TimetableEntry(
                        session=self.session,
                        subject=entry_data['subject'],
                        teacher=entry_data['teacher'],
                        room=entry_data['room'],
                        day_of_week=day,
                        period=period,
                        duration=entry_data['duration'],
                        is_continuous=entry_data['is_continuous']
                    )
                    entries.append(entry)

                    # Skip the duration of this entry
                    period += entry_data['duration']
                else:
                    period += 1

        return entries

    def _calculate_statistics(self, entries: List[TimetableEntry]) -> Dict:
        """
        Calculate statistics for the generated timetable
        """
        stats = {
            'total_subjects': len(set(e.subject for e in entries)),
            'total_hours': sum(e.duration for e in entries),
            'theory_periods': sum(e.duration for e in entries if e.subject.subject_type == 'theory'),
            'lab_blocks': len([e for e in entries if e.subject.subject_type == 'lab']),
            'activity_periods': sum(e.duration for e in entries if e.subject.subject_type == 'activity'),
            'mini_project_blocks': len([e for e in entries if e.subject.subject_type == 'mini_project']),
            'tutorial_periods': sum(e.duration for e in entries if e.subject.subject_type == 'tutorial'),
            'remedial_periods': sum(e.duration for e in entries if e.subject.subject_type == 'remedial'),
            'proctor_periods': sum(e.duration for e in entries if e.subject.subject_type == 'proctor'),
        }

        # Teacher workload statistics
        teacher_hours = defaultdict(int)
        for entry in entries:
            teacher_hours[entry.teacher.name] += entry.duration

        stats['teacher_workload'] = dict(teacher_hours)
        stats['avg_teacher_hours'] = sum(teacher_hours.values()) / len(teacher_hours) if teacher_hours else 0

        # Room utilization
        room_hours = defaultdict(int)
        for entry in entries:
            room_hours[entry.room.room_number] += entry.duration

        stats['room_utilization'] = dict(room_hours)
        stats['avg_room_hours'] = sum(room_hours.values()) / len(room_hours) if room_hours else 0

        return stats

    def _retry_generation(self, subjects: List[Subject]) -> Dict:
        """
        Retry generation with different strategies
        """
        # Try up to 3 times with different random seeds
        for attempt in range(3):
            self.timetable_matrix = [[None for _ in range(9)] for _ in range(7)]
            self.teacher_assignments.clear()
            self.room_assignments.clear()
            self.subject_assignments.clear()
            self.current_attempt = 0

            # Shuffle subjects for different order
            shuffled_subjects = subjects.copy()
            random.shuffle(shuffled_subjects)

            if self._backtrack_generate(shuffled_subjects, 0):
                entries = self._create_entries_from_matrix()
                validation_result = ConstraintValidator.validate_timetable(
                    str(self.session.id),
                    entries
                )

                if validation_result['is_compliant']:
                    TimetableEntry.objects.bulk_create(entries)
                    self.session.is_valid = True
                    self.session.constraint_compliance = validation_result
                    self.session.statistics = self._calculate_statistics(entries)
                    self.session.save()

                    self.generation_log.status = 'success'
                    self.generation_log.completed_at = timezone.now()
                    self.generation_log.save()

                    return {
                        'success': True,
                        'session_id': str(self.session.id),
                        'entries': len(entries),
                        'constraint_compliance': validation_result,
                        'statistics': self.session.statistics
                    }

        # All attempts failed
        self.generation_log.status = 'failed'
        self.generation_log.message = 'Failed to generate compliant timetable after multiple attempts'
        self.generation_log.completed_at = timezone.now()
        self.generation_log.save()

        return {
            'success': False,
            'message': 'Failed to generate compliant timetable after multiple attempts'
        }


def regenerate_timetable(session_id: str, avoid_previous_conflicts: bool = True) -> Dict:
    """
    Re-generate timetable for an existing session
    """
    try:
        session = TimetableSession.objects.get(id=session_id)

        # Delete existing entries
        TimetableEntry.objects.filter(session=session).delete()

        # Create new scheduler with same parameters
        scheduler = TimetableScheduler(
            branch=session.branch,
            semester=session.semester,
            section=session.section,
            academic_year=session.academic_year
        )

        # Set the existing session instead of creating a new one
        scheduler.session = session

        # Generate new timetable
        result = scheduler.generate_timetable()

        if result['success']:
            return {
                'success': True,
                'message': 'Timetable re-generated successfully',
                'session_id': str(session.id),
                'constraint_compliance': result['constraint_compliance'],
                'statistics': result['statistics']
            }
        else:
            return {
                'success': False,
                'message': result.get('message', 'Failed to re-generate timetable')
            }

    except TimetableSession.DoesNotExist:
        return {
            'success': False,
            'message': 'Timetable session not found'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error during re-generation: {str(e)}'
        }