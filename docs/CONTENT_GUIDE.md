# BabySteps Digital School — Content Authoring Guide

Every week of content for a subject consists of **three files**:

| File | Purpose | Location |
|------|---------|----------|
| `week{W}.json` | 4 micro-lessons (Days 1–4) + Day 5 weekly assessment | `json/teaching/class{N}/{Subject}/week{W}.json` |
| `week{W}_practice.json` | Adaptive practice bank (15 questions per day × 4 days) | `json/teaching/class{N}/{Subject}/week{W}_practice.json` |
| `grade{N}.json` | Vocabulary word list (30 words per language per grade) | `json/vocabulary/{Language}/grade{N}.json` |

Copy the templates from `json/templates/` and fill in the placeholders.
All `TODO:` markers must be replaced before the file is used.

---

## 1. File Naming & Folder Structure

```
json/
├── teaching/
│   ├── class1/
│   │   ├── English/
│   │   │   ├── week1.json
│   │   │   ├── week1_practice.json
│   │   │   ├── week2.json
│   │   │   └── week2_practice.json
│   │   ├── Mathematics/
│   │   ├── EVS/
│   │   ├── Hindi/
│   │   └── Telugu/
│   ├── class2/
│   │   └── ...
│   └── class12/
│       └── ...
└── vocabulary/
    ├── English/
    │   ├── grade1.json
    │   └── grade2.json
    ├── Hindi/
    └── Telugu/
```

**Subject folder names** (use exactly as written — the system is case-sensitive):

| Class | Subjects |
|-------|---------|
| 1–5 | `English`, `Mathematics`, `EVS`, `Hindi`, `Telugu` |
| 6–8 | `English`, `Mathematics`, `Science`, `Social_Studies`, `Hindi`, `Telugu` |
| 9–10 | `English`, `Mathematics`, `Physics`, `Chemistry`, `Biology`, `History`, `Geography`, `Hindi`, `Telugu` |
| 11–12 | `English`, `Mathematics`, `Physics`, `Chemistry`, `Biology`, `History`, `Political_Science`, `Economics` |

---

## 2. ID Naming Convention

All IDs are used internally by the system to identify content. Keep them unique.

| ID Field | Pattern | Example |
|----------|---------|---------|
| `lesson_id` | `{SUBJ}{CLASS}_{BOOK}_W{WW}` | `ENG1_MRIDANG_W01` |
| `chapter_id` | `{BOOK}_CH{NN}` | `MRIDANG_CH01` |
| `micro_lesson_id` | `{lesson_id}_D{N}` | `ENG1_MRIDANG_W01_D1` |
| `assessment_id` | `{lesson_id}_ASSESS` | `ENG1_MRIDANG_W01_ASSESS` |
| Daily activity ID | `D{day}_A{N}` | `D1_A1` |
| Daily practice Q ID | `W{WW}_D{N}_P_{E\|M\|H}{N}` | `W01_D1_P_E1` |
| Assessment Q ID | `WA_Q{N}` | `WA_Q1` |

**Subject codes:**

| Subject | Code |
|---------|------|
| English | `ENG` |
| Mathematics | `MAT` |
| EVS / Science | `SCI` |
| Social Studies | `SST` |
| Hindi | `HIN` |
| Telugu | `TEL` |
| Physics | `PHY` |
| Chemistry | `CHE` |
| Biology | `BIO` |
| History | `HIS` |
| Geography | `GEO` |

**Week padding:** Always zero-pad to 2 digits: `W01`, `W02`, ... `W36`.

---

## 3. IQ Levels — Three Variants for Every Lesson

Every teaching day has **three** content variants keyed by `foundation`, `standard`, `advanced`:

| Key | IQ Range | Audience | Style |
|-----|----------|----------|-------|
| `foundation` | IQ < 90 | Needs more support | Spell words aloud letter-by-letter, short sentences, 3× repetition, slow TTS (0.7) |
| `standard` | IQ 90–120 | Grade level | Normal sentences, 2× repetition, normal TTS (0.9) |
| `advanced` | IQ > 120 | Above grade level | Deeper thinking, connections to real life, 1× repetition, faster TTS (1.1) |

**Rules:**
- All three variants must cover the **same concept** — only depth and pacing differ
- `foundation` must spell out new words: `"Say FOREST. F-O-R-E-S-T. Forest."`
- `advanced` should end with a reflection or application question
- `revision_prompts` (Days 2–4) must also have all three variants — foundation prompts recall single words, advanced asks for synthesis

---

## 4. week{W}.json — Field Reference

