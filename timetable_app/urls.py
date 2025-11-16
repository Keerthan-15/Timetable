from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'branches', views.BranchViewSet)
router.register(r'semesters', views.SemesterViewSet)
router.register(r'subjects', views.SubjectViewSet)
router.register(r'teachers', views.TeacherViewSet)
router.register(r'classrooms', views.ClassroomViewSet)
router.register(r'timetable', views.TimetableSessionViewSet, basename='timetable-session')
router.register(r'constraint-configs', views.ConstraintConfigViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    path('generate/', views.generate_timetable, name='generate-timetable'),
    path('grid/', views.get_timetable_grid, name='timetable-grid'),
    path('dashboard/', views.get_dashboard_statistics, name='dashboard-stats'),
    path('validate/', views.validate_constraints, name='validate-constraints'),
]