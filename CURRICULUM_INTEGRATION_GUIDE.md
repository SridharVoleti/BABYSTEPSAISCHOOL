# Curriculum Integration Guide
**Author**: BabySteps Development Team  
**Last Updated**: 2025-10-31  
**Purpose**: Guide for integrating curriculum JSON files with the application

---

## Overview

This guide explains how to integrate the curriculum JSON files from the `curriculam/` folder with the BabySteps Digital School application. The curriculum loader service provides a clean API for accessing lesson content across all services.

---

## Curriculum Structure

### Folder Organization

```
curriculam/
└── class{N}/                    # Class number (1-12)
    └── {SUBJECT}/               # Subject name (EVS, Math, etc.)
        └── Month{M}/            # Month number (1-12)
            └── Week_{W}/        # Week number (1-52)
                ├── Lessons/
                │   └── {SUBJECT}_C{N}_M{M}_W{W}_D{D}.json
                └── Questions_Banks/
                    └── {SUBJECT}_C{N}_M{M}_W{W}_D{D}_QB.json
```

### Current Available Content

- **Class 1 EVS**: 10 months complete (400 JSON files)
  - Months 1-10: 40 files each (20 lessons + 20 question banks)
  - Total: ~200 lesson files + ~200 question bank files

---

## Curriculum Loader Service

### Installation

The curriculum loader service is located at:
```
services/curriculum_loader_service/
├── __init__.py          # Package initialization
├── models.py            # Database models
├── loader.py            # Core loader logic
├── views.py             # API views (to be created)
├── urls.py              # URL routing (to be created)
└── tests/               # Test suite (to be created)
```

### Database Models

#### 1. CurriculumMetadata
Tracks curriculum structure and metadata:
- `class_number`: Class (1-12)
- `subject`: Subject name
- `total_months`, `total_weeks`, `total_lessons`, `total_question_banks`
- `curriculum_path`: Relative path to curriculum folder
- `is_active`, `is_frozen`: Status flags
- `academic_year`, `version`: Version tracking

#### 2. LessonFile
Tracks individual lesson JSON files:
- `lesson_id`: Unique ID (e.g., SCI_C1_M1_W1_D1)
- `lesson_title`: Lesson title
- `month`, `week`, `day`: Temporal organization
- `file_path`: Path to JSON file
- `duration_minutes`, `level`, `version`: Lesson metadata
- `has_tts`, `has_activities`, `has_ai_coach`, `has_question_bank`: Feature flags
- `is_validated`, `validation_errors`: Validation status

#### 3. QuestionBankFile
Tracks question bank JSON files:
- `qb_id`: Unique ID (e.g., SCI_C1_M1_W1_D1_QB)
- `lesson`: Link to associated lesson
- `file_path`: Path to JSON file
- `total_questions`, `question_types`, `difficulty_levels`: QB metadata

#### 4. CurriculumCache
Caches parsed JSON content:
- `lesson`: Link to lesson file
- `json_content`: Parsed JSON
- `cache_key`, `content_hash`: Cache management
- `is_valid`, `expires_at`: Cache validity
- `hit_count`: Performance tracking

---

## Using the Curriculum Loader

### Basic Usage

```python
from services.curriculum_loader_service.loader import curriculum_loader

# Load a specific lesson
lesson = curriculum_loader.load_lesson(
    class_number=1,
    subject='EVS',
    month=1,
    week=1,
    day=1,
    use_cache=True  # Use cached content if available
)

if lesson:
    print(f"Lesson Title: {lesson['metadata']['lesson_title']}")
    print(f"Duration: {lesson['metadata']['duration_minutes']} minutes")
    print(f"Content Blocks: {len(lesson['content_blocks'])}")
```

### Loading Question Banks

```python
# Load associated question bank
qb = curriculum_loader.load_question_bank(
    class_number=1,
    subject='EVS',
    month=1,
    week=1,
    day=1,
    use_cache=True
)

if qb:
    print(f"Total Questions: {len(qb.get('questions', []))}")
```

### Scanning Curriculum Structure

```python
# Scan all available curriculums
curriculums = curriculum_loader.scan_curriculum_structure()

for curr in curriculums:
    print(f"Class {curr['class_number']} - {curr['subject']}")
    print(f"  Lessons: {curr['total_lessons']}")
    print(f"  Question Banks: {curr['total_question_banks']}")
    print(f"  Months: {curr['total_months']}")
```

### Cache Management

```python
# Clear specific cache
curriculum_loader.clear_cache('lesson_c1_EVS_m1_w1_d1')

# Clear all caches
curriculum_loader.clear_cache()

# Disable caching temporarily
curriculum_loader.use_cache = False
lesson = curriculum_loader.load_lesson(1, 'EVS', 1, 1, 1)
curriculum_loader.use_cache = True
```