### Top-level fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `lesson_id` | string | ✅ | Unique, follows naming convention |
| `class` | integer | ✅ | 1–12 |
| `subject` | string | ✅ | Must match folder name exactly |
| `chapter_id` | string | ✅ | Textbook chapter reference |
| `chapter_title` | string | ✅ | Title as it appears in the textbook |
| `character` | string | ✅ | AI tutor character name for this lesson (friendly animal or person) |
| `week_number` | integer | ✅ | 1–36 |
| `learning_objectives` | array of strings | ✅ | 4–6 objectives; start each with a verb (Identify/Explain/Use/Retell/Pronounce) |
| `micro_lessons` | array | ✅ | Exactly 4 items (Day 1–4). See below. |
| `weekly_assessment` | object | ✅ | Day 5 quiz. See below. |

### micro_lesson fields (per day)

| Field | Type | Required | Days | Notes |
|-------|------|----------|------|-------|
| `day` | integer | ✅ | 1–4 | |
| `micro_lesson_id` | string | ✅ | all | |
| `title` | string | ✅ | all | Short, child-friendly title |
| `duration_minutes` | integer | ✅ | all | Target: 10 |
| `revision_prompts` | object | ✅ | 2–4 only | Three IQ variants, each an array of 2–3 strings. Omit on Day 1. |
| `teaching_content` | object | ✅ | all | Three IQ variants. See below. |
| `vocabulary` | array | ✅ | all | 3 words per day × 4 days = 12 unique words for the week |
| `dialogue_flow` | array | ✅ | all | 4 stages: greeting → concept → activity → wrapup |
| `activities` | array | ✅ | all | 1 activity per day |
| `practice_questions` | array | ✅ | all | 3 MCQs per day (used in the lesson itself, not the practice bank) |
| `read_along` | object | ✅ | all | 3 languages, 4 sentences each |

### teaching_content variant fields

| Field | Type | Notes |
|-------|------|-------|
| `concept_text` | string | The spoken lesson text. Foundation: 60–100 words. Standard: 80–120 words. Advanced: 100–150 words. |
| `pacing` | string | `"slow"` / `"normal"` / `"fast"` |
| `repetition_count` | integer | Foundation: 3, Standard: 2, Advanced: 1 |
| `tts_rate` | float | Foundation: 0.7, Standard: 0.9, Advanced: 1.1 |

### vocabulary item fields

| Field | Type | Notes |
|-------|------|-------|
| `word` | string | Lowercase |
| `definition` | string | Child-friendly, one sentence, max 12 words |
| `image_hint` | string | Filename hint for future image lookup (e.g. `"owl.png"`) |

### dialogue_flow stages (exactly 4, in order)

| Stage | Purpose |
|-------|---------|
| `greeting` | Character introduces themselves or re-enters; hooks the child |
| `concept` | Character previews the lesson topic |
| `activity` | Character prompts the child to try the activity |
| `wrapup` | Character celebrates and previews tomorrow |

### activity types

| `type` | Required fields | Notes |
|--------|----------------|-------|
| `matching` | `instructions`, `items[]` with `word`/`match` pairs | Good for vocabulary days |
| `sequencing` | `instructions`, `items[]` with `position`/`text` | Good for story days |

All activities need `"scoring": {"correct_xp": N}` where N is 5–15.

### practice_questions (3 per day, inline in lesson)

All three must be `"type": "mcq"` with:
- `options`: array of 3 strings
- `correct_answer`: 0-indexed integer (0, 1, or 2)
- `hint`: one sentence pointing toward the answer without giving it away

### read_along fields

4 sentences per language. Each sentence should be a complete, simple sentence from the lesson's core idea.

| Language | `transliterations` |
|----------|--------------------|
| `English` | Empty array `[]` |
| `Hindi` | Romanized phonetic (IAST-inspired, readable) |
| `Telugu` | Romanized phonetic (readable by non-Telugu speakers) |

### weekly_assessment fields

| Field | Type | Notes |
|-------|------|-------|
| `assessment_id` | string | `{lesson_id}_ASSESS` |
| `title` | string | "Week N Assessment: {Chapter Title}" |
| `time_limit_minutes` | integer | 15 |
| `questions` | array | Exactly 10 MCQs. Each has 4 options. `points`: 2 per question (total 20). |
| `star_thresholds` | object | `one_star`: 40, `two_stars`: 60, `three_stars`: 80 (percentage) |

Assessment questions should test all 12 vocabulary words and the main concept. Distribute across: 4 vocabulary recall + 3 comprehension + 2 application + 1 moral/synthesis.

---

## 5. week{W}_practice.json — Field Reference

