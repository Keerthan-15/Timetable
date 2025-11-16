from rest_framework import serializers
from .models import (
    Branch, Semester, Subject, Teacher, Classroom,
    TimetableEntry, TimetableSession, ConstraintConfig
)


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'


class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = '__all__'


class SubjectSerializer(serializers.ModelSerializer):
    branches = BranchSerializer(many=True, read_only=True)
    semesters = SemesterSerializer(many=True, read_only=True)
    branch_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    semester_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Subject
        fields = '__all__'

    def create(self, validated_data):
        branch_ids = validated_data.pop('branch_ids', [])
        semester_ids = validated_data.pop('semester_ids', [])

        subject = Subject.objects.create(**validated_data)

        if branch_ids:
            subject.branches.set(branch_ids)
        if semester_ids:
            subject.semesters.set(semester_ids)

        return subject

    def update(self, instance, validated_data):
        branch_ids = validated_data.pop('branch_ids', None)
        semester_ids = validated_data.pop('semester_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if branch_ids is not None:
            instance.branches.set(branch_ids)
        if semester_ids is not None:
            instance.semesters.set(semester_ids)

        return instance


class TeacherSerializer(serializers.ModelSerializer):
    departments = BranchSerializer(many=True, read_only=True)
    department_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Teacher
        fields = '__all__'

    def create(self, validated_data):
        department_ids = validated_data.pop('department_ids', [])
        teacher = Teacher.objects.create(**validated_data)

        if department_ids:
            teacher.departments.set(department_ids)

        return teacher

    def update(self, instance, validated_data):
        department_ids = validated_data.pop('department_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if department_ids is not None:
            instance.departments.set(department_ids)

        return instance


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = '__all__'


class TimetableEntrySerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    teacher = TeacherSerializer(read_only=True)
    room = ClassroomSerializer(read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = TimetableEntry
        fields = '__all__'


class TimetableSessionSerializer(serializers.ModelSerializer):
    branch = BranchSerializer(read_only=True)
    semester = SemesterSerializer(read_only=True)
    entries = TimetableEntrySerializer(many=True, read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    semester_name = serializers.CharField(source='semester.__str__', read_only=True)

    class Meta:
        model = TimetableSession
        fields = '__all__'


class TimetableGenerationRequestSerializer(serializers.Serializer):
    branch_id = serializers.IntegerField()
    semester_id = serializers.IntegerField()
    section = serializers.CharField(max_length=5, default='A')
    academic_year = serializers.CharField(max_length=9)
    constraint_config = serializers.DictField(default=dict)


class TimetableRegenerationRequestSerializer(serializers.Serializer):
    avoid_previous_conflicts = serializers.BooleanField(default=True)


class ConstraintConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConstraintConfig
        fields = '__all__'


class BulkImportSerializer(serializers.Serializer):
    file = serializers.FileField()
    data_type = serializers.ChoiceField(choices=['subjects', 'teachers', 'branches'])