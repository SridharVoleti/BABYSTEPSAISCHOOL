"""
2026-03-04: Monitor Tools Service API views (BS-MON-005/006/007).

Endpoints:
    --- Grade Book (BS-MON-005) ---
    POST   /api/v1/monitor-tools/grades/add/              monitor: add grade entry
    GET    /api/v1/monitor-tools/grades/student/{id}/     parent/monitor: student grades
    GET    /api/v1/monitor-tools/grades/class/            monitor: class grade list
    GET    /api/v1/monitor-tools/grades/report-card/{id}/ parent/monitor: term report card

    --- Homework (BS-MON-006) ---
    POST   /api/v1/monitor-tools/homework/                monitor: create assignment
    GET    /api/v1/monitor-tools/homework/?grade=         student/parent: list for grade
    POST   /api/v1/monitor-tools/homework/done/           parent: mark done
    GET    /api/v1/monitor-tools/homework/{hw_id}/submissions/ monitor: all submissions

    --- Timetable (BS-MON-007) ---
    POST   /api/v1/monitor-tools/timetable/               monitor: create slot
    GET    /api/v1/monitor-tools/timetable/?grade=        any auth: get timetable
    PATCH  /api/v1/monitor-tools/timetable/{id}/          monitor: update slot
    DELETE /api/v1/monitor-tools/timetable/{id}/          monitor: delete slot
    GET    /api/v1/monitor-tools/timetable/today/?grade=  any auth: today's schedule
"""

from rest_framework import status  # 2026-03-04: HTTP codes
from rest_framework.permissions import IsAuthenticated  # 2026-03-04: Auth
from rest_framework.response import Response  # 2026-03-04: DRF response
from rest_framework.views import APIView  # 2026-03-04: CBVs

from services.auth_service.models import Student  # 2026-03-04: Student

from .models import HomeworkAssignment, TimetableSlot
from .serializers import (
    GradeBookEntrySerializer, AddGradeSerializer, GradesQuerySerializer,
    HomeworkAssignmentSerializer, CreateHomeworkSerializer,
    HomeworkSubmissionSerializer, MarkHomeworkDoneSerializer,
    TimetableSlotSerializer, CreateTimetableSlotSerializer, UpdateTimetableSlotSerializer,
)
from .services import GradeBookService, HomeworkService, TimetableService


def _is_monitor(request) -> bool:
    """2026-03-04: True if requesting user is Django staff (monitor)."""
    return request.user.is_authenticated and request.user.is_staff


def _get_student(request):
    """2026-03-04: Return (student, None) or (None, error_response)."""
    if not hasattr(request.user, 'student_profile'):
        return None, Response({'error': 'Student auth required.'}, status=status.HTTP_403_FORBIDDEN)
    return request.user.student_profile, None


def _get_parent(request):
    """2026-03-04: Return (parent, None) or (None, error_response)."""
    if not hasattr(request.user, 'parent_profile'):
        return None, Response({'error': 'Parent auth required.'}, status=status.HTTP_403_FORBIDDEN)
    return request.user.parent_profile, None


# ============================================================
# Grade Book Views
# ============================================================