This file powers the **adaptive mastery practice** (the 5-star system). Each day has 15 questions split into 3 difficulties × 5 questions.

### Top-level fields

| Field | Notes |
|-------|-------|
| `lesson_id` | Must match the `lesson_id` in `week{W}.json` exactly |
| `practice_bank` | Object with keys `day_1`, `day_2`, `day_3`, `day_4` |

### Per day

| Field | Notes |
|-------|-------|
| `concept_id` | `{lesson_id}_C{N}` |
| `concept_name` | The concept title for this day (matches `title` in micro_lesson) |
| `questions` | Object with keys `easy`, `medium`, `hard`. Each is an array of exactly 5 questions. |

### Question difficulty levels

| Level | Bloom's Level | Focus |
|-------|--------------|-------|
| `easy` | Remember/Recall | Direct recall of lesson facts. Simple wording. |
| `medium` | Understand/Apply | Slightly indirect, requires applying the concept. |
| `hard` | Analyse/Evaluate | Multi-step reasoning, word order, pattern recognition. |

### Question types

| `type` | `correct_answer` type | Extra fields |
|--------|----------------------|-------------|
| `mcq` | integer (0-indexed) | `options`: 4 strings, `hint`, `explanation` |
| `true_false` | boolean (`true`/`false`) | `explanation` |
| `numeric_fill` | integer | `explanation` |
| `drag_order` | — | `items`: array of strings, `correct_order`: array of 0-indexed ints, `explanation` |

**Rules:**
- Every question needs `explanation` (shown after answering — positive, educational tone)
- MCQ on easy/medium: 4 options. The wrong options should be plausible, not absurd.
- `numeric_fill` answers must be whole numbers only
- `drag_order` should have 3–5 items. `correct_order` lists the correct position of each item by its 0-indexed array position.

### ID pattern

`W{WW}_D{N}_P_{E|M|H}{N}` where:
- `W{WW}` = week number zero-padded
- `D{N}` = day 1–4
- `P` = practice
- `E` / `M` / `H` = easy / medium / hard
- `{N}` = 1–5

---

## 6. grade{N}.json — Vocabulary Word List Reference

Each file is a **flat JSON array** of 30 words. The system seeds this into the database.

| Field | Type | Notes |
|-------|------|-------|
| `rank` | integer | 1–30, defines presentation order (most common/important first) |
| `word` | string | The word in its native script (Telugu: Telugu script, Hindi: Devanagari, English: English) |
| `romanization` | string | For Indic scripts: readable phonetic spelling in Roman letters. Leave `""` for English. |
| `word_type` | string | `noun`, `verb`, `adjective`, `adverb`, `pronoun`, `preposition`, `conjunction`, `number`, `other` |
| `image_keyword` | string | A single English noun the system can use to find an image (e.g. `"sun"`, `"running"`) |

**Grade-wise vocabulary guidance:**

| Grade | English focus | Hindi focus | Telugu focus |
|-------|--------------|-------------|-------------|
| 1 | Sight words + basic nouns | Common household/nature nouns | Common household/nature nouns |
| 2 | Action words + adjectives | Daily action verbs | Daily action verbs |
| 3 | Descriptive words + simple connectors | Descriptive adjectives | Descriptive adjectives |
| 4–5 | Academic vocabulary | Subject-related nouns | Subject-related nouns |
| 6–8 | Tier-2 vocabulary | Abstract nouns, idioms | Abstract nouns |
| 9–12 | Advanced academic / exam vocabulary | Literary vocabulary | Literary vocabulary |

---

## 7. Quick Checklist Before Submitting a Week's Content

**week{W}.json**
- [ ] `lesson_id` is unique and follows naming convention
- [ ] Exactly 4 micro-lessons (Days 1–4)
- [ ] Day 1 has no `revision_prompts`; Days 2–4 have all three IQ variants
- [ ] Each day has exactly 3 vocabulary words (12 unique words total)
- [ ] Each `dialogue_flow` has exactly 4 stages in order: greeting, concept, activity, wrapup
- [ ] Each day has 3 `practice_questions` (all MCQ, 3 options each)
- [ ] `read_along` for each day has exactly 4 sentences in English, Hindi, and Telugu
- [ ] Hindi and Telugu have `transliterations` arrays (not empty)
- [ ] `weekly_assessment` has exactly 10 questions (4 options each, 2 points each)
- [ ] `star_thresholds` sums to correct percentages

