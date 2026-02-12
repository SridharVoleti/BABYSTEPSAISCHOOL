# 2025-11-14: Student Mentor Agent (VidyaAI) - LangChain + Ollama (LLaMA 3.2)
# Author: BabySteps Development Team
# Purpose: Single-agent CLI that adapts lesson pacing based on student comprehension

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    # LangChain community provider for Ollama
    from langchain_community.llms import Ollama  # type: ignore
except Exception as e:  # pragma: no cover
    print("[ERROR] Missing dependency: langchain-community.\n"
          "Run: pip install -r services/student_mentor_agent/requirements.txt")
    raise

# ----------------------
# 1. LLaMA 3.2 Model Setup
# ----------------------

def get_llm(model: str = "llama3.2", temperature: float = 0.6) -> Ollama:
    """Create an Ollama LLM instance.

    Requires local Ollama daemon and model pulled:
      - Install Ollama: https://ollama.ai
      - Start service (Windows): ollama serve
      - Pull model: ollama pull llama3.2

    Configure remote/base URL via environment variable if running inside Docker:
      - OLLAMA_BASE_URL (e.g., http://host.docker.internal:11434)
    """
    base_url = os.getenv("OLLAMA_BASE_URL")
    if base_url:
        return Ollama(model=model, temperature=temperature, base_url=base_url)
    return Ollama(model=model, temperature=temperature)


# ----------------------
# 2. Student Memory Store (simple JSON file)
# ----------------------

# Persist memory next to this script so it doesn't pollute project root
BASE_DIR = Path(__file__).resolve().parent
MEMORY_FILE = BASE_DIR / "student_memory.json"
REPO_ROOT = BASE_DIR.parent.parent  # project root
CURRICULAM_ROOT = REPO_ROOT / "curriculam"


def init_memory() -> dict:
    """Initialize or load student memory from JSON file."""
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            memory = json.load(f)
    except FileNotFoundError:
        memory = {
            "student_id": "S001",
            "current_topic": "Magnetism",
            "mode": "A",  # A = slower pacing; B = slightly faster
            "correct_streak": 0,
            "mastery_score": 0.4,
        }
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=4)
    return memory


def save_memory(memory: dict) -> None:
    """Persist updated memory to disk."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4)


# ----------------------
# 2b. Curriculum JSON Loader
# ----------------------

def find_lesson_file(class_number: int, subject: str, month: int, week: int, day: int) -> Optional[Path]:
    subject_folder = CURRICULAM_ROOT / f"class{class_number}" / subject / f"Month{month}" / f"Week_{week}" / "Lessons"
    if not subject_folder.exists():
        return None
    pattern = f"*_C{class_number}_M{month}_W{week}_D{day}.json"
    matches = list(subject_folder.glob(pattern))
    return matches[0] if matches else None


def find_qb_file(class_number: int, subject: str, month: int, week: int, day: int) -> Optional[Path]:
    qb_folder = CURRICULAM_ROOT / f"class{class_number}" / subject / f"Month{month}" / f"Week_{week}" / "Questions_Banks"
    if not qb_folder.exists():
        return None
    pattern = f"*_C{class_number}_M{month}_W{week}_D{day}_QB.json"
    matches = list(qb_folder.glob(pattern))
    return matches[0] if matches else None


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------
# 3. Generate Response Function
# ----------------------

def generate_response(llm: Ollama, student_input: str, memory: dict) -> str:
    """Generate a teacher-style response tailored to pacing mode."""
    system_prompt = f"""
You are VidyaAI, a patient and gentle teacher for children aged 8–10.
You are teaching the topic: {memory['current_topic']}.
Your teaching mode is {memory['mode']}.

Teaching guidelines:
- Assume the student learns slowly by default.
- Mode A: Explain slowly, use simple Indian examples, one concept at a time.
- Mode B: Explain slightly faster with a bit more detail.
- Always maintain a kind and encouraging tone.
- Never overwhelm the student.
- After every explanation, ask one short question to check understanding.
- Encourage curiosity and praise every small success.

