from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Branch(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    sections = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])

    class Meta:
        verbose_name_plural = "Branches"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Semester(models.Model):
    ACADEMIC_YEARS = [
        ('2024-25', '2024-25'),
        ('2025-26', '2025-26'),
        ('2026-27', '2026-27'),
        ('2027-28', '2027-28'),
    ]

    SEMESTER_TYPES = [
        ('odd', 'Odd'),
        ('even', 'Even'),
    ]

    number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    academic_year = models.CharField(max_length=9, choices=ACADEMIC_YEARS)
    semester_type = models.CharField(max_length=10, choices=SEMESTER_TYPES)

    class Meta:
        unique_together = ['number', 'academic_year', 'semester_type']
        ordering = ['academic_year', 'semester_type', 'number']

    def __str__(self):
        return f"{self.academic_year} {self.get_semester_type_display()} Semester {self.number}"


class Subject(models.Model):
    SUBJECT_TYPES = [
        ('theory', 'Theory'),
        ('lab', 'Laboratory'),
        ('activity', 'Activity'),
        ('mini_project', 'Mini Project'),
        ('tutorial', 'Tutorial'),
        ('remedial', 'Remedial'),
        ('proctor', 'Proctor'),
    ]

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    credits = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    hours_per_week = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)])
    subject_type = models.CharField(max_length=20, choices=SUBJECT_TYPES)
    branches = models.ManyToManyField(Branch, related_name='subjects')
    semesters = models.ManyToManyField(Semester, related_name='subjects')
    is_core = models.BooleanField(default=False)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name} ({self.credits} credits)"


class Teacher(models.Model):
    name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=20, unique=True)
    departments = models.ManyToManyField(Branch, related_name='teachers')
    max_hours_per_day = models.IntegerField(default=6, validators=[MinValueValidator(1), MaxValueValidator(12)])
    max_hours_per_week = models.IntegerField(default=24, validators=[MinValueValidator(1), MaxValueValidator(60)])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.employee_id})"


class Classroom(models.Model):
    ROOM_TYPES = [
        ('theory', 'Theory Room'),
        ('lab', 'Laboratory'),
        ('activity', 'Activity Hall'),
    ]

    room_number = models.CharField(max_length=20)
    building = models.CharField(max_length=50)
    capacity = models.IntegerField(validators=[MinValueValidator(10), MaxValueValidator(200)])
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['room_number', 'building']
        ordering = ['building', 'room_number']

    def __str__(self):
        return f"{self.building} - {self.room_number} ({self.capacity} seats)"


class TimetableSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    section = models.CharField(max_length=5, default='A')
    academic_year = models.CharField(max_length=9)
    generated_at = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)
    constraint_compliance = models.JSONField(default=dict)
    statistics = models.JSONField(default=dict)

    class Meta:
        unique_together = ['branch', 'semester', 'section', 'academic_year']
        ordering = ['-generated_at']

    def __str__(self):
        return f"Timetable for {self.branch.code} {self.semester} {self.section}"


class TimetableEntry(models.Model):
    DAYS_OF_WEEK = [
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
    ]

    session = models.ForeignKey(TimetableSession, on_delete=models.CASCADE, related_name='entries')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    room = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    period = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    duration = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(3)])
    is_continuous = models.BooleanField(default=False)

    class Meta:
        unique_together = ['session', 'day_of_week', 'period']
        ordering = ['day_of_week', 'period']

    def __str__(self):
        return f"{self.get_day_of_week_display()} Period {self.period}: {self.subject.code}"


class ConstraintConfig(models.Model):
    name = models.CharField(max_length=100)
    config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Constraint Config: {self.name}"


class TimetableGenerationLog(models.Model):
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    ]

    session = models.ForeignKey(TimetableSession, on_delete=models.CASCADE, related_name='generation_logs')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='started')
    message = models.TextField(blank=True)
    algorithm_details = models.JSONField(default=dict)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Generation Log for {self.session} - {self.status}"