---

## API Endpoints (To Be Implemented)

### Lesson Retrieval

```
GET /api/curriculum/class/{class}/subject/{subject}/month/{month}/week/{week}/day/{day}
```

**Response:**
```json
{
  "metadata": {
    "lesson_id": "SCI_C1_M1_W1_D1",
    "class": "1",
    "subject": "Science",
    "lesson_title": "What is Science?",
    "duration_minutes": 30
  },
  "objectives": { ... },
  "vocabulary": { ... },
  "content_blocks": [ ... ],
  "gamification": { ... }
}
```

### Question Bank Retrieval

```
GET /api/curriculum/class/{class}/subject/{subject}/month/{month}/week/{week}/day/{day}/qb
```

### Curriculum List

```
GET /api/curriculum/list
```

**Response:**
```json
{
  "curriculums": [
    {
      "class_number": 1,
      "subject": "EVS",
      "total_lessons": 200,
      "total_question_banks": 200,
      "total_months": 10,
      "is_active": true
    }
  ]
}
```

### Lesson Navigation

```
GET /api/curriculum/class/{class}/subject/{subject}/next?current_month={m}&current_week={w}&current_day={d}
GET /api/curriculum/class/{class}/subject/{subject}/previous?current_month={m}&current_week={w}&current_day={d}
```

---

## Integration with Existing Services

### 1. Lesson Service Integration

Update `services/lesson_generator/views.py`:

```python
from services.curriculum_loader_service.loader import curriculum_loader

def get_lesson(request, class_number, subject, month, week, day):
    """Load lesson from curriculum folder"""
    lesson = curriculum_loader.load_lesson(
        class_number=class_number,
        subject=subject,
        month=month,
        week=week,
        day=day
    )
    
    if not lesson:
        return JsonResponse({'error': 'Lesson not found'}, status=404)
    
    return JsonResponse(lesson)
```

### 2. Assessment Engine Integration

Update `services/assessment_engine/views.py`:

```python
from services.curriculum_loader_service.loader import curriculum_loader

def get_assessment(request, class_number, subject, month, week, day):
    """Load question bank for assessment"""
    qb = curriculum_loader.load_question_bank(
        class_number=class_number,
        subject=subject,
        month=month,
        week=week,
        day=day
    )
    
    if not qb:
        return JsonResponse({'error': 'Question bank not found'}, status=404)
    
    # Extract questions and create assessment
    questions = qb.get('questions', [])
    
    return JsonResponse({
        'assessment_id': f"ASSESS_{qb['metadata']['qb_id']}",
        'questions': questions,
        'total_questions': len(questions)
    })
```

### 3. Progress Tracking Integration

Update `services/student_progress_graph_engine/views.py`:

```python
from services.curriculum_loader_service.loader import curriculum_loader

def get_student_progress(request, student_id, class_number, subject):
    """Get student progress for a subject"""
    # Scan curriculum to get total lessons
    curriculums = curriculum_loader.scan_curriculum_structure()
    
    curr = next(
        (c for c in curriculums 
         if c['class_number'] == class_number and c['subject'] == subject),
        None
    )
    
    if not curr:
        return JsonResponse({'error': 'Curriculum not found'}, status=404)
    
    # Get student progress from database
    # ... (existing logic)
    
    return JsonResponse({
        'student_id': student_id,
        'class': class_number,
        'subject': subject,
        'total_lessons': curr['total_lessons'],
        'completed_lessons': completed_count,
        'progress_percentage': (completed_count / curr['total_lessons']) * 100
    })
```

### 4. Gamification Engine Integration

Update `services/gamification_engine/views.py`:

```python
from services.curriculum_loader_service.loader import curriculum_loader

def award_lesson_completion(request, student_id, lesson_id):
    """Award points and badges for lesson completion"""
    # Parse lesson_id to extract class, subject, month, week, day
    # Example: SCI_C1_M1_W1_D1 -> class=1, subject=SCI, month=1, week=1, day=1
    
    parts = lesson_id.split('_')
    class_num = int(parts[1].replace('C', ''))
    month = int(parts[2].replace('M', ''))
    week = int(parts[3].replace('W', ''))
    day = int(parts[4].replace('D', ''))
    
    # Determine subject from prefix
    subject_map = {'SCI': 'EVS', 'EVS': 'EVS', 'MATH': 'Math'}
    subject = subject_map.get(parts[0], 'EVS')
    
    # Load lesson to get gamification data
    lesson = curriculum_loader.load_lesson(class_num, subject, month, week, day)
    
    if not lesson:
        return JsonResponse({'error': 'Lesson not found'}, status=404)
    
    # Extract gamification data
    gamification = lesson.get('gamification', {})
    points = gamification.get('points_system', {}).get('lesson_completion', 25)
    badges = gamification.get('badges_system', {})
    
    # Award points and badges
    # ... (existing logic)
    
    return JsonResponse({
        'points_awarded': points,
        'badges_awarded': list(badges.keys())
    })
```

