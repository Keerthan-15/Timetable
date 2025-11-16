from django.contrib import admin
from .models import (
    Branch, Semester, Subject, Teacher, Classroom,
    TimetableEntry, ConstraintConfig, TimetableSession
)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'sections']
    search_fields = ['code', 'name']


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['academic_year', 'semester_type', 'number']
    list_filter = ['academic_year', 'semester_type']
    search_fields = ['academic_year']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'credits', 'hours_per_week', 'subject_type', 'is_core']
    list_filter = ['subject_type', 'is_core', 'credits']
    search_fields = ['code', 'name']
    filter_horizontal = ['branches', 'semesters']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'name', 'max_hours_per_day', 'max_hours_per_week']
    search_fields = ['name', 'employee_id']
    filter_horizontal = ['departments']


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'building', 'capacity', 'room_type']
    list_filter = ['room_type', 'building']
    search_fields = ['room_number', 'building']


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ['subject', 'branch', 'semester', 'section', 'day_of_week', 'period', 'room', 'teacher']
    list_filter = ['branch', 'semester', 'section', 'day_of_week', 'subject__subject_type']
    search_fields = ['subject__name', 'subject__code', 'teacher__name']


@admin.register(ConstraintConfig)
class ConstraintConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']


@admin.register(TimetableSession)
class TimetableSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'branch', 'semester', 'section', 'academic_year', 'is_valid', 'generated_at']
    list_filter = ['is_valid', 'generated_at', 'academic_year']
    search_fields = ['branch__name', 'semester__academic_year']