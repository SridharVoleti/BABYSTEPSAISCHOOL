# 2025-11-26: Mentor Chat Service - Django REST Views (Ollama-backed with resilience)
# Author: BabySteps Development Team
# Updated: 2025-11-26 - Added robust Ollama client with connection pooling and retry logic

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import os
import json
import logging

# 2025-11-26: Import robust Ollama client
from .ollama_client import ollama_client

# 2025-11-26: Configure logging
logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

@csrf_exempt
@require_http_methods(["POST"])
@api_view(["POST"])
def chat(request):
    try:
        # Parse the request data
        try:
            if request.content_type == 'application/json':
                data = request.data
            else:
                data = json.loads(request.body)
        except (json.JSONDecodeError, Exception):
            return Response(
                {"success": False, "error": "Invalid JSON"},
                status=status.HTTP_400_BAD_REQUEST
            )

        message = data.get('message', '').strip()
        class_number = int(data.get('class_number', 1))  # Default to class 1 if not provided
        
        if not message:
            return Response(
                {"success": False, "error": "Message is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the appropriate teacher and their focus
        teacher = get_teacher_for_class(class_number)
        teacher_focus = teacher['focus']
        
        # Determine if the question is within this class's curriculum
        subject = get_subject_from_question(message, teacher_focus)
        
        # If no subject found, try to identify if it's a future topic
        if not subject:
            # Find which class typically covers this topic
            topic_class = find_topic_class(message, class_number)
            
            if topic_class > class_number:
                # Provide a simple explanation and mention when they'll learn more
                # 2025-11-26: Use robust Ollama client for future topic explanation
                system_prompt = (
                    f"You are {teacher['name']}, a science teacher for Class {class_number}. "
                    f"The student is asking about a topic typically covered in Class {topic_class}. "
                    "Provide a very simple, 1-2 sentence explanation with a basic example. "
                    f"Mention that they'll learn more about this in Class {topic_class}. "
                    "Keep it encouraging and age-appropriate."
                )
                
                try:
                    response_text = ollama_client.chat(
                        message=message,
                        system_prompt=system_prompt,
                        temperature=0.7
                    )
                except Exception as e:
                    logger.error(f"Ollama generation failed for future topic: {e}")
                    response_text = f"That's an interesting question! You'll learn more about this topic in Class {topic_class}."
                
                return Response({
                    "success": True,
                    "text": response_text,
                    "teacher": teacher['name'],
                    "class": class_number,
                    "subject": "Science",
                    "future_topic": True,
                    "tts": get_tts_config(class_number)
                })
            
            # If not a future topic, respond about current focus areas
            current_focus = [
                f"- {subject.capitalize()}: {teacher_focus[subject]}" 
                for subject in ['physics', 'chemistry', 'biology', 'earth_space'] 
                if teacher_focus[subject] != "None"
            ]
            
            return Response({
                "success": True,
                "text": (
                    f"I'm {teacher['name']}, your Class {class_number} science teacher. "
                    f"Your question seems to be about a different topic. Here's what we're focusing on:\n\n"
                    f"{chr(10).join(current_focus)}"
                ),
                "teacher": teacher['name'],
                "class": class_number,
                "subject": "Science",
                "tts": get_tts_config(class_number)
            })

        # If we get here, the question is within the current curriculum
        subject_focus = teacher_focus[subject]
        subject_name = {
            'physics': 'Physics',
            'chemistry': 'Chemistry',
            'biology': 'Biology',
            'earth_space': 'Earth & Space Science'
        }.get(subject, 'Science')

        # 2025-11-26: Prepare the prompt for Ollama
        system_prompt = (
            f"You are {teacher['name']}, a {teacher_focus['mode']} science teacher for Class {class_number}. "
            f"Your expertise includes: {subject_focus}. "
            "Explain concepts simply and engagingly, using age-appropriate language. "
            "If a question is beyond the class level, suggest they ask their teacher for more advanced topics. "
            "Keep responses concise and focused on the curriculum."
        )
        
        # 2025-11-26: Use robust Ollama client with retry logic
        try:
            response_text = ollama_client.chat(
                message=message,
                system_prompt=system_prompt,
                temperature=0.7
            )
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            # 2025-11-26: Provide helpful error message
            response_text = "I'm having trouble connecting right now. Please try again in a moment."
        
        return Response({
            "success": True,
            "text": response_text,
            "teacher": teacher['name'],
            "class": class_number,
            "subject": subject_name,
            "tts": get_tts_config(class_number)
        })

    except Exception as e:
        # 2025-11-26: Enhanced error handling with logging
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        
        # 2025-11-26: Check if it's a connection issue
        error_msg = str(e)
        if "connect" in error_msg.lower() or "timeout" in error_msg.lower():
            return Response({
                "success": False,
                "error": "Unable to connect to AI service. Please try again.",
                "details": str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response({
            "success": False,
            "error": "An error occurred processing your request",
            "details": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(["GET"])
def health_check(request):
    """
    2025-11-26: Health check endpoint to verify the service is running
    Uses robust Ollama client with caching
    """
    try:
        # 2025-11-26: Use robust health check from Ollama client
        is_healthy = ollama_client.health_check(force=True)
        
        if is_healthy:
            return Response({
                "success": True,
                "status": "healthy",
                "ollama_connected": True,
                "default_model": DEFAULT_MODEL,
                "circuit_breaker_state": ollama_client.circuit_breaker.state
            })
        else:
            return Response({
                "success": False,
                "status": "unhealthy",
                "ollama_connected": False,
                "error": f"Model {DEFAULT_MODEL} not available",
                "circuit_breaker_state": ollama_client.circuit_breaker.state
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response({
            "success": False,
            "status": "unhealthy",
            "ollama_connected": False,
            "error": str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

# Science teachers and their curriculum focus
SCIENCE_TEACHERS = {
    1: {
        "name": "Aarini",
        "focus": {
            "learning": "Curiosity & Observation",
            "physics": "None",
            "chemistry": "None",
            "biology": "Living vs Non-living",
            "earth_space": "Day & Night; Sun; Moon",
            "mode": "Observation & Storytelling"
        }
    },
    2: {
        "name": "Vaidehi",
        "focus": {
            "learning": "Exploring Living & Non-Living Things",
            "physics": "None",
            "chemistry": "None",
            "biology": "Parts of Body; Senses; Cleanliness",
            "earth_space": "Weather & Seasons",
            "mode": "Songs; Activities; Group Talk"
        }
    },
    3: {
        "name": "Samaira",
        "focus": {
            "learning": "Environment & Human Body Basics",
            "physics": "Push; Pull; Light; Shadows (Intro)",
            "chemistry": "Water; Air; Soil Basics",
            "biology": "Human Body Systems",
            "earth_space": "Water Cycle; Soil; Air",
            "mode": "Demonstrations; Experiments"
        }
    },
    4: {
        "name": "Ishani",
        "focus": {
            "learning": "Plants; Animals; Earth & Sky",
            "physics": "Simple Machines & Motion Basics",
            "chemistry": "Matter & Its Changes",
            "biology": "Plants & Animals in Detail",
            "earth_space": "Earth Layers & Solar System",
            "mode": "Hands-on Learning"
        }
    },
    5: {
        "name": "Mihira",
        "focus": {
            "learning": "Natural Resources & Simple Machines",
            "physics": "Forces & Simple Energy Forms",
            "chemistry": "States of Matter; Mixtures",
            "biology": "Life Cycles; Habitats",
            "earth_space": "Natural Resources & Environment",
            "mode": "Field Observation & Experiments"
        }
    },
    6: {
        "name": "Saanvi",
        "focus": {
            "learning": "Introduction to Physics; Chemistry; Biology",
            "physics": "Motion; Force; Energy; Work",
            "chemistry": "Elements; Compounds; Mixtures",
            "biology": "Cells; Tissues; Reproduction",
            "earth_space": "Earth Structure; Rocks; Weather",
            "mode": "Models & Charts"
        }
    },
    7: {
        "name": "Ritvika",
        "focus": {
            "learning": "Forces; Matter; Cells; Ecosystems",
            "physics": "Sound; Light; Magnetism Basics",
            "chemistry": "Air; Water; Acids; Bases",
            "biology": "Health; Diseases; Ecosystems",
            "earth_space": "Climate & Seasons",
            "mode": "Lab Work; Hypothesis Testing"
        }
    },
    8: {
        "name": "Anvika",
        "focus": {
            "learning": "Energy; Motion; Light; Life Processes",
            "physics": "Electricity & Heat Concepts",
            "chemistry": "Chemical Reactions Basics",
            "biology": "Human Anatomy & Evolution (Intro)",
            "earth_space": "Solar System & Gravity",
            "mode": "Data Collection & Interpretation"
        }
    },
    9: {
        "name": "Shrayathi",
        "focus": {
            "learning": "Physics: Motion; Energy | Chemistry: Reactions | Biology: Cells",
            "physics": "Motion Laws; Energy; Work",
            "chemistry": "Atoms; Elements; Periodic Table",
            "biology": "Genetics; Reproduction; Ecology",
            "earth_space": "Natural Resources; Pollution",
            "mode": "Practical Experiments"
        }
    },
    10: {
        "name": "Vyanjana",
        "focus": {
            "learning": "Integrated Science & Experiments | Environment Awareness",
            "physics": "Electricity; Magnetism; Light",
            "chemistry": "Chemical Bonding; Carbon Compounds",
            "biology": "Ecosystem & Environment",
            "earth_space": "Sustainability & Energy",
            "mode": "Quantitative Analysis"
        }
    },
    11: {
        "name": "Tanirika",
        "focus": {
            "learning": "Specialization in Physics; Chemistry; Biology",
            "physics": "Mechanics; Thermodynamics; Optics",
            "chemistry": "Physical; Inorganic; Organic Chemistry",
            "biology": "Plant Physiology; Genetics; Ecology",
            "earth_space": "Environmental Science (Optional)",
            "mode": "Theory + Experiments + Problem Solving"
        }
    },
    12: {
        "name": "Nishka",
        "focus": {
            "learning": "Advanced Theoretical & Experimental Science",
            "physics": "Electronics; Modern Physics; Waves",
            "chemistry": "Thermodynamics; Kinetics; Biomolecules",
            "biology": "Human Physiology; Evolution; Biotechnology",
            "earth_space": "Climate Science; Sustainability (Advanced)",
            "mode": "Research & Analytical Thinking"
        }
    }
}

def get_subject_from_question(question, teacher_focus):
    """Determine which subject the question relates to based on keywords."""
    question = question.lower()
    
    # Check physics keywords
    physics_terms = ['physics', 'force', 'energy', 'motion', 'light', 'sound', 
                    'electricity', 'magnetism', 'heat', 'optics', 'wave', 'electron',
                    'mechanics', 'thermodynamics', 'optics', 'electronics']
    if any(term in question for term in physics_terms) and teacher_focus['physics'] != "None":
        return "physics"
    
    # Check chemistry keywords
    chemistry_terms = ['chemistry', 'element', 'compound', 'reaction', 'acid', 
                      'base', 'matter', 'atom', 'molecule', 'chemical', 'bond',
                      'organic', 'inorganic', 'periodic', 'kinetics']
    if any(term in question for term in chemistry_terms) and teacher_focus['chemistry'] != "None":
        return "chemistry"
    
    # Check biology keywords
    biology_terms = ['biology', 'cell', 'plant', 'animal', 'human', 'body', 
                    'tissue', 'organ', 'ecosystem', 'reproduction', 'genetics',
                    'physiology', 'evolution', 'biotechnology', 'habitat']
    if any(term in question for term in biology_terms) and teacher_focus['biology'] != "None":
        return "biology"
    
    # Check earth/space keywords
    earth_terms = ['earth', 'space', 'weather', 'climate', 'rock', 'mineral', 
                  'planet', 'star', 'solar system', 'universe', 'sustainability',
                  'pollution', 'environment', 'atmosphere']
    if any(term in question for term in earth_terms) and teacher_focus['earth_space'] != "None":
        return "earth_space"
    
    return None

def get_teacher_for_class(class_number):
    """Get the appropriate teacher for the given class number (1-12)."""
    class_num = max(1, min(12, int(class_number)))
    return SCIENCE_TEACHERS.get(class_num, SCIENCE_TEACHERS[12])

def find_topic_class(topic, current_class):
    """Determine which class typically covers the given topic."""
    topic = topic.lower()
    
    # Define topic to class mapping
    topic_class_mapping = {
        # Physics topics
        'light': 7, 'sound': 7, 'magnetism': 7, 'electricity': 8, 'heat': 8,
        'motion': 9, 'force': 9, 'energy': 9, 'work': 9, 'optics': 11,
        'mechanics': 11, 'thermodynamics': 11, 'electronics': 12, 'waves': 12,
        
        # Chemistry topics
        'matter': 4, 'element': 6, 'compound': 6, 'reaction': 8, 'acid': 7,
        'base': 7, 'periodic table': 9, 'organic': 10, 'inorganic': 11,
        'biomolecules': 12, 'kinetics': 12,
        
        # Biology topics
        'cell': 6, 'tissue': 6, 'reproduction': 6, 'genetics': 9, 'evolution': 11,
        'biotechnology': 12, 'physiology': 11, 'ecosystem': 7, 'habitat': 5,
        
        # Earth/Space topics
        'solar system': 4, 'climate': 7, 'weather': 6, 'rock': 6, 'mineral': 6,
        'sustainability': 10, 'pollution': 9, 'atmosphere': 8
    }
    
    # Find the most relevant topic match
    for key, class_num in topic_class_mapping.items():
        if key in topic:
            return class_num
    
    # Default to next class if no specific match found
    return min(12, current_class + 1)

def get_tts_config(class_number):
    """Get TTS configuration based on class level."""
    rate = max(0.7, min(1.2, 0.7 + (class_number - 1) * 0.05))  # 0.7 to 1.2 range
    return {
        "enabled": True,
        "rate": rate,
        "pitch": 1.0,
        "voice": "female",
        "language": "en-IN"
    }