---

## Frontend Integration

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const LessonPlayer = ({ classNumber, subject, month, week, day }) => {
  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchLesson = async () => {
      try {
        const response = await axios.get(
          `/api/curriculum/class/${classNumber}/subject/${subject}/month/${month}/week/${week}/day/${day}`
        );
        setLesson(response.data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchLesson();
  }, [classNumber, subject, month, week, day]);

  if (loading) return <div>Loading lesson...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!lesson) return <div>Lesson not found</div>;

  return (
    <div className="lesson-player">
      <h1>{lesson.metadata.lesson_title}</h1>
      <p>Duration: {lesson.metadata.duration_minutes} minutes</p>
      
      {/* Render content blocks */}
      {lesson.content_blocks.map((block, index) => (
        <ContentBlock key={index} block={block} />
      ))}
      
      {/* Render vocabulary */}
      <VocabularySection words={lesson.vocabulary.word_list} />
      
      {/* Render gamification */}
      <GamificationPanel 
        points={lesson.gamification.points_system}
        badges={lesson.gamification.badges_system}
      />
    </div>
  );
};

export default LessonPlayer;
```

---

## Migration Strategy

### Step 1: Database Setup

```bash
# Create migrations for curriculum loader models
python manage.py makemigrations curriculum_loader_service

# Apply migrations
python manage.py migrate
```

### Step 2: Scan and Import Curriculum

```python
# Run management command to scan and import curriculum
python manage.py scan_curriculum

# Or use Django shell
from services.curriculum_loader_service.loader import curriculum_loader
from services.curriculum_loader_service.models import CurriculumMetadata

# Scan curriculum structure
curriculums = curriculum_loader.scan_curriculum_structure()

# Create database records
for curr_data in curriculums:
    CurriculumMetadata.objects.update_or_create(
        class_number=curr_data['class_number'],
        subject=curr_data['subject'],
        defaults=curr_data
    )
```

### Step 3: Update Existing Services

1. Update `lesson_generator` service to use curriculum loader
2. Update `assessment_engine` to load question banks
3. Update `student_progress_graph_engine` to track curriculum progress
4. Update `gamification_engine` to use lesson gamification data

### Step 4: Create API Endpoints

Create `services/curriculum_loader_service/views.py` and `urls.py`

### Step 5: Update Frontend

Update React components to fetch lessons from new API endpoints

---

## Testing

### Unit Tests

```python
# services/curriculum_loader_service/tests/test_loader.py

from django.test import TestCase
from services.curriculum_loader_service.loader import curriculum_loader

class CurriculumLoaderTestCase(TestCase):
    def test_load_lesson_class1_evs(self):
        """Test loading Class 1 EVS lesson"""
        lesson = curriculum_loader.load_lesson(1, 'EVS', 1, 1, 1)
        
        self.assertIsNotNone(lesson)
        self.assertIn('metadata', lesson)
        self.assertEqual(lesson['metadata']['class'], '1')
        self.assertEqual(lesson['metadata']['subject'], 'Science')
    
    def test_load_nonexistent_lesson(self):
        """Test loading non-existent lesson"""
        lesson = curriculum_loader.load_lesson(99, 'NonExistent', 1, 1, 1)
        
        self.assertIsNone(lesson)
    
    def test_cache_functionality(self):
        """Test caching works correctly"""
        # First load (from file)
        lesson1 = curriculum_loader.load_lesson(1, 'EVS', 1, 1, 1, use_cache=True)
        
        # Second load (from cache)
        lesson2 = curriculum_loader.load_lesson(1, 'EVS', 1, 1, 1, use_cache=True)
        
        self.assertEqual(lesson1, lesson2)
    
    def test_scan_curriculum_structure(self):
        """Test curriculum structure scanning"""
        curriculums = curriculum_loader.scan_curriculum_structure()
        
        self.assertGreater(len(curriculums), 0)
        
        # Check Class 1 EVS exists
        class1_evs = next(
            (c for c in curriculums if c['class_number'] == 1 and c['subject'] == 'EVS'),
            None
        )
        
        self.assertIsNotNone(class1_evs)
        self.assertGreater(class1_evs['total_lessons'], 0)
