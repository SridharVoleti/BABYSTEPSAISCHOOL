# 2025-12-18: Learning Engine Service - Micro-Lesson Learning System
# Author: BabySteps Development Team
# Purpose: Core learning engine implementing Duolingo-style micro-lesson progression
# Last Modified: 2025-12-18

"""
Learning Engine Service

This service implements the core learning experience for the AI School platform,
following Duolingo-inspired principles:
- Micro-learning (5-10 minute units)
- Mastery over coverage
- Visual-first, explanation-driven teaching
- Practice before memorization
- Adaptive difficulty calibration
- Real-time feedback and validation

Key Components:
- MicroLesson: JSON-driven lesson structure with worked examples and practice
- StudentProgress: Track mastery, streaks, and learning paths
- PracticeEngine: Real-time validation with step-by-step feedback
- AdaptiveDifficulty: Adjust based on accuracy, time, and retries
"""

# 2025-12-18: Default app configuration for Django
default_app_config = 'services.learning_engine.apps.LearningEngineConfig'
