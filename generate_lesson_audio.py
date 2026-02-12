#!/usr/bin/env python3
"""
# 2025-10-17: Generate pre-recorded audio files for Lesson 1 Read-Along activity
# Authors: Sridhar
# Contact: sridhar@babystepsdigitalschool.com
# Last Modified: 2025-10-17
"""

import os
import sys
import json
from pathlib import Path

# Set Django settings before importing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Add backend to path to import TTS service
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

try:
    import django
    django.setup()
    
    # Debug pyttsx3
    try:
        import pyttsx3
        print(f"✅ pyttsx3 imported: {pyttsx3}")
        
        # Try to create engine
        engine = pyttsx3.init()
        print(f"✅ pyttsx3 engine created: {engine}")
        
        voices = engine.getProperty('voices')
        print(f"✅ Voices found: {len(voices)}")
        for i, voice in enumerate(voices):
            print(f"  {i}: {voice.name}")
            
    except Exception as e:
        print(f"❌ pyttsx3 error: {e}")
        sys.exit(1)
    
    from apps.ai_services.tts_service import tts_service
    print(f"✅ TTS service object: {tts_service}")
    
    if tts_service is None:
        print("❌ TTS service is None")
        sys.exit(1)
        
    print("✅ TTS service imported successfully")
except ImportError as e:
    print(f"❌ Failed to import TTS service: {e}")
    sys.exit(1)

def generate_readalong_audio():
    """Generate audio files for Lesson 1 read-along activity"""

    # Output directory
    output_dir = Path(__file__).parent / 'frontend' / 'public' / 'audio' / 'class1' / 'lesson1' / 'readalong'
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")

    # Read-along text from lesson summary
    full_text = """The Wise Owl lives in a quiet forest. Every night the owl sits on a high branch and watches the animals. The owl is called wise because it listens first, thinks carefully, and then helps the other animals by giving good advice. In the story, a rabbit worries about a lost path and the owl helps by asking questions and noticing small traces on the ground. The animals learn that listening and thinking calmly are important when solving problems."""

    # Split into sentences (simple split on periods)
    sentences = [s.strip() + '.' for s in full_text.split('.') if s.strip()]

    print(f"📝 Found {len(sentences)} sentences to generate audio for")

    # Generate audio for each sentence
    generated_files = []

    for i, sentence in enumerate(sentences, 1):
        filename = f"sentence_{i}.wav"
        output_path = output_dir / filename

        print(f"🎤 Generating audio for sentence {i}: {sentence[:50]}...")

        try:
            # Use female voice for the read-along (Ollie the Owl)
            audio_path = tts_service.synthesize_text(
                text=sentence,
                output_path=str(output_path),
                speed=0.8,  # Slower for children
                speaker='female'  # Use female voice
            )

            file_size = os.path.getsize(audio_path)
            print(f"✅ Generated {filename} ({file_size} bytes)")

            generated_files.append({
                'sentence_number': i,
                'text': sentence,
                'filename': filename,
                'file_size': file_size
            })

        except Exception as e:
            print(f"❌ Failed to generate audio for sentence {i}: {e}")
            continue

    # Save metadata
    metadata = {
        'lesson_id': 'ENG1_MRIDANG_01',
        'activity_id': 'A1_read_along',
        'total_sentences': len(sentences),
        'generated_files': generated_files,
        'voice': 'female',
        'speed': 0.8
    }

    metadata_path = output_dir / 'metadata.json'
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated {len(generated_files)} audio files")
    print(f"📄 Metadata saved to {metadata_path}")

    return generated_files

if __name__ == '__main__':
    if tts_service is None:
        print("❌ TTS service not available")
        sys.exit(1)

    generate_readalong_audio()