class AddGradeView(APIView):
    """2026-03-04: POST /api/v1/monitor-tools/grades/add/ — monitor adds grade."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _is_monitor(request):
            return Response({'error': 'Monitor access required.'}, status=status.HTTP_403_FORBIDDEN)

        ser = AddGradeSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data
        try:
            student = Student.objects.get(pk=d['student_id'], is_active=True)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

        entry = GradeBookService.add_grade(
            student=student,
            subject=d['subject'],
            term=d['term'],
            assessment_type=d['assessment_type'],
            title=d['title'],
            score=d['score'],
            max_score=d.get('max_score', 100.0),
            remarks=d.get('remarks', ''),
            recorded_by=request.user,
            date_recorded=d.get('date_recorded'),
        )
        return Response(GradeBookEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class StudentGradesView(APIView):
    """2026-03-04: GET /api/v1/monitor-tools/grades/student/{student_id}/"""

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not _is_monitor(request):
            parent, error = _get_parent(request)
            if error:
                return error
            if student.parent_id != parent.pk:
                return Response({'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        query = GradesQuerySerializer(data=request.query_params)
        if not query.is_valid():
            return Response(query.errors, status=status.HTTP_400_BAD_REQUEST)

        entries = GradeBookService.get_student_grades(
            student,
            subject=query.validated_data.get('subject'),
            term=query.validated_data.get('term'),
        )
        return Response({
            'student_id': str(student_id),
            'student_name': student.full_name,
            'entries': GradeBookEntrySerializer(entries, many=True).data,
        })


class ClassGradesView(APIView):
    """2026-03-04: GET /api/v1/monitor-tools/grades/class/?grade=&subject=&term= — monitor."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_monitor(request):
            return Response({'error': 'Monitor access required.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            grade = int(request.query_params.get('grade', ''))
            subject = request.query_params.get('subject', '').strip()
            term = request.query_params.get('term', '').strip()
            if not subject or not term:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': 'Required query params: grade (int), subject (str), term (T1/T2/T3).'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        entries = GradeBookService.get_class_grades(grade, subject, term)
        return Response({
            'grade': grade, 'subject': subject, 'term': term,
            'entries': GradeBookEntrySerializer(entries, many=True).data,
        })


class ReportCardView(APIView):
    """2026-03-04: GET /api/v1/monitor-tools/grades/report-card/{student_id}/?term= """

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not _is_monitor(request):
            parent, error = _get_parent(request)
            if error:
                return error
            if student.parent_id != parent.pk:
                return Response({'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        term = request.query_params.get('term', 'T1')
        report = GradeBookService.get_student_report_card(student, term)
        return Response({
            'student_id': str(student_id),
            'student_name': student.full_name,
            'term': term,
            'subjects': report,
        })


# ============================================================
# Homework Views
# ============================================================

class HomeworkListCreateView(APIView):
    """
    2026-03-04:
    POST /api/v1/monitor-tools/homework/             monitor: create
    GET  /api/v1/monitor-tools/homework/?grade=      student/parent/monitor: list
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            grade = int(request.query_params.get('grade', ''))
        except (ValueError, TypeError):
            # 2026-03-04: If student, infer grade from token
            if hasattr(request.user, 'student_profile'):
                grade = request.user.student_profile.grade
            else:
                return Response({'error': 'Query param grade required.'}, status=status.HTTP_400_BAD_REQUEST)

        assignments = HomeworkService.list_assignments_for_grade(grade)
        return Response({
            'grade': grade,
            'assignments': HomeworkAssignmentSerializer(assignments, many=True).data,
        })

    def post(self, request):
        if not _is_monitor(request):
            return Response({'error': 'Monitor access required.'}, status=status.HTTP_403_FORBIDDEN)

        ser = CreateHomeworkSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data
        hw = HomeworkService.create_assignment(
            grade=d['grade'],
            subject=d['subject'],
            title=d['title'],
            description=d['description'],
            due_date=d['due_date'],
            assigned_by=request.user,
        )
        return Response(HomeworkAssignmentSerializer(hw).data, status=status.HTTP_201_CREATED)


class StudentHomeworkView(APIView):
    """2026-03-04: GET /api/v1/monitor-tools/homework/student/ — student's homework with status."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        student, error = _get_student(request)
        if error:
            return error
        hw_list = HomeworkService.get_student_homework(student)
        return Response({'homework': hw_list})


class HomeworkMarkDoneView(APIView):
    """2026-03-04: POST /api/v1/monitor-tools/homework/done/ — parent marks homework done."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 2026-03-04: Parent or student can mark done
        if hasattr(request.user, 'student_profile'):
            student = request.user.student_profile
        elif hasattr(request.user, 'parent_profile'):
            # 2026-03-04: Parent must provide student_id in body
            student_id = request.data.get('student_id')
            if not student_id:
                return Response({'error': 'student_id required.'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                student = Student.objects.get(pk=student_id, parent=request.user.parent_profile)
            except Student.DoesNotExist:
                return Response({'error': 'Student not found or not yours.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Student or parent auth required.'}, status=status.HTTP_403_FORBIDDEN)

        ser = MarkHomeworkDoneSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data
        try:
            sub = HomeworkService.mark_done(str(d['homework_id']), student, d.get('note', ''))
        except HomeworkAssignment.DoesNotExist:
            return Response({'error': 'Homework not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(HomeworkSubmissionSerializer(sub).data)


class HomeworkSubmissionsView(APIView):
    """2026-03-04: GET /api/v1/monitor-tools/homework/{hw_id}/submissions/ — monitor."""

    permission_classes = [IsAuthenticated]

    def get(self, request, hw_id):
        if not _is_monitor(request):
            return Response({'error': 'Monitor access required.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            HomeworkAssignment.objects.get(pk=hw_id)
        except HomeworkAssignment.DoesNotExist:
            return Response({'error': 'Homework not found.'}, status=status.HTTP_404_NOT_FOUND)

        subs = HomeworkService.get_class_submissions(str(hw_id))
        return Response({'submissions': HomeworkSubmissionSerializer(subs, many=True).data})


# ============================================================
# Timetable Views
# ============================================================

class TimetableView(APIView):
    """
    2026-03-04:
    GET  /api/v1/monitor-tools/timetable/?grade=   any auth
    POST /api/v1/monitor-tools/timetable/          monitor: create slot
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            grade = int(request.query_params.get('grade', ''))
        except (ValueError, TypeError):
            if hasattr(request.user, 'student_profile'):
                grade = request.user.student_profile.grade
            else:
                return Response({'error': 'Query param grade required.'}, status=status.HTTP_400_BAD_REQUEST)

        slots = TimetableService.get_timetable(grade)
        return Response({
            'grade': grade,
            'slots': TimetableSlotSerializer(slots, many=True).data,
        })

    def post(self, request):
        if not _is_monitor(request):
            return Response({'error': 'Monitor access required.'}, status=status.HTTP_403_FORBIDDEN)

        ser = CreateTimetableSlotSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data
        slot = TimetableService.add_slot(
            grade=d['grade'],
            day_of_week=d['day_of_week'],
            start_time=d['start_time'],
            end_time=d['end_time'],
            subject=d['subject'],
            teacher_name=d.get('teacher_name', ''),
            room=d.get('room', ''),
            created_by=request.user,
        )
        return Response(TimetableSlotSerializer(slot).data, status=status.HTTP_201_CREATED)


class TimetableSlotDetailView(APIView):
    """
    2026-03-04:
    PATCH  /api/v1/monitor-tools/timetable/{id}/   monitor: update
    DELETE /api/v1/monitor-tools/timetable/{id}/   monitor: soft-delete
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, slot_id):
        if not _is_monitor(request):
            return Response({'error': 'Monitor access required.'}, status=status.HTTP_403_FORBIDDEN)

        ser = UpdateTimetableSlotSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            slot = TimetableService.update_slot(str(slot_id), **ser.validated_data)
        except TimetableSlot.DoesNotExist:
            return Response({'error': 'Slot not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(TimetableSlotSerializer(slot).data)

    def delete(self, request, slot_id):
        if not _is_monitor(request):
            return Response({'error': 'Monitor access required.'}, status=status.HTTP_403_FORBIDDEN)

        TimetableService.delete_slot(str(slot_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


class TodayScheduleView(APIView):
    """2026-03-04: GET /api/v1/monitor-tools/timetable/today/?grade= — today's classes."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            grade = int(request.query_params.get('grade', ''))
        except (ValueError, TypeError):
            if hasattr(request.user, 'student_profile'):
                grade = request.user.student_profile.grade
            else:
                return Response({'error': 'Query param grade required.'}, status=status.HTTP_400_BAD_REQUEST)

        slots = TimetableService.get_today_schedule(grade)
        return Response({
            'grade': grade,
            'slots': TimetableSlotSerializer(slots, many=True).data,
        })
