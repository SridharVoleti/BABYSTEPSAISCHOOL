"""
2026-02-27: Static scene catalog for Story Mode Service (BS-GAM-003).

Defines 20 seeded narrative scenes — 4 per subject across 5 subjects
(English, Math, Science, Hindi, Telugu). Each scene is keyed by
concept_slot within its subject, building a culturally relevant
educational narrative for Indian children.
"""

# 2026-02-27: Master scene catalog: 4 scenes × 5 subjects = 20 total
SCENE_CATALOG = [
    # ── English ──────────────────────────────────────────────────────────────
    {
        'scene_id': 'english_q001',
        'subject': 'English',
        'scene_type': 'concept',
        'concept_slot': 1,
        'narrative_text': (
            "Priya steps through the carved wooden doors of Saraswati's Library, "
            "where glowing letters dance like fireflies above ancient bookshelves. "
            "A friendly parrot named Varna swoops down and places the first golden "
            "word-scroll in her hands, beginning her quest for language mastery."
        ),
        'bonus_text': '',
        'illustration_ref': '',
    },
    {
        'scene_id': 'english_q001_bonus',
        'subject': 'English',
        'scene_type': 'bonus',
        'concept_slot': 1,
        'narrative_text': (
            "A radiant golden door appears behind the first bookshelf — visible "
            "only to those who earned five stars. Inside, Varna reveals the "
            "Secret Scroll Room, where the rarest stories in all of India "
            "are preserved in shimmering light."
        ),
        'bonus_text': (
            "You have unlocked the Secret Scroll Room with a perfect five-star score! "
            "Varna grants you the Golden Quill — a mark of excellence awarded only "
            "to the most dedicated language learners."
        ),
        'illustration_ref': '',
    },
    {
        'scene_id': 'english_q002',
        'subject': 'English',
        'scene_type': 'concept',
        'concept_slot': 2,
        'narrative_text': (
            "Priya discovers a hidden reading nook behind a waterfall of silver "
            "sentences, where every book whispers its story aloud when touched. "
            "Varna cheers as she decodes a riddle written in starlight ink, "
            "earning the right to climb to the next level of the library tower."
        ),
        'bonus_text': '',
        'illustration_ref': '',
    },
    {
        'scene_id': 'english_q003',
        'subject': 'English',
        'scene_type': 'bonus',
        'concept_slot': 3,
        'narrative_text': (
            "A secret door appears in the library wall, etched with five gleaming "
            "stars — only students of exceptional skill may enter. Inside, Priya "
            "finds the Chamber of Stories, where tales from across India come alive "
            "as vivid holograms narrated in perfect English."
        ),
        'bonus_text': (
            "You have discovered the Chamber of Stories! Here, the Panchatantra "
            "tales and folk stories from every Indian state unfold before you. "
            "Varna grants you the Storyteller's Feather — a mark of true mastery."
        ),
        'illustration_ref': '',
    },
    {
        'scene_id': 'english_finale_ch01',
        'subject': 'English',
        'scene_type': 'chapter_finale',
        'concept_slot': 10,
        'narrative_text': (
            "The entire library trembles with celebration as Priya places the "
            "final golden scroll on the Altar of Words, completing the first "
            "chapter of her journey through Saraswati's Library. Goddess Saraswati "
            "herself appears, blessing Priya with the Scholar's Veena — a symbol "
            "that she has mastered the foundations of English."
        ),
        'bonus_text': '',
        'illustration_ref': '',
    },

    # ── Math ─────────────────────────────────────────────────────────────────
    {
        'scene_id': 'math_q001',
        'subject': 'Math',
        'scene_type': 'concept',
        'concept_slot': 1,
        'narrative_text': (
            "Arjun arrives at the towering gates of Aryabhatta's Kingdom, where "
            "numbers are carved into every stone and geometric patterns tile every "
            "floor. The great sage Aryabhatta greets him with a warm smile and "
            "hands him a bronze abacus to begin solving the first puzzle of the realm."
        ),
        'bonus_text': '',
        'illustration_ref': '',
    },
    {
        'scene_id': 'math_q001_bonus',
        'subject': 'Math',
        'scene_type': 'bonus',
        'concept_slot': 1,
        'narrative_text': (
            "A hidden chamber glows with golden light beyond the kingdom gates — "
            "only five-star scholars may enter. Aryabhatta reveals the Chamber "
            "of Ancient Calculations, where the world's first mathematical "
            "discoveries are preserved in luminous equations."
        ),
        'bonus_text': (
            "You have entered the Chamber of Ancient Calculations! Aryabhatta "
            "shares the secret behind the discovery of zero and the decimal "
            "system. You receive the Bronze Abacus of Champions — awarded only "
            "to the finest mathematical minds."
        ),
        'illustration_ref': '',
    },
    {
        'scene_id': 'math_q002',
        'subject': 'Math',
        'scene_type': 'concept',
        'concept_slot': 2,
        'narrative_text': (
            "Deep inside the kingdom's crystal cave, Arjun finds a wall covered in "
            "number patterns that pulse with blue light whenever solved correctly. "
            "Each correct answer reveals a new passage forward, leading him closer "
            "to the fabled Hall of Infinite Numbers at the kingdom's heart."
        ),
        'bonus_text': '',
        'illustration_ref': '',
    },
    {
        'scene_id': 'math_q003',
        'subject': 'Math',
        'scene_type': 'bonus',
        'concept_slot': 3,
        'narrative_text': (
            "A secret staircase spirals upward from the cave, accessible only to "
            "those who earned a perfect five-star score. Arjun climbs to the "
            "Observatory of Zero, where Aryabhatta's greatest invention — the "
            "concept of zero — floats as a glowing orb in the centre of the room."
        ),
        'bonus_text': (
            "You have reached the Observatory of Zero! Aryabhatta reveals the "
            "mystery behind his invention of zero and how it changed mathematics "
            "forever. You receive the Zero Stone — the rarest treasure in the kingdom."
        ),
        'illustration_ref': '',
    },
    {
        'scene_id': 'math_finale_ch01',
        'subject': 'Math',
        'scene_type': 'chapter_finale',
        'concept_slot': 10,
        'narrative_text': (
            "The citizens of Aryabhatta's Kingdom line the streets as Arjun "
            "solves the Grand Equation etched on the kingdom's central monument, "
            "completing the first chapter of his mathematical journey. Aryabhatta "
            "crowns him with a laurel of silver pi symbols, proclaiming him a "
            "true Number Warrior of the realm."
        ),
        'bonus_text': '',
        'illustration_ref': '',
    },

    # ── Science ──────────────────────────────────────────────────────────────
    {
        'scene_id': 'science_q001',
        'subject': 'Science',
        'scene_type': 'concept',
        'concept_slot': 1,
        'narrative_text': (
            "Meena enters the lush Vaisheshika Valley, where every plant, rock, "
            "and creature hums with scientific energy waiting to be discovered. "
            "A wise old owl named Kanada perches on an ancient banyan tree and "
            "presents her with a magnifying glass that reveals the hidden atoms "
            "in everything around her."
        ),
        'bonus_text': '',
        'illustration_ref': '',
    },
    {
        'scene_id': 'science_q001_bonus',
        'subject': 'Science',
        'scene_type': 'bonus',
        'concept_slot': 1,
        'narrative_text': (
            "A secret path through glowing ferns appears only for five-star "
            "scientists. Kanada leads Meena to the Ancient Atom Garden, where "
            "each flower represents a different element discovered by Indian "
            "scholars thousands of years ago."
        ),
        'bonus_text': (
            "You have discovered the Ancient Atom Garden! Kanada reveals how "
            "ancient Indian sages first proposed the concept of the atom, "
            "centuries before modern science. You receive the Atom Amulet — "
            "proof that you think like a true scientist."
        ),
        'illustration_ref': '',
    },
    {
        'scene_id': 'science_q002',
        'subject': 'Science',
        'scene_type': 'concept',
        'concept_slot': 2,
        'narrative_text': (
            "Following a trail of glowing footprints, Meena arrives at the Valley's "
            "Laboratory River, where experiments float past on lily pads and "
            "colourful chemical reactions bloom like flowers in the current. "
            "Kanada challenges her to predict which experiment will succeed, "
            "sharpening her scientific thinking with every attempt."
        ),
        'bonus_text': '',
        'illustration_ref': '',
    },
    {
        'scene_id': 'science_q003',
        'subject': 'Science',
        'scene_type': 'bonus',
        'concept_slot': 3,
        'narrative_text': (
            "A hidden grotto opens beneath the great waterfall, its entrance marked "
            "by five radiant stars that shimmer only for top scholars. Inside, "
            "Meena finds the Inventors' Cave, where India's greatest scientists — "
            "C.V. Raman, Homi Bhabha, and APJ Abdul Kalam — appear as friendly "
            "holograms ready to share their secrets."
        ),
        'bonus_text': (
            "You have unlocked the Inventors' Cave! Meet the legends of Indian "
            "science who changed the world with curiosity and determination. "
            "Kanada awards you the Atom Amulet — proof that you think like a "
            "true scientist."
        ),
        'illustration_ref': '',
    },
    {
        'scene_id': 'science_finale_ch01',
        'subject': 'Science',
        'scene_type': 'chapter_finale',
        'concept_slot': 10,
        'narrative_text': (
            "The whole Vaisheshika Valley erupts in bioluminescent light as Meena "
            "completes the Final Experiment that unlocks the valley's deepest "
            "mystery, finishing the first chapter of her scientific adventure. "
            "Kanada soars into the sky trailing a rainbow of discovery, and "
            "Meena is crowned the Valley's first Junior Scientist."
        ),
        'bonus_text': '',
        'illustration_ref': '',
    },

    # ── Hindi ─────────────────────────────────────────────────────────────────
    {
        'scene_id': 'hindi_q001',
        'subject': 'Hindi',
        'scene_type': 'concept',
        'concept_slot': 1,
        'narrative_text': (
            "Ravi passes through a gateway formed from two giant Devanagari letters "
            "and enters Devanagari Dham, a luminous city where every building is "
            "built from stacked aksharas glowing amber and gold. A cheerful "
            "sparrow named Kavita sings the first Hindi vowel song to welcome him "
            "and leads him to the Akshar Mahal — the Palace of Letters."
        ),
        'bonus_text': '',
        'illustration_ref': '',
    },
    {
        'scene_id': 'hindi_q001_bonus',
        'subject': 'Hindi',
        'scene_type': 'bonus',
        'concept_slot': 1,
        'narrative_text': (
            "A gleaming door of carved Devanagari script opens for five-star "
            "scholars only, leading to the Akshara Treasury where the rarest "
            "Hindi manuscripts are stored. Kavita sings a special song of "
            "welcome for Ravi's exceptional achievement."
        ),
        'bonus_text': (
            "You have unlocked the Akshara Treasury! The greatest Hindi poets "
            "and writers appear to share their wisdom with you. Kavita presents "
            "the Golden Akshara — awarded only to the most dedicated Hindi scholars."
        ),
        'illustration_ref': '',
    },
    {
        'scene_id': 'hindi_q002',
        'subject': 'Hindi',
        'scene_type': 'concept',
        'concept_slot': 2,
        'narrative_text': (
            "In the bustling bazaar of Devanagari Dham, word-merchants sell "
            "shimmering vocabulary gems that Ravi must correctly name to add "
            "to his collection. Kavita whispers pronunciation tips as Ravi "
            "haggles with the merchants, growing his Hindi word treasury "
            "with every successful exchange."
        ),
        'bonus_text': '',
        'illustration_ref': '',
    },
    {
        'scene_id': 'hindi_q003',
        'subject': 'Hindi',
        'scene_type': 'bonus',
        'concept_slot': 3,
        'narrative_text': (
            "A golden door appears at the far end of the bazaar, bearing five "
            "star-shaped locks that dissolve only under a perfect score. Beyond "
            "it lies the Kavya Kunj — the Garden of Poetry — where verses from "
            "Kabir, Mirabai, and Tulsidas bloom as fragrant flowers that recite "
            "their poems when gently touched."
        ),
        'bonus_text': (
            "You have entered the Kavya Kunj — the Garden of Poetry! The great "
            "Hindi poets share their wisdom with you through beautiful verses. "
            "Kavita gifts you the Poet's Inkpot, a rare treasure earned only by "
            "the most dedicated Hindi learners."
        ),
        'illustration_ref': '',
    },
    {
        'scene_id': 'hindi_finale_ch01',
        'subject': 'Hindi',
        'scene_type': 'chapter_finale',
        'concept_slot': 10,
        'narrative_text': (
            "All the citizens of Devanagari Dham gather in the central courtyard "
            "as Ravi recites the chapter's Grand Shloka from memory, completing "
            "the first chapter of his Hindi journey with perfect diction. Kavita "
            "places a garland of golden aksharas around his neck, and the city "
            "resonates with the joyful sounds of dhol and shehnai."
        ),
        'bonus_text': '',
        'illustration_ref': '',
    },

    # ── Telugu ────────────────────────────────────────────────────────────────
    {
        'scene_id': 'telugu_q001',
        'subject': 'Telugu',
        'scene_type': 'concept',
        'concept_slot': 1,
        'narrative_text': (
            "Lakshmi steps into the emerald expanse of Andhra Vanam, a magical "
            "forest where every leaf is engraved with Telugu letters that rustle "
            "melodiously in the breeze. A gentle deer named Akshara guides her "
            "to the first Gunintamala Tree, whose branches form the vowels and "
            "consonants of the Telugu script."
        ),
        'bonus_text': '',
        'illustration_ref': '',
    },
    {
        'scene_id': 'telugu_q001_bonus',
        'subject': 'Telugu',
        'scene_type': 'bonus',
        'concept_slot': 1,
        'narrative_text': (
            "A hidden grove surrounded by jasmine and golden lotus opens only "
            "for five-star learners — the Nannaya Nivasam, named after Telugu's "
            "first great poet. Akshara bows gently, welcoming Lakshmi to this "
            "secret sanctuary of Telugu literature."
        ),
        'bonus_text': (
            "You have entered the Nannaya Nivasam! The first poets of Telugu "
            "literature share their stories and verses with you here. Akshara "
            "presents the Pearl of Andhra — the rarest honour in Andhra Vanam."
        ),
        'illustration_ref': '',
    },
    {
        'scene_id': 'telugu_q002',
        'subject': 'Telugu',
        'scene_type': 'concept',
        'concept_slot': 2,
        'narrative_text': (
            "Following a stream of silver water that babbles in Telugu rhymes, "
            "Lakshmi reaches the Padyala Pond — the Lake of Verses — where "
            "Telugu poetry is woven into the ripples on the water's surface. "
            "Akshara leaps gracefully across stepping stones shaped like "
            "ottulu, encouraging Lakshmi to read each one aloud and correctly."
        ),
        'bonus_text': '',
        'illustration_ref': '',
    },
    {
        'scene_id': 'telugu_q003',
        'subject': 'Telugu',
        'scene_type': 'bonus',
        'concept_slot': 3,
        'narrative_text': (
            "Hidden behind a cascade of jasmine flowers, a secret clearing "
            "reveals itself only to five-star scholars, glowing with soft "
            "lamplight under an ancient neem tree. Inside, Lakshmi discovers "
            "the Sahitya Sangam — Confluence of Literature — where the works "
            "of Nannaya, Tikkana, and Errana come alive in vivid storytelling."
        ),
        'bonus_text': (
            "You have reached the Sahitya Sangam — the Confluence of Telugu "
            "Literature! The Maha Kavi poets share the stories behind their "
            "greatest works with you. Akshara presents you the Kavitha Kalasam "
            "— the golden pot of poetry — awarded only to the finest Telugu scholars."
        ),
        'illustration_ref': '',
    },
    {
        'scene_id': 'telugu_finale_ch01',
        'subject': 'Telugu',
        'scene_type': 'chapter_finale',
        'concept_slot': 10,
        'narrative_text': (
            "The entire Andhra Vanam comes alive with the songs of birds and "
            "the fragrance of kadamba blossoms as Lakshmi recites the final "
            "Champu verse, completing the first chapter of her Telugu adventure. "
            "Akshara bows gracefully before her, and the forest itself crowns "
            "her with a wreath of golden lotus flowers — Andhra Vanam's highest honour."
        ),
        'bonus_text': '',
        'illustration_ref': '',
    },
]
