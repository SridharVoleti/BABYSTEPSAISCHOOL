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
    DailyActivity,
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
    DailyActivitySerializer,
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
    2026-02-14: Enhanced API view for student star map dashboard.
    Per BS-STU-001-F (Star Map) and BS-STU-002-F (Daily Streak).
    """

    permission_classes = [permissions.IsAuthenticated]

    # 2026-02-14: Streak milestone thresholds
    STREAK_MILESTONES = [3, 7, 14, 30, 60, 100]

    def _mastery_to_stars(self, mastery_score):
        """
        2026-02-14: Convert mastery percentage (0-100) to star count (0-5).
        0-19%=0, 20-39%=1, 40-59%=2, 60-79%=3, 80-89%=4, 90-100%=5.
        """
        if mastery_score >= 90:
            return 5
        elif mastery_score >= 80:
            return 4
        elif mastery_score >= 60:
            return 3
        elif mastery_score >= 40:
            return 2
        elif mastery_score >= 20:
            return 1
        return 0

    def _update_streak(self, profile, user):
        """
        2026-02-14: Update streak based on DailyActivity records.
        Checks yesterday and today for qualifying activity.
        """
        today = timezone.now().date()
        # 2026-02-14: Get or create today's activity record
        daily_activity, _ = DailyActivity.objects.get_or_create(
            student=user,
            activity_date=today,
        )

        # 2026-02-14: Check if streak needs updating
        if profile.last_activity_date == today:
            return  # 2026-02-14: Already updated today

        yesterday = today - timezone.timedelta(days=1)
        yesterday_activity = DailyActivity.objects.filter(
            student=user,
            activity_date=yesterday,
            qualifies_as_learning_day=True
        ).exists()

        if profile.last_activity_date == yesterday and yesterday_activity:
            # 2026-02-14: Streak continues
            pass
        elif profile.last_activity_date and (today - profile.last_activity_date).days > 1:
            # 2026-02-14: Streak broken (missed more than 1 day)
            if not yesterday_activity:
                profile.current_streak_days = 0
                profile.save()

    def _get_streak_milestone(self, current_streak):
        """
        2026-02-14: Check if current streak hits a milestone.
        Returns milestone value or None.
        """
        if current_streak in self.STREAK_MILESTONES:
            return current_streak
        return None

    def get(self, request):
        """
        2026-02-14: Get star map dashboard data for current user.
        Returns student info, streak, star map, today's learning, daily activity.
        """
        user = request.user

        # 2026-02-14: Get or create learning profile
        profile, _ = StudentLearningProfile.objects.get_or_create(user=user)

        # 2026-02-14: Update streak status
        self._update_streak(profile, user)
        profile.refresh_from_db()

        # 2026-02-14: Get student grade from user profile
        grade = getattr(user, 'grade', None) or 1

        # 2026-02-14: Get all progress records for this student (best attempt per concept)
        all_progress = MicroLessonProgress.objects.filter(
            student=user
        ).select_related('micro_lesson', 'micro_lesson__lesson').order_by(
            'micro_lesson_id', '-mastery_score'
        )

        # 2026-02-14: Build best mastery per micro-lesson
        best_mastery = {}
        for prog in all_progress:
            ml_id = prog.micro_lesson_id
            if ml_id not in best_mastery or prog.mastery_score > best_mastery[ml_id]:
                best_mastery[ml_id] = prog.mastery_score

        # 2026-02-14: Build star map grouped by subject
        all_lessons = MicroLesson.objects.filter(
            is_published=True,
            qa_status='passed'
        ).select_related('lesson').order_by('lesson__subject', 'lesson__chapter_id', 'sequence_in_lesson')

        star_map = {}
        total_stars = 0
        for ml in all_lessons:
            subject = ml.lesson.subject if ml.lesson else 'General'
            if subject not in star_map:
                star_map[subject] = []

            mastery = best_mastery.get(ml.id, 0)
            stars = self._mastery_to_stars(mastery)
            total_stars += stars

            # 2026-02-14: Lock check - previous concept in same subject needs 3+ stars
            locked = False
            subject_concepts = star_map[subject]
            if subject_concepts:
                prev_stars = subject_concepts[-1]['stars']
                if prev_stars < 3:
                    locked = True

            star_map[subject].append({
                'id': ml.id,
                'title': ml.title,
                'stars': stars,
                'locked': locked,
                'mastery': mastery,
            })

        # 2026-02-14: Build today's learning suggestions
        todays_learning = []
        # 2026-02-14: Find in-progress and next concepts
        in_progress_lessons = MicroLessonProgress.objects.filter(
            student=user,
            status='in_progress'
        ).select_related('micro_lesson', 'micro_lesson__lesson')[:3]

        for prog in in_progress_lessons:
            ml = prog.micro_lesson
            todays_learning.append({
                'id': ml.id,
                'title': ml.title,
                'subject': ml.lesson.subject if ml.lesson else 'General',
                'status': 'continue',
                'stars': self._mastery_to_stars(prog.mastery_score),
            })

        # 2026-02-14: Add next unlocked concepts if fewer than 3 suggestions
        if len(todays_learning) < 3:
            completed_ids = set(best_mastery.keys())
            in_progress_ids = set(p.micro_lesson_id for p in in_progress_lessons)
            for subject, concepts in star_map.items():
                if len(todays_learning) >= 3:
                    break
                for concept in concepts:
                    if len(todays_learning) >= 3:
                        break
                    if concept['id'] not in completed_ids and concept['id'] not in in_progress_ids and not concept['locked']:
                        todays_learning.append({
                            'id': concept['id'],
                            'title': concept['title'],
                            'subject': subject,
                            'status': 'next',
                            'stars': 0,
                        })

        # 2026-02-14: Get today's daily activity
        today = timezone.now().date()
        daily_activity_obj, _ = DailyActivity.objects.get_or_create(
            student=user,
            activity_date=today,
        )

        # 2026-02-14: Determine avatar_id from user profile
        avatar_id = getattr(user, 'avatar_id', 'boy_1') or 'boy_1'

        # 2026-02-14: Build response
        response_data = {
            'student_name': user.get_full_name() or user.username,
            'avatar_id': avatar_id,
            'grade': grade,
            'current_streak': profile.current_streak_days,
            'longest_streak': profile.longest_streak_days,
            'total_stars': total_stars,
            'todays_learning': todays_learning,
            'star_map': star_map,
            'streak_milestone': self._get_streak_milestone(profile.current_streak_days),
            'daily_activity': {
                'concepts_completed': daily_activity_obj.concepts_completed,
                'questions_answered': daily_activity_obj.questions_answered,
                'time_spent_minutes': daily_activity_obj.time_spent_minutes,
            },
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


class DailyActivityView(APIView):
    """
    2026-02-14: API view for recording and retrieving daily learning activity.
    Used for BS-STU-002-F streak tracking.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """2026-02-14: Get today's activity for current user."""
        today = timezone.now().date()
        activity, _ = DailyActivity.objects.get_or_create(
            student=request.user,
            activity_date=today,
        )
        return Response(DailyActivitySerializer(activity).data)

    def patch(self, request):
        """
        2026-02-14: Update today's activity (increment counters).
        Accepts: concepts_completed, questions_answered, time_spent_minutes.
        """
        today = timezone.now().date()
        activity, _ = DailyActivity.objects.get_or_create(
            student=request.user,
            activity_date=today,
        )

        # 2026-02-14: Increment counters
        if 'concepts_completed' in request.data:
            activity.concepts_completed += int(request.data['concepts_completed'])
        if 'questions_answered' in request.data:
            activity.questions_answered += int(request.data['questions_answered'])
        if 'time_spent_minutes' in request.data:
            activity.time_spent_minutes += int(request.data['time_spent_minutes'])

        # 2026-02-14: Update qualification and save
        activity.update_qualification()

        # 2026-02-14: If qualified, update streak on profile
        if activity.qualifies_as_learning_day:
            profile, _ = StudentLearningProfile.objects.get_or_create(user=request.user)
            profile.update_streak()

        return Response(DailyActivitySerializer(activity).data)