```

### Integration Tests

```python
# services/curriculum_loader_service/tests/test_integration.py

from django.test import TestCase, Client
from django.urls import reverse

class CurriculumAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_get_lesson_api(self):
        """Test lesson retrieval API"""
        response = self.client.get(
            '/api/curriculum/class/1/subject/EVS/month/1/week/1/day/1'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('metadata', data)
    
    def test_get_curriculum_list_api(self):
        """Test curriculum list API"""
        response = self.client.get('/api/curriculum/list')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('curriculums', data)
```

---

## Performance Considerations

### Caching Strategy

1. **Django Cache**: In-memory cache for frequently accessed lessons
   - Timeout: 1 hour
   - Automatic invalidation on file changes

2. **Database Cache**: Persistent cache for all lessons
   - Stores parsed JSON content
   - Tracks hit count for analytics
   - Expires after 24 hours

3. **CDN Cache** (Future): Serve static JSON files via CDN
   - Reduce server load
   - Faster global access

### Optimization Tips

1. **Lazy Loading**: Load lessons on-demand, not all at once
2. **Pagination**: For curriculum lists, paginate results
3. **Compression**: Compress JSON responses (gzip)
4. **Indexing**: Database indexes on frequently queried fields
5. **Connection Pooling**: Reuse database connections

---

## Security Considerations

### Access Control

- **Students**: Can only access lessons assigned to their class
- **Teachers**: Can access all lessons for classes they teach
- **Admins**: Full access to all curriculum content

### Data Validation

- Validate all input parameters (class, subject, month, week, day)
- Sanitize file paths to prevent directory traversal attacks
- Validate JSON structure before caching

### Rate Limiting

- Implement rate limiting on API endpoints
- Prevent abuse and excessive cache invalidation

---

## Monitoring and Analytics

### Metrics to Track

1. **Lesson Access**: Which lessons are most accessed
2. **Cache Hit Rate**: Percentage of requests served from cache
3. **Load Times**: Average time to load lessons
4. **Error Rate**: Percentage of failed lesson loads
5. **Popular Subjects**: Most accessed subjects/classes

### Logging

```python
import logging

logger = logging.getLogger('curriculum_loader')

# Log lesson access
logger.info(f"Lesson accessed: {lesson_id} by user {user_id}")

# Log cache hits/misses
logger.debug(f"Cache hit for {cache_key}")
logger.debug(f"Cache miss for {cache_key}, loading from file")

# Log errors
logger.error(f"Failed to load lesson: {lesson_id}, error: {error}")
```

---

## Troubleshooting

### Common Issues

#### 1. Lesson Not Found
**Symptom**: API returns 404 for existing lesson  
**Solution**: 
- Check file path construction
- Verify folder structure matches expected pattern
- Check file naming convention

#### 2. JSON Parse Error
**Symptom**: JSONDecodeError when loading lesson  
**Solution**:
- Validate JSON syntax in file
- Check for BOM or encoding issues
- Use JSON validator tool

#### 3. Cache Inconsistency
**Symptom**: Outdated lesson content returned  
**Solution**:
- Clear cache: `curriculum_loader.clear_cache()`
- Check cache expiration settings
- Verify content hash calculation

#### 4. Performance Issues
**Symptom**: Slow lesson loading  
**Solution**:
- Enable caching
- Check database query performance
- Add indexes on frequently queried fields
- Consider CDN for static files

---

## Future Enhancements

### Planned Features

1. **Content Versioning**: Track lesson versions and changes
2. **A/B Testing**: Test different lesson variations
3. **Personalization**: Customize lessons based on student performance
4. **Offline Support**: Download lessons for offline access
5. **Multi-language**: Support multiple languages per lesson
6. **Content Analytics**: Track which content blocks are most effective
7. **Auto-validation**: Automatically validate new curriculum files
8. **Content Migration**: Tools to migrate old format to new format

---

## Conclusion

The curriculum loader service provides a robust, scalable solution for integrating curriculum JSON files with the BabySteps Digital School application. By following this guide, you can:

- ✅ Load lessons and question banks from the `curriculam/` folder
- ✅ Cache content for performance
- ✅ Integrate with existing microservices
- ✅ Build frontend components that consume curriculum data
- ✅ Monitor and optimize curriculum access

**Next Steps**:
1. Complete API endpoint implementation
2. Update existing services to use curriculum loader
3. Create frontend components for lesson display
4. Write comprehensive tests (99% coverage)
5. Deploy to staging for testing

For questions or issues, contact the BabySteps Development Team.
