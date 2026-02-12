# 2025-12-18: Learning Engine Views
# Author: BabySteps Development Team
# Purpose: DRF views for learning engine API endpoints
# Last Modified: 2025-12-18

"""
Learning Engine Views

Provides API endpoints for:
- Micro-lesson listing and detail
- Student progress tracking
- Practice question validation with real-time feedback
- Difficulty calibration
- Student dashboard
"""

# 2025-12-18: Import DRF components
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

# 2025-12-18: Import Django utilities
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Avg, Count, Q

# 2025-12-18: Import models
from .models import (
    StudentLearningProfile,
    MicroLesson,
    MicroLessonProgress,
    PracticeAttempt,
    DifficultyCalibration,
)

# 2025-12-18: Import serializers
from .serializers import (
    StudentLearningProfileSerializer,
    MicroLessonListSerializer,
    MicroLessonDetailSerializer,
    MicroLessonProgressSerializer,
    PracticeAttemptSerializer,
    PracticeSubmissionSerializer,
    PracticeValidationResponseSerializer,
    DifficultyCalibrationSerializer,
    StudentDashboardSerializer,
    LessonProgressUpdateSerializer,
)


class MicroLessonViewSet(viewsets.ReadOnlyModelViewSet):
    """
    2025-12-18: ViewSet for MicroLesson CRUD operations.
    
    Endpoints:
    - GET /api/learning/lessons/ - List all published lessons
    - GET /api/learning/lessons/{id}/ - Get lesson detail
    - GET /api/learning/lessons/by-chapter/ - List lessons by chapter
    - POST /api/learning/lessons/{id}/start/ - Start a lesson
    """
    
    # 2025-12-18: Default queryset - only published lessons
    queryset = MicroLesson.objects.filter(is_published=True, qa_status='passed')
    
    # 2025-12-18: Permission - allow any for now (will add auth later)
    permission_classes = [permissions.AllowAny]
    
    def get_serializer_class(self):
        """2025-12-18: Use different serializers for list vs detail."""
        if self.action == 'list':
            return MicroLessonListSerializer
        return MicroLessonDetailSerializer
    
    def get_queryset(self):
        """2025-12-18: Filter queryset based on query params."""
        queryset = super().get_queryset()
        
        # 2025-12-18: Filter by subject
        subject = self.request.query_params.get('subject')
        if subject:
            queryset = queryset.filter(subject__iexact=subject)
        
        # 2025-12-18: Filter by class
        class_number = self.request.query_params.get('class')
        if class_number:
            queryset = queryset.filter(class_number=int(class_number))
        
        # 2025-12-18: Filter by chapter
        chapter_id = self.request.query_params.get('chapter')
        if chapter_id:
            queryset = queryset.filter(chapter_id=chapter_id)
        
        return queryset.order_by('class_number', 'subject', 'chapter_id', 'sequence_in_chapter')
    
    @action(detail=False, methods=['get'])
    def by_chapter(self, request):
        """
        2025-12-18: Get lessons grouped by chapter.
        Returns a structured response for lesson tree display.
        """
        # 2025-12-18: Get filter params
        subject = request.query_params.get('subject')
        class_number = request.query_params.get('class')
        
        # 2025-12-18: Build queryset
        queryset = self.get_queryset()
        if subject:
            queryset = queryset.filter(subject__iexact=subject)
        if class_number:
            queryset = queryset.filter(class_number=int(class_number))
        
        # 2025-12-18: Group by chapter
        chapters = {}
        for lesson in queryset:
            chapter_key = lesson.chapter_id
            if chapter_key not in chapters:
                chapters[chapter_key] = {
                    'chapter_id': lesson.chapter_id,
                    'chapter_name': lesson.chapter_name,
                    'lessons': []
                }
            chapters[chapter_key]['lessons'].append(
                MicroLessonListSerializer(lesson).data
            )
        
        return Response(list(chapters.values()))
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        2025-12-18: Start a lesson for the current user.
        Creates or retrieves a progress record.
        """
        # 2025-12-18: Get the lesson
        lesson = self.get_object()
        
        # 2025-12-18: Check if user is authenticated
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required to start a lesson'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # 2025-12-18: Get or create progress record
        progress, created = MicroLessonProgress.objects.get_or_create(
            student=request.user,
            micro_lesson=lesson,
            defaults={
                'status': 'in_progress',
                'started_at': timezone.now(),
            }
        )
        
        # 2025-12-18: If existing progress, check if we need a new attempt
        if not created and progress.status == 'completed':
            # 2025-12-18: Create new attempt
            new_attempt_number = progress.attempt_number + 1
            progress = MicroLessonProgress.objects.create(
                student=request.user,
                micro_lesson=lesson,
                status='in_progress',
                started_at=timezone.now(),
                attempt_number=new_attempt_number
            )
        elif not created and progress.status == 'not_started':
            # 2025-12-18: Update existing to in_progress
            progress.status = 'in_progress'
            progress.started_at = timezone.now()
            progress.save()
        
        # 2025-12-18: Update student's streak
        profile, _ = StudentLearningProfile.objects.get_or_create(user=request.user)
        profile.update_streak()
        
        # 2025-12-18: Get difficulty calibration
        calibration, _ = DifficultyCalibration.objects.get_or_create(
            student=request.user,
            subject=lesson.subject,
            defaults={'current_difficulty': 'core'}
        )
        progress.difficulty_level = calibration.current_difficulty
        progress.save()
        
        return Response({
            'progress': MicroLessonProgressSerializer(progress).data,
            'lesson': MicroLessonDetailSerializer(lesson, context={'request': request}).data,
            'difficulty_level': calibration.current_difficulty
        })


class MicroLessonProgressViewSet(viewsets.ModelViewSet):
    """
    2025-12-18: ViewSet for MicroLessonProgress operations.
    
    Endpoints:
    - GET /api/learning/progress/ - List user's progress records
    - GET /api/learning/progress/{id}/ - Get progress detail
    - PATCH /api/learning/progress/{id}/ - Update progress
    - POST /api/learning/progress/{id}/advance/ - Advance to next step
    """
    
    serializer_class = MicroLessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """2025-12-18: Return only current user's progress."""
        return MicroLessonProgress.objects.filter(
            student=self.request.user
        ).select_related('micro_lesson').order_by('-updated_at')
    
    @action(detail=True, methods=['post'])
    def advance(self, request, pk=None):
        """
        2025-12-18: Advance to the next step in the lesson.
        Updates current_step and time_spent.
        """
        progress = self.get_object()
        
        # 2025-12-18: Validate input
        serializer = LessonProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 2025-12-18: Update progress
        progress.current_step = serializer.validated_data['current_step']
        progress.time_spent_seconds += serializer.validated_data['time_spent_seconds']
        
        # 2025-12-18: Update status if provided
        if 'status' in serializer.validated_data:
            progress.status = serializer.validated_data['status']
            if progress.status == 'completed':
                progress.completed_at = timezone.now()
                progress.calculate_mastery()
        
        progress.save()
        
        return Response(MicroLessonProgressSerializer(progress).data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        2025-12-18: Mark lesson as completed and calculate mastery.
        """
        progress = self.get_object()
        
        # 2025-12-18: Calculate mastery score
        mastery = progress.calculate_mastery()
        
        # 2025-12-18: Update status
        progress.status = 'mastered' if mastery >= 80 else 'completed'
        progress.current_step = 'completed'
        progress.completed_at = timezone.now()
        progress.save()
        
        # 2025-12-18: Update student profile
        profile, _ = StudentLearningProfile.objects.get_or_create(user=request.user)
        profile.total_mastery_points += mastery
        profile.save()
        
        return Response({
            'progress': MicroLessonProgressSerializer(progress).data,
            'mastery_score': mastery,
            'status': progress.status,
            'message': 'Congratulations! You have mastered this lesson!' if progress.status == 'mastered' else 'Lesson completed. Keep practicing to improve your mastery!'
        })


class PracticeValidationView(APIView):
    """
    2025-12-18: API view for validating practice answers.
    Provides real-time feedback with step-by-step solutions.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        2025-12-18: Validate a practice answer and return feedback.
        
        Request body:
        - lesson_progress_id: ID of progress record
        - question_index: Question number (1-10)
        - student_answer: Student's answer
        - time_taken_seconds: Time taken
        - hints_requested: Number of hints used (optional)
        - retry_count: Number of retries (optional)
        """
        # 2025-12-18: Validate input
        serializer = PracticeSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # 2025-12-18: Get progress record
        progress = get_object_or_404(
            MicroLessonProgress,
            id=data['lesson_progress_id'],
            student=request.user
        )
        
        # 2025-12-18: Get the question from the lesson
        lesson = progress.micro_lesson
        question_index = data['question_index']
        
        if question_index > len(lesson.practice_questions):
            return Response(
                {'error': f'Question {question_index} does not exist'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        question = lesson.practice_questions[question_index - 1]
        student_answer = data['student_answer'].strip()
        correct_answer = str(question.get('answer', question.get('correct_answer', ''))).strip()
        
        # 2025-12-18: Validate answer
        is_correct = self._check_answer(student_answer, correct_answer, question)
        partial_credit = 1.0 if is_correct else self._calculate_partial_credit(student_answer, correct_answer, question)
        
        # 2025-12-18: Detect misconception if wrong
        misconception = ''
        if not is_correct:
            misconception = self._detect_misconception(student_answer, question, lesson.misconceptions)
        
        # 2025-12-18: Create attempt record
        attempt = PracticeAttempt.objects.create(
            lesson_progress=progress,
            question_index=question_index,
            question_content=question,
            student_answer=student_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            partial_credit=partial_credit,
            time_taken_seconds=data['time_taken_seconds'],
            hints_used=data.get('hints_requested', 0),
            retry_count=data.get('retry_count', 0),
            misconception_detected=misconception
        )
        
        # 2025-12-18: Update progress
        progress.questions_attempted += 1
        if is_correct:
            progress.questions_correct += 1
        progress.hints_used += data.get('hints_requested', 0)
        progress.save()
        
        # 2025-12-18: Update difficulty calibration
        calibration, _ = DifficultyCalibration.objects.get_or_create(
            student=request.user,
            subject=lesson.subject
        )
        calibration.add_attempt(
            is_correct=is_correct,
            time_seconds=data['time_taken_seconds'],
            retries=data.get('retry_count', 0)
        )
        
        # 2025-12-18: Build response
        response_data = {
            'is_correct': is_correct,
            'partial_credit': partial_credit,
            'correct_answer': correct_answer,
            'step_by_step_solution': question.get('solution_steps', []),
            'common_misconception': misconception,
            'feedback_message': self._get_feedback_message(is_correct, progress),
            'questions_remaining': 10 - progress.questions_attempted,
            'current_accuracy': progress.questions_correct / max(1, progress.questions_attempted),
            'adaptive_hint': self._get_adaptive_hint(is_correct, calibration, question)
        }
        
        # 2025-12-18: Store feedback in attempt
        attempt.feedback_shown = response_data
        attempt.save()
        
        return Response(response_data)
    
    def _check_answer(self, student_answer, correct_answer, question):
        """2025-12-18: Check if student answer is correct."""
        # 2025-12-18: Normalize answers for comparison
        student_normalized = student_answer.lower().strip()
        correct_normalized = correct_answer.lower().strip()
        
        # 2025-12-18: Direct match
        if student_normalized == correct_normalized:
            return True
        
        # 2025-12-18: Check for acceptable alternatives
        alternatives = question.get('acceptable_answers', [])
        for alt in alternatives:
            if student_normalized == str(alt).lower().strip():
                return True
        
        # 2025-12-18: Numeric comparison (handle floating point)
        try:
            student_num = float(student_answer)
            correct_num = float(correct_answer)
            if abs(student_num - correct_num) < 0.001:
                return True
        except (ValueError, TypeError):
            pass
        
        return False
    
    def _calculate_partial_credit(self, student_answer, correct_answer, question):
        """2025-12-18: Calculate partial credit for partially correct answers."""
        # 2025-12-18: For now, simple partial credit based on similarity
        # This can be enhanced with more sophisticated logic
        
        # 2025-12-18: Check if answer contains key elements
        key_elements = question.get('key_elements', [])
        if key_elements:
            matches = sum(1 for elem in key_elements if elem.lower() in student_answer.lower())
            return matches / len(key_elements)
        
        return 0.0
    
    def _detect_misconception(self, student_answer, question, lesson_misconceptions):
        """2025-12-18: Detect common misconception from wrong answer."""
        # 2025-12-18: Check question-specific misconceptions
        question_misconceptions = question.get('misconceptions', {})
        for wrong_pattern, misconception in question_misconceptions.items():
            if wrong_pattern.lower() in student_answer.lower():
                return misconception
        
        # 2025-12-18: Check lesson-level misconceptions
        for misc in lesson_misconceptions:
            if misc.get('trigger', '').lower() in student_answer.lower():
                return misc.get('explanation', '')
        
        return ''
    
    def _get_feedback_message(self, is_correct, progress):
        """2025-12-18: Generate personalized feedback message."""
        accuracy = progress.questions_correct / max(1, progress.questions_attempted)
        
        if is_correct:
            if accuracy >= 0.9:
                return "Excellent! You're doing amazingly well! 🌟"
            elif accuracy >= 0.7:
                return "Great job! Keep up the good work! 👍"
            else:
                return "Correct! You're improving! 💪"
        else:
            if accuracy >= 0.7:
                return "Not quite right, but you're still doing well overall. Let's learn from this!"
            elif accuracy >= 0.5:
                return "That's okay! Mistakes help us learn. Review the solution and try again."
            else:
                return "Let's slow down and review the concept. Would you like to see the worked example again?"
    
    def _get_adaptive_hint(self, is_correct, calibration, question):
        """2025-12-18: Get adaptive hint for struggling students."""
        if is_correct:
            return ''
        
        # 2025-12-18: Only provide extra hints for support level students
        if calibration.current_difficulty == 'support':
            return question.get('support_hint', question.get('hint', ''))
        
        return ''


class StudentDashboardView(APIView):
    """
    2025-12-18: API view for student dashboard data.
    Aggregates progress, mastery, streaks, and recommendations.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        2025-12-18: Get dashboard data for current user.
        """
        user = request.user
        
        # 2025-12-18: Get or create learning profile
        profile, _ = StudentLearningProfile.objects.get_or_create(user=user)
        
        # 2025-12-18: Get progress statistics
        progress_stats = MicroLessonProgress.objects.filter(student=user).aggregate(
            completed_count=Count('id', filter=Q(status__in=['completed', 'mastered'])),
            in_progress_count=Count('id', filter=Q(status='in_progress')),
            avg_mastery=Avg('mastery_score', filter=Q(status__in=['completed', 'mastered']))
        )
        
        # 2025-12-18: Get recent lessons
        recent_progress = MicroLessonProgress.objects.filter(
            student=user
        ).select_related('micro_lesson').order_by('-updated_at')[:5]
        
        # 2025-12-18: Build skill heatmap (mastery by chapter)
        skill_heatmap = {}
        completed_progress = MicroLessonProgress.objects.filter(
            student=user,
            status__in=['completed', 'mastered']
        ).select_related('micro_lesson')
        
        for prog in completed_progress:
            chapter_key = f"{prog.micro_lesson.subject}_{prog.micro_lesson.chapter_id}"
            if chapter_key not in skill_heatmap:
                skill_heatmap[chapter_key] = {
                    'subject': prog.micro_lesson.subject,
                    'chapter': prog.micro_lesson.chapter_name,
                    'scores': [],
                }
            skill_heatmap[chapter_key]['scores'].append(prog.mastery_score)
        
        # 2025-12-18: Calculate averages for heatmap
        for key in skill_heatmap:
            scores = skill_heatmap[key]['scores']
            skill_heatmap[key]['average_mastery'] = sum(scores) / len(scores) if scores else 0
            del skill_heatmap[key]['scores']
        
        # 2025-12-18: Get recommended lessons (next in sequence)
        completed_lesson_ids = completed_progress.values_list('micro_lesson_id', flat=True)
        recommended = MicroLesson.objects.filter(
            is_published=True,
            qa_status='passed'
        ).exclude(
            id__in=completed_lesson_ids
        ).order_by('class_number', 'subject', 'chapter_id', 'sequence_in_chapter')[:5]
        
        # 2025-12-18: Get lessons needing revision (low mastery)
        revision_needed_progress = MicroLessonProgress.objects.filter(
            student=user,
            status__in=['completed', 'mastered'],
            mastery_score__lt=70
        ).select_related('micro_lesson').order_by('mastery_score')[:5]
        revision_lessons = [p.micro_lesson for p in revision_needed_progress]
        
        # 2025-12-18: Build response
        response_data = {
            'profile': StudentLearningProfileSerializer(profile).data,
            'total_lessons_completed': progress_stats['completed_count'] or 0,
            'total_lessons_in_progress': progress_stats['in_progress_count'] or 0,
            'overall_mastery_average': round(progress_stats['avg_mastery'] or 0, 1),
            'recent_lessons': MicroLessonProgressSerializer(recent_progress, many=True).data,
            'skill_heatmap': skill_heatmap,
            'recommended_lessons': MicroLessonListSerializer(recommended, many=True).data,
            'revision_needed': MicroLessonListSerializer(revision_lessons, many=True).data,
        }
        
        return Response(response_data)


class DifficultyCalibrationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    2025-12-18: ViewSet for viewing difficulty calibrations.
    """
    
    serializer_class = DifficultyCalibrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """2025-12-18: Return only current user's calibrations."""
        return DifficultyCalibration.objects.filter(student=self.request.user)