**week{W}_practice.json**
- [ ] `lesson_id` matches the lesson file exactly
- [ ] All 4 days present
- [ ] Each day has exactly 5 easy + 5 medium + 5 hard = 15 questions
- [ ] All question IDs are unique
- [ ] Every question has an `explanation`
- [ ] No `correct_answer` refers to an index out of range

**grade{N}.json**
- [ ] Exactly 30 words
- [ ] `rank` 1–30, no duplicates
- [ ] Indic scripts have non-empty `romanization`
- [ ] `word_type` is one of the allowed values

---

## 8. comprehension_questions — Marks-Based Articulation (BS-CMP)

Each micro-lesson day can optionally include a `comprehension_questions` array. These questions require the student to articulate their understanding in **spoken or typed answers**, unlike MCQs which test recall.

**Lesson flow with comprehension questions:**
```
teaching → comprehension check → vocabulary → read_along → practice → complete
```

Questions appear **immediately after the teaching dialogue** completes, before vocabulary. They are optional — lessons without this field behave exactly as before.

### Mark Definitions

| Marks | Type | Description |
|-------|------|-------------|
| 1 | MCQ | In `practice_questions` — NOT here |
| 2 | Articulation | Student states 2 key points (speak or type) |
| 3 | Articulation | Student states 3 key points (speak or type) |
| 5 | Articulation | Extended — student elaborates with 5 key points |

### comprehension_questions field reference

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | ✅ | Pattern: `D{day}_CQ{N}`. Example: `D1_CQ1`, `D1_CQ2`, `D3_CQ1` |
| `marks` | integer | ✅ | Must be 2, 3, or 5 (never 1 — that's MCQ) |
| `type` | string | ✅ | Always `"articulation"` |
| `question` | string | ✅ | Open-ended question for the student |
| `key_points` | array | ✅ | Length MUST equal `marks`. Each is one distinct idea to cover. |
| `model_answer` | string | ✅ | Full ideal answer. Used by LLM as gold standard for calibration. |
| `explanation` | string | ✅ | Marking guide — what a complete answer must include |
| `media` | array | optional | Image/video references shown alongside the question. See media fields below. |

### key_points rules

- Array length **must equal** `marks` (2 key_points for 2 marks, etc.)
- Each key point is **one distinct idea** — not two ideas merged
- Write key points the student might say in their own words — not exact quotes from `model_answer`
- The LLM checks if each point is covered even when stated differently
- **key_points are withheld from the frontend** until after submission (to prevent gaming)

### model_answer rules

- Write the ideal complete answer in 2–5 sentences
- Cover ALL key points clearly
- Use natural language a student/teacher would use
- The LLM uses this as a "gold standard" to calibrate evaluation fairness

### media fields (optional)

| Field | Type | Notes |
|-------|------|-------|
| `type` | string | `"image"` or `"video"` |
| `src` | string | Relative path under `MEDIA_ROOT` (the `media/` directory) |
| `caption` | string | Alt text / caption for accessibility |

Media `src` paths are relative to Django's `MEDIA_ROOT`. The frontend constructs the full URL as `{DJANGO_BASE_URL}/media/{src}`. Files are served by Django in development and by a CDN in production.

Example:
```json
{"type": "image", "src": "science/class6/plant_types.jpg", "caption": "Types of plants"}
{"type": "video", "src": "science/class6/plant_intro.mp4", "caption": "Introduction video"}
```

### Media in teaching_content (optional)

You can also add a `media` array to any IQ-level variant within `teaching_content`:

```json
"teaching_content": {
  "standard": {
    "concept_text": "...",
    "pacing": "normal",
    "repetition_count": 2,
    "tts_rate": 0.9,
    "media": [
      {"type": "image", "src": "subject/classN/concept.jpg", "caption": "..."}
    ]
  }
}
```

Teaching content media is displayed below the concept text during the teaching stage.

### Scoring

After the student answers, the backend:
1. Calls the LLM to check each key point
2. Returns `marks_awarded` = count of covered key points
3. Reveals `key_points_text` (the list of points) so the student sees what they missed
4. When ALL questions for the day are answered, updates `DayProgress.comprehension_score`
   and advances `current_day`

**comprehension_score** = `total_marks_awarded / total_marks_available × 100`

**weighted_star_rating** = `min(5, ceil(comprehension_score / 20))`

### Quick Checklist for comprehension_questions

- [ ] `marks` is 2, 3, or 5 (never 1)
- [ ] `key_points` array length equals `marks`
- [ ] `model_answer` covers all key points
- [ ] `id` follows `D{day}_CQ{N}` pattern
- [ ] `explanation` describes what a full-marks answer must include
- [ ] Media `src` paths are relative to `media/` (not absolute URLs)