You must never mention you are an AI or language model.
Your goal is to help the student truly understand the concept.
""".strip()

    full_prompt = system_prompt + f"\nStudent says: {student_input}\nVidyaAI:"

    # Newer LangChain versions prefer .invoke(); fallback to callable if needed
    try:
        response = llm.invoke(full_prompt)  # type: ignore[attr-defined]
    except AttributeError:
        response = llm(full_prompt)  # type: ignore[call-arg]
    return str(response).strip()


# ----------------------
# 4. Update Mastery Function
# ----------------------

def update_mastery(memory: dict, correct: bool) -> None:
    """Update mastery score and mode based on correctness feedback."""
    if correct:
        memory["correct_streak"] += 1
        memory["mastery_score"] += 0.1
    else:
        memory["correct_streak"] = 0
        memory["mastery_score"] -= 0.05

    # Switch pacing mode
    if memory["correct_streak"] >= 2 and memory["mastery_score"] > 0.7:
        memory["mode"] = "B"
    elif memory["mastery_score"] < 0.5:
        memory["mode"] = "A"

    # Clamp score to [0, 1]
    memory["mastery_score"] = round(max(0.0, min(memory["mastery_score"], 1.0)), 2)
    save_memory(memory)


# ----------------------
# 4b. Run Lesson and Activities from JSON
# ----------------------

def run_ai_coach(llm: Ollama, coach: Dict[str, Any]) -> None:
    prompt = coach.get("ai_prompt", "Share your answer.")
    print(f"\n🤖 AI Coach: {prompt}")
    user = input("You: ")

    # Evaluate with LLM for friendliness
    eval_prompt = (
        "You are a primary teacher. Evaluate the student's short response for clarity and correctness. "
        "Give one short encouraging feedback and one tiny suggestion if needed.\n\n"
        f"Prompt: {prompt}\nStudent: {user}\nTeacher Feedback:"
    )
    try:
        try:
            feedback = llm.invoke(eval_prompt)  # type: ignore[attr-defined]
        except AttributeError:
            feedback = llm(eval_prompt)  # type: ignore[call-arg]
        print(f"\n📝 Feedback: {str(feedback).strip()}\n")
    except Exception:
        print("\n📝 Feedback: Great try! Let's keep practicing.\n")


def run_lesson_from_json(llm: Ollama, lesson: Dict[str, Any]) -> Dict[str, Any]:
    meta = lesson.get("metadata", {})
    blocks: List[Dict[str, Any]] = lesson.get("content_blocks", [])
    total_points = 0
    earned_points = 0

    title = meta.get("lesson_title", "Lesson")
    print(f"\n===== {title} =====")

    for idx, block in enumerate(blocks, start=1):
        btype = block.get("type", "content")
        text = block.get("text", "")
        pts = int(block.get("points_awarded", 0))
        total_points += pts
        print(f"\n[{idx}/{len(blocks)}] {btype.replace('_', ' ').title()}")
        print(f"{text}\n")

        coach = block.get("ai_expression_coach")
        if coach and coach.get("enabled"):
            run_ai_coach(llm, coach)
            earned_points += int(coach.get("points_awarded", 0))
        else:
            # Simple comprehension check per block
            ans = input("Press Enter to continue or type 'q' to skip: ")
            if ans.strip().lower() != 'q':
                earned_points += pts

    print(f"\n🎯 Lesson Complete! Points: {earned_points}/{total_points}\n")
    return {"earned_points": earned_points, "total_points": total_points}


# ----------------------
# 4c. Run Question Bank
# ----------------------

def evaluate_open_response(llm: Ollama, question: Dict[str, Any], user: str) -> bool:
    qtext = question.get("question_text", "")
    target = question.get("expected_answer") or question.get("expected_keywords", [])
    rubric = (
        "Evaluate if the student's answer is reasonable and aligns with the expected idea. "
        "Reply only with 'Correct' or 'Incorrect'."
    )
    prompt = f"Question: {qtext}\nExpected: {target}\nStudent: {user}\n{rubric}"
    try:
        try:
            out = llm.invoke(prompt)  # type: ignore[attr-defined]
        except AttributeError:
            out = llm(prompt)  # type: ignore[call-arg]
        verdict = str(out).strip().lower()
        return verdict.startswith("correct")
    except Exception:
        return False


def run_question_bank(llm: Ollama, qb: Dict[str, Any]) -> Dict[str, Any]:
    questions = qb.get("questions", [])
    score = 0
    max_score = int(qb.get("max_score", 0)) or sum(int(q.get("points", 0)) for q in questions)

    print("\n===== Quick Check =====")
    for q in questions:
        qtype = q.get("type")
        text = q.get("question_text", "")
        points = int(q.get("points", 0))
        print(f"\n{qtype.title() if qtype else 'Question'}: {text}")

        user = input("Your answer: ").strip()

        correct = False
        if qtype == "multiple_choice":
            # show options
            opts = q.get("options", [])
            if opts:
                print(f"Options: {', '.join(opts)}")
            correct = user.lower() == str(q.get("correct_answer", "")).lower()
        elif qtype == "true_false":
            correct = user.lower() in {str(q.get("correct_answer", "")).lower(),
                                       ("true" if str(q.get("correct_answer", "")).lower() == "true" else "false")} 
        elif qtype == "fill_in_blank":
            correct = user.strip().lower() == str(q.get("correct_answer", "")).strip().lower()
        else:
            # voice_response, reasoning, others -> LLM judge
            correct = evaluate_open_response(llm, q, user)

        if correct:
            print("✅ Correct!")
            score += points
        else:
            print(f"❌ Correct answer: {q.get('correct_answer', 'See explanation')}")

    print(f"\n📝 Assessment Score: {score}/{max_score}\n")
    return {"score": score, "max_score": max_score}


# ----------------------
# 5. Simple Interaction Loop (CLI)
# ----------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="VidyaAI - Student Mentor Agent")
    parser.add_argument("--class_num", type=int, default=1)
    parser.add_argument("--subject", type=str, default="EVS")
    parser.add_argument("--month", type=int, default=1)
    parser.add_argument("--week", type=int, default=1)
    parser.add_argument("--day", type=int, default=1)
    parser.add_argument("--skip_qb", action="store_true")
    args = parser.parse_args()

    try:
        llm = get_llm()
    except Exception as e:  # pragma: no cover
        print("[ERROR] Could not initialize Ollama LLM.\n\n"
              "Make sure Ollama is installed, running, and the model is pulled:\n"
              "  1) Install: https://ollama.ai\n"
              "  2) Start service:  ollama serve\n"
              "  3) Pull model:     ollama pull llama3.2\n"
              "  4) If running inside Docker, set OLLAMA_BASE_URL= http://host.docker.internal:11434\n\n"
              f"Details: {e}")
        sys.exit(1)

    # Load lesson JSON
    lesson_path = find_lesson_file(args.class_num, args.subject, args.month, args.week, args.day)
    if not lesson_path:
        print("[ERROR] Lesson JSON not found in curriculam/. Check class/subject/month/week/day.")
        print(f"Looked under: {CURRICULAM_ROOT / f'class{args.class_num}' / args.subject / f'Month{args.month}' / f'Week_{args.week}' / 'Lessons'}")
        sys.exit(2)

    lesson_json = load_json(lesson_path)

    # Update memory topic from JSON metadata
    memory = init_memory()
    topic_name = lesson_json.get("metadata", {}).get("lesson_title") or memory.get("current_topic", "Magnetism")
    memory["current_topic"] = topic_name
    save_memory(memory)

    print(f"\n🎓 VidyaAI: We'll learn '{topic_name}'. Lesson file: {lesson_path.name}")
    run_lesson_from_json(llm, lesson_json)

    if not args.skip_qb:
        qb_path = find_qb_file(args.class_num, args.subject, args.month, args.week, args.day)
        if qb_path and qb_path.exists():
            qb = load_json(qb_path)
            run_question_bank(llm, qb)
        else:
            print("\n(No question bank found for this lesson.)\n")

    print("VidyaAI: Great job today! 🌸")


if __name__ == "__main__":
    main()
