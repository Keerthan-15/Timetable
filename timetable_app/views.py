from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponse, Http404
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Branch, Semester, Subject, Teacher, Classroom,
    TimetableEntry, TimetableSession, ConstraintConfig
)
from .serializers import (
    BranchSerializer, SemesterSerializer, SubjectSerializer,
    TeacherSerializer, ClassroomSerializer, TimetableEntrySerializer,
    TimetableSessionSerializer, TimetableGenerationRequestSerializer,
    TimetableRegenerationRequestSerializer, ConstraintConfigSerializer,
    BulkImportSerializer
)
from .services.scheduler import TimetableScheduler, regenerate_timetable
from .services.constraint_engine import ConstraintValidator
from .export.pdf_generator import PDFGenerator
from .export.csv_generator import CSVGenerator
import pandas as pd
import json


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer


class SemesterViewSet(viewsets.ModelViewSet):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    filterset_fields = ['academic_year', 'semester_type']


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['subject_type', 'credits', 'branches', 'semesters']
    search_fields = ['code', 'name']

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def bulk_import(self, request):
        """Import subjects from CSV file"""
        serializer = BulkImportSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']

            try:
                df = pd.read_csv(file)
                created_count = 0
                errors = []

                for index, row in df.iterrows():
                    try:
                        with transaction.atomic():
                            subject_data = {
                                'code': row['code'],
                                'name': row['name'],
                                'credits': int(row['credits']),
                                'hours_per_week': int(row['hours_per_week']),
                                'subject_type': row['subject_type'],
                                'is_core': bool(row.get('is_core', False))
                            }

                            subject = Subject.objects.create(**subject_data)

                            # Handle branches and semesters if present
                            if 'branches' in row and pd.notna(row['branches']):
                                branch_codes = [code.strip() for code in str(row['branches']).split(',')]
                                branches = Branch.objects.filter(code__in=branch_codes)
                                subject.branches.set(branches)

                            if 'semesters' in row and pd.notna(row['semesters']):
                                semester_ids = [int(sid.strip()) for sid in str(row['semesters']).split(',')]
                                semesters = Semester.objects.filter(id__in=semester_ids)
                                subject.semesters.set(semesters)

                            created_count += 1

                    except Exception as e:
                        errors.append(f"Row {index + 1}: {str(e)}")

                return Response({
                    'created': created_count,
                    'errors': errors,
                    'total_rows': len(df)
                })

            except Exception as e:
                return Response(
                    {'error': f'Error processing file: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['departments', 'is_active']
    search_fields = ['name', 'employee_id']


class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['room_type', 'building', 'is_active']
    search_fields = ['room_number', 'building']


class TimetableSessionViewSet(viewsets.ModelViewSet):
    queryset = TimetableSession.objects.all()
    serializer_class = TimetableSessionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['branch', 'semester', 'section', 'academic_year', 'is_valid']

    @action(detail=True, methods=['get'])
    def entries(self, request, pk=None):
        """Get all timetable entries for a session"""
        session = self.get_object()
        entries = session.entries.all().order_by('day_of_week', 'period')
        serializer = TimetableEntrySerializer(entries, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def export_pdf(self, request, pk=None):
        """Export timetable as PDF"""
        try:
            session = self.get_object()
            entries = session.entries.all().order_by('day_of_week', 'period')

            pdf_generator = PDFGenerator()
            pdf_content = pdf_generator.generate_timetable_pdf(session, entries)

            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="timetable_{session.branch.code}_{session.semester.number}_{session.section}.pdf"'
            return response

        except Exception as e:
            return Response(
                {'error': f'Error generating PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def export_csv(self, request, pk=None):
        """Export timetable as CSV"""
        try:
            session = self.get_object()
            entries = session.entries.all().order_by('day_of_week', 'period')

            csv_generator = CSVGenerator()
            csv_content = csv_generator.generate_timetable_csv(session, entries)

            response = HttpResponse(csv_content, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="timetable_{session.branch.code}_{session.semester.number}_{session.section}.csv"'
            return response

        except Exception as e:
            return Response(
                {'error': f'Error generating CSV: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Validate timetable against constraints"""
        try:
            session = self.get_object()
            entries = list(session.entries.all())

            validation_result = ConstraintValidator.validate_timetable(
                str(session.id),
                entries
            )

            return Response(validation_result)

        except Exception as e:
            return Response(
                {'error': f'Error validating timetable: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate timetable for existing session"""
        try:
            session = self.get_object()

            serializer = TimetableRegenerationRequestSerializer(data=request.data)
            if serializer.is_valid():
                result = regenerate_timetable(
                    str(session.id),
                    serializer.validated_data['avoid_previous_conflicts']
                )

                if result['success']:
                    return Response(result)
                else:
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'error': f'Error regenerating timetable: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
def generate_timetable(request):
    """Generate a new timetable"""
    serializer = TimetableGenerationRequestSerializer(data=request.data)
    if serializer.is_valid():
        try:
            # Get parameters
            branch_id = serializer.validated_data['branch_id']
            semester_id = serializer.validated_data['semester_id']
            section = serializer.validated_data['section']
            academic_year = serializer.validated_data['academic_year']
            constraint_config = serializer.validated_data['constraint_config']

            # Get objects
            branch = Branch.objects.get(id=branch_id)
            semester = Semester.objects.get(id=semester_id)

            # Check if timetable already exists
            existing_session = TimetableSession.objects.filter(
                branch=branch,
                semester=semester,
                section=section,
                academic_year=academic_year
            ).first()

            if existing_session and existing_session.is_valid:
                return Response({
                    'success': False,
                    'message': 'Valid timetable already exists for this configuration. Use regenerate instead.',
                    'existing_session_id': str(existing_session.id)
                }, status=status.HTTP_400_BAD_REQUEST)

            # Generate timetable
            scheduler = TimetableScheduler(branch, semester, section, academic_year)
            result = scheduler.generate_timetable()

            if result['success']:
                return Response(result, status=status.HTTP_201_CREATED)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except Branch.DoesNotExist:
            return Response(
                {'error': 'Branch not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Semester.DoesNotExist:
            return Response(
                {'error': 'Semester not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error generating timetable: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_timetable_grid(request):
    """Get timetable in grid format for frontend display"""
    session_id = request.GET.get('session_id')
    if not session_id:
        return Response(
            {'error': 'session_id parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        session = TimetableSession.objects.get(id=session_id)
        entries = session.entries.all().order_by('day_of_week', 'period')

        # Create grid structure
        grid = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

        for day_num, day_name in enumerate(days, 1):
            grid[day_name] = {period: None for period in range(1, 9)}  # Periods 1-8

        # Fill grid with entries
        for entry in entries:
            day_name = entry.get_day_of_week_display()
            period = entry.period

            # Handle continuous blocks
            for p in range(period, period + entry.duration):
                if p <= 8:
                    grid[day_name][p] = {
                        'id': entry.id,
                        'subject': {
                            'code': entry.subject.code,
                            'name': entry.subject.name,
                            'type': entry.subject.subject_type,
                            'credits': entry.subject.credits
                        },
                        'teacher': {
                            'name': entry.teacher.name,
                            'id': entry.teacher.id
                        },
                        'room': {
                            'number': entry.room.room_number,
                            'building': entry.room.building,
                            'id': entry.room.id
                        },
                        'duration': entry.duration,
                        'is_continuous': entry.is_continuous,
                        'is_start': p == period
                    }

        return Response({
            'session': TimetableSessionSerializer(session).data,
            'grid': grid,
            'statistics': session.statistics,
            'constraint_compliance': session.constraint_compliance
        })

    except TimetableSession.DoesNotExist:
        return Response(
            {'error': 'Timetable session not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error retrieving timetable: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_dashboard_statistics(request):
    """Get dashboard statistics"""
    try:
        # Basic counts
        total_branches = Branch.objects.count()
        total_semesters = Semester.objects.count()
        total_subjects = Subject.objects.count()
        total_teachers = Teacher.objects.filter(is_active=True).count()
        total_rooms = Classroom.objects.filter(is_active=True).count()

        # Timetable statistics
        total_timetables = TimetableSession.objects.count()
        valid_timetables = TimetableSession.objects.filter(is_valid=True).count()
        pending_timetables = total_timetables - valid_timetables

        # Recent timetables
        recent_timetables = TimetableSession.objects.order_by('-generated_at')[:5]

        # Subject type distribution
        subject_types = Subject.objects.values('subject_type').annotate(count=Count('id'))

        # Room type distribution
        room_types = Classroom.objects.filter(is_active=True).values('room_type').annotate(count=Count('id'))

        return Response({
            'overview': {
                'total_branches': total_branches,
                'total_semesters': total_semesters,
                'total_subjects': total_subjects,
                'total_teachers': total_teachers,
                'total_rooms': total_rooms
            },
            'timetables': {
                'total': total_timetables,
                'valid': valid_timetables,
                'pending': pending_timetables,
                'success_rate': (valid_timetables / total_timetables * 100) if total_timetables > 0 else 0
            },
            'recent_timetables': TimetableSessionSerializer(recent_timetables, many=True).data,
            'subject_distribution': list(subject_types),
            'room_distribution': list(room_types)
        })

    except Exception as e:
        return Response(
            {'error': f'Error retrieving statistics: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def validate_constraints(request):
    """Validate timetable constraints"""
    session_id = request.data.get('session_id')
    if not session_id:
        return Response(
            {'error': 'session_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        session = TimetableSession.objects.get(id=session_id)
        entries = list(session.entries.all())

        validation_result = ConstraintValidator.validate_timetable(
            session_id,
            entries
        )

        return Response(validation_result)

    except TimetableSession.DoesNotExist:
        return Response(
            {'error': 'Timetable session not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error validating constraints: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ConstraintConfigViewSet(viewsets.ModelViewSet):
    queryset = ConstraintConfig.objects.all()
    serializer_class = ConstraintConfigSerializer