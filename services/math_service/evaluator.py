"""
2026-03-02: Ground-Truth RAG Evaluator for math problems (BS-MTH module).

Purpose:
    Evaluate student answers against pre-verified worked solutions from
    the JSON problem bank. Uses direct comparison for MCQ and numeric_fill;
    uses LLM (anchored to the correct solution) for word_problem types.
    The LLM never computes answers — it only compares and gives Socratic feedback.
"""

import json  # 2026-03-02: JSON parsing for LLM response
import logging  # 2026-03-02: Module logger

logger = logging.getLogger(__name__)  # 2026-03-02: Logger


class MathEvaluator:
    """
    2026-03-02: Ground-Truth RAG pattern evaluator for math problems.

    Routes to direct comparison or LLM-anchored evaluation based on
    problem type. LLM is never asked to compute — only to judge.
    """

    @staticmethod
    def evaluate(problem: dict, student_answer: str) -> dict:
        """
        2026-03-02: Evaluate a student answer against the pre-verified solution.

        MCQ and numeric_fill use direct comparison (no LLM call).
        Word problems use LLM evaluation anchored to the worked solution.

        Args:
            problem: Problem dict from JSON (must contain type, correct_answer,
                     worked_solution).
            student_answer: Student's raw answer string.

        Returns:
            dict: {is_correct, feedback, correct_answer, worked_steps}
        """
        problem_type = problem.get('type', 'mcq')  # 2026-03-02: Get problem type

        if problem_type in ('mcq', 'numeric_fill'):  # 2026-03-02: Direct comparison
            return MathEvaluator._direct_eval(problem, student_answer)

        # 2026-03-02: Word problem — use LLM-anchored evaluation
        return MathEvaluator._llm_eval(problem, student_answer)

    @staticmethod
    def _direct_eval(problem: dict, student_answer: str) -> dict:
        """
        2026-03-02: Direct comparison evaluation (no LLM).

        Normalises student_answer by stripping whitespace and attempting
        numeric comparison. For MCQ, correct_answer is an index (int)
        into the options list.

        Args:
            problem: Problem dict with correct_answer and worked_solution.
            student_answer: Student's raw answer string.

        Returns:
            dict: {is_correct, feedback, correct_answer, worked_steps}
        """
        correct = problem.get('correct_answer')  # 2026-03-02: Ground truth
        worked = problem.get('worked_solution', {})  # 2026-03-02: Worked solution
        explanation = worked.get('explanation', '')  # 2026-03-02: Explanation text
        worked_steps = worked.get('steps', [])  # 2026-03-02: Step list

        # 2026-03-02: Normalise student answer
        cleaned = student_answer.strip()  # 2026-03-02: Strip whitespace

        problem_type = problem.get('type', 'mcq')  # 2026-03-02: Type

        if problem_type == 'mcq':  # 2026-03-02: MCQ: correct_answer is int index
            # 2026-03-02: Student may submit index as string or the option text
            is_correct = False  # 2026-03-02: Default

            # 2026-03-02: First try as integer index comparison
            try:
                student_idx = int(cleaned)  # 2026-03-02: Try as index
                is_correct = student_idx == int(correct)  # 2026-03-02: Compare indices
            except (ValueError, TypeError):  # 2026-03-02: Not parseable as int
                pass

            # 2026-03-02: Also check if student typed the option text directly
            if not is_correct:
                options = problem.get('options', [])  # 2026-03-02: Option list
                correct_idx = int(correct) if isinstance(correct, (int, str)) else -1
                if 0 <= correct_idx < len(options):
                    correct_text = options[correct_idx]  # 2026-03-02: Text of correct option
                    is_correct = cleaned.lower() == correct_text.lower()  # 2026-03-02: Text compare

            # 2026-03-02: Build human-readable correct answer
            options = problem.get('options', [])  # 2026-03-02: All options
            correct_display = (  # 2026-03-02: Show option text if possible
                options[int(correct)] if isinstance(correct, int) and 0 <= int(correct) < len(options)
                else str(correct)
            )
        else:  # 2026-03-02: numeric_fill
            is_correct = False  # 2026-03-02: Default
            try:
                student_num = float(cleaned)  # 2026-03-02: Parse student answer
                correct_num = float(str(correct))  # 2026-03-02: Parse correct answer
                is_correct = abs(student_num - correct_num) < 1e-6  # 2026-03-02: Float compare
            except (ValueError, TypeError):  # 2026-03-02: Non-numeric — string compare
                is_correct = cleaned.lower() == str(correct).lower()

            correct_display = str(correct)  # 2026-03-02: Show numeric answer

        feedback = (  # 2026-03-02: Build feedback
            explanation if is_correct
            else f"Not quite. {explanation}"
        )

        return {  # 2026-03-02: Result dict
            'is_correct': is_correct,
            'feedback': feedback,
            'correct_answer': correct_display,
            'worked_steps': worked_steps,
        }

    @staticmethod
    def _llm_eval(problem: dict, student_answer: str) -> dict:
        """
        2026-03-02: LLM-anchored evaluation for word problems.

        Feeds the pre-verified worked solution to the LLM as ground truth.
        The LLM is asked to compare — never to compute. Falls back to direct
        comparison if the LLM fails or returns malformed JSON.

        Args:
            problem: Problem dict with question, worked_solution, correct_answer.
            student_answer: Student's raw answer string.

        Returns:
            dict: {is_correct, feedback, correct_answer, worked_steps}
        """
        worked = problem.get('worked_solution', {})  # 2026-03-02: Pre-verified solution
        steps = worked.get('steps', [])  # 2026-03-02: Step list
        correct_answer = worked.get('answer', str(problem.get('correct_answer', '')))  # 2026-03-02: Correct answer
        worked_steps = steps  # 2026-03-02: For return value

        # 2026-03-02: Build evaluation prompt — LLM compares, never computes
        steps_text = '\n'.join(f"  Step {i + 1}: {s}" for i, s in enumerate(steps))  # 2026-03-02: Format
        prompt = (
            f"MATH PROBLEM:\n{problem.get('question', '')}\n\n"
            f"PRE-VERIFIED CORRECT SOLUTION:\n{steps_text}\n"
            f"CORRECT ANSWER: {correct_answer}\n\n"
            f"STUDENT'S ANSWER: {student_answer}\n\n"
            "Your task: Determine if the student's answer is correct by comparing it "
            "to the CORRECT ANSWER above. Do NOT recompute — just compare.\n"
            "Give one sentence of Socratic feedback appropriate for a primary school child.\n"
            "Respond ONLY with valid JSON:\n"
            '{"is_correct": true/false, "feedback": "one sentence feedback"}'
        )

        try:
            from services.llm_service.factory import get_llm_provider  # 2026-03-02: LLM factory
            llm = get_llm_provider()  # 2026-03-02: Get configured provider
            response = llm.chat(  # 2026-03-02: LLM call
                message=prompt,
                system_prompt='You are a math teacher evaluator. Respond only with valid JSON.',
            )
            raw_text = response.text.strip()  # 2026-03-02: Raw LLM output

            # 2026-03-02: Extract JSON from response (handle markdown code blocks)
            if '```' in raw_text:  # 2026-03-02: Strip markdown fences
                raw_text = raw_text.split('```')[1]  # 2026-03-02: Get content
                if raw_text.startswith('json'):  # 2026-03-02: Strip language tag
                    raw_text = raw_text[4:]
            raw_text = raw_text.strip()  # 2026-03-02: Clean whitespace

            result = json.loads(raw_text)  # 2026-03-02: Parse JSON
            is_correct = bool(result.get('is_correct', False))  # 2026-03-02: Extract bool
            feedback = str(result.get('feedback', ''))  # 2026-03-02: Extract feedback

        except Exception as exc:  # 2026-03-02: LLM error — fall back to direct compare
            logger.warning("LLM eval failed, falling back to direct compare: %s", exc)
            return MathEvaluator._direct_string_eval(problem, student_answer, worked_steps)

        return {  # 2026-03-02: Result dict
            'is_correct': is_correct,
            'feedback': feedback,
            'correct_answer': correct_answer,
            'worked_steps': worked_steps,
        }

    @staticmethod
    def _direct_string_eval(problem: dict, student_answer: str, worked_steps: list) -> dict:
        """
        2026-03-02: Fallback string comparison for word problems when LLM unavailable.

        Args:
            problem: Problem dict.
            student_answer: Student's raw answer string.
            worked_steps: Pre-extracted step list.

        Returns:
            dict: Evaluation result using string comparison.
        """
        worked = problem.get('worked_solution', {})  # 2026-03-02: Worked solution
        correct = worked.get('answer', str(problem.get('correct_answer', '')))  # 2026-03-02: Correct
        cleaned = student_answer.strip().lower()  # 2026-03-02: Normalise student answer
        correct_clean = str(correct).strip().lower()  # 2026-03-02: Normalise correct

        # 2026-03-02: Try numeric comparison first
        is_correct = False  # 2026-03-02: Default
        try:
            is_correct = abs(float(cleaned) - float(correct_clean)) < 1e-6  # 2026-03-02: Numeric
        except (ValueError, TypeError):  # 2026-03-02: Non-numeric — string compare
            is_correct = cleaned == correct_clean

        feedback = (  # 2026-03-02: Build feedback
            worked.get('explanation', 'Correct!')
            if is_correct
            else f"Not quite. The answer is {correct}."
        )

        return {  # 2026-03-02: Result dict
            'is_correct': is_correct,
            'feedback': feedback,
            'correct_answer': str(correct),
            'worked_steps': worked_steps,
        }

    @staticmethod
    def generate_hint(problem: dict, hint_number: int) -> str:
        """
        2026-03-02: Generate a progressive hint for a problem.

        hint_number=1 → return problem['hint'] (no LLM)
        hint_number=2 → LLM rephrases step 1 of worked solution as a question
        hint_number=3 → LLM reveals step 1 of the worked solution directly

        Args:
            problem: Problem dict with hint and worked_solution fields.
            hint_number: Which hint level (1, 2, or 3).

        Returns:
            str: Hint text.
        """
        basic_hint = problem.get('hint', 'Think carefully about what the problem is asking.')  # 2026-03-02: Default

        if hint_number <= 1:  # 2026-03-02: Level 1: basic hint from JSON
            return basic_hint  # 2026-03-02: Return direct hint

        worked = problem.get('worked_solution', {})  # 2026-03-02: Worked solution
        steps = worked.get('steps', [])  # 2026-03-02: Steps list
        step_1 = steps[0] if steps else ''  # 2026-03-02: First step

        if not step_1:  # 2026-03-02: No steps available
            return basic_hint  # 2026-03-02: Fall back to basic hint

        if hint_number == 2:  # 2026-03-02: Level 2: rephrase as guiding question
            prompt = (  # 2026-03-02: Build prompt
                f"You are a primary school maths teacher. The student needs a hint for this problem:\n"
                f"{problem.get('question', '')}\n\n"
                f"The first step of the solution is: {step_1}\n\n"
                "Rephrase this step as a gentle guiding question for the child. "
                "Keep it short (one sentence)."
            )
            try:
                from services.llm_service.factory import get_llm_provider  # 2026-03-02: LLM
                llm = get_llm_provider()  # 2026-03-02: Get provider
                response = llm.chat(message=prompt, system_prompt='You are a helpful maths teacher.')
                return response.text.strip()  # 2026-03-02: LLM hint
            except Exception as exc:  # 2026-03-02: Fallback on error
                logger.warning("Hint LLM call failed: %s", exc)
                return basic_hint  # 2026-03-02: Fall back

        # 2026-03-02: Level 3: reveal step 1 directly
        return f"Here's a clue: {step_1}"  # 2026-03-02: Direct reveal
