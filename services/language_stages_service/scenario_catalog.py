"""
2026-03-02: Static scenario catalog for Language Stages Service (BS-LNG-005).

Defines 20 universal conversation scenarios. Scenarios are language-agnostic;
the {target_language} placeholder in opening_prompt_template is substituted
at runtime with the student's chosen language name.

All scenarios have difficulty='beginner' for scenarios 1-7,
'intermediate' for 8-14, 'advanced' for 15-20.
"""

# 2026-03-02: 20 universal conversational scenarios
SCENARIO_CATALOG = [
    {
        'scenario_number': 1,
        'title': 'Introducing Yourself',
        'ai_persona': 'friendly neighbour',
        'difficulty': 'beginner',
        'min_turns': 4,
        'max_turns': 8,
        'unlock_after_scenario': None,
        'context_description': (
            "You have just moved into a new neighbourhood. Your friendly neighbour "
            "comes to greet you and wants to learn your name, age, and where you "
            "are from. The conversation is warm and encouraging."
        ),
        'opening_prompt_template': (
            "Hello! I am your new neighbour. Welcome! "
            "Please tell me your name in {target_language}."
        ),
    },
    {
        'scenario_number': 2,
        'title': 'At the Market',
        'ai_persona': 'market shopkeeper',
        'difficulty': 'beginner',
        'min_turns': 4,
        'max_turns': 10,
        'unlock_after_scenario': 1,
        'context_description': (
            "The student is visiting a busy local market. The shopkeeper is selling "
            "fruits and vegetables. The student needs to ask for items, ask the price, "
            "and complete a simple purchase using the target language."
        ),
        'opening_prompt_template': (
            "Welcome to my shop! What would you like to buy today? "
            "Please ask me in {target_language}."
        ),
    },
    {
        'scenario_number': 3,
        'title': 'Asking for Directions',
        'ai_persona': 'helpful passerby',
        'difficulty': 'beginner',
        'min_turns': 4,
        'max_turns': 8,
        'unlock_after_scenario': 2,
        'context_description': (
            "The student is lost in a new town and needs to find the bus station or "
            "a school. A helpful passerby is willing to give directions. The student "
            "must ask politely and understand the directions given."
        ),
        'opening_prompt_template': (
            "Hello, you look a bit lost! Can I help you? "
            "Please ask me for directions in {target_language}."
        ),
    },
    {
        'scenario_number': 4,
        'title': 'Talking About Family',
        'ai_persona': 'curious classmate',
        'difficulty': 'beginner',
        'min_turns': 4,
        'max_turns': 10,
        'unlock_after_scenario': 3,
        'context_description': (
            "A new classmate is curious about the student's family. They ask about "
            "parents, siblings, and family activities. The student describes their "
            "family members and what they do."
        ),
        'opening_prompt_template': (
            "Hi! I would love to know about your family. "
            "Can you tell me about them in {target_language}?"
        ),
    },
    {
        'scenario_number': 5,
        'title': 'Describing Your Day',
        'ai_persona': 'friendly teacher',
        'difficulty': 'beginner',
        'min_turns': 4,
        'max_turns': 10,
        'unlock_after_scenario': 4,
        'context_description': (
            "The teacher asks the student to describe how their day has been. "
            "The student talks about what they did in the morning, afternoon, and "
            "evening using simple past tense expressions."
        ),
        'opening_prompt_template': (
            "Good morning! How was your day yesterday? "
            "Please tell me in {target_language}."
        ),
    },
    {
        'scenario_number': 6,
        'title': 'Favourite Food',
        'ai_persona': 'school cook',
        'difficulty': 'beginner',
        'min_turns': 4,
        'max_turns': 8,
        'unlock_after_scenario': 5,
        'context_description': (
            "The school cook is planning the menu and wants to know what the students "
            "like to eat. The student tells the cook about their favourite foods, "
            "snacks, and drinks."
        ),
        'opening_prompt_template': (
            "Hello! I am planning this week's menu. "
            "What is your favourite food? Tell me in {target_language}."
        ),
    },
    {
        'scenario_number': 7,
        'title': 'Weather Talk',
        'ai_persona': 'radio presenter',
        'difficulty': 'beginner',
        'min_turns': 4,
        'max_turns': 8,
        'unlock_after_scenario': 6,
        'context_description': (
            "A local radio presenter is doing a short segment on today's weather "
            "and asks listeners to call in and describe the weather outside their "
            "window. The student describes the weather and how it makes them feel."
        ),
        'opening_prompt_template': (
            "Welcome to our weather segment! What is the weather like outside "
            "your home right now? Describe it in {target_language}."
        ),
    },
    {
        'scenario_number': 8,
        'title': 'At a Restaurant',
        'ai_persona': 'restaurant waiter',
        'difficulty': 'intermediate',
        'min_turns': 5,
        'max_turns': 10,
        'unlock_after_scenario': 7,
        'context_description': (
            "The student is at a restaurant with family. The waiter greets them, "
            "takes the order, and brings the bill. The student must order food "
            "politely, ask about dishes, and say thank you."
        ),
        'opening_prompt_template': (
            "Good evening! Welcome to our restaurant. "
            "Please see the menu and order your meal in {target_language}."
        ),
    },
    {
        'scenario_number': 9,
        'title': 'At School',
        'ai_persona': 'new student',
        'difficulty': 'intermediate',
        'min_turns': 5,
        'max_turns': 10,
        'unlock_after_scenario': 8,
        'context_description': (
            "A new student has joined the class and needs help understanding the "
            "school timetable, rules, and finding the classroom. The student helps "
            "the newcomer navigate school life."
        ),
        'opening_prompt_template': (
            "Hello, I am new here! Can you help me understand how school works? "
            "Please explain in {target_language}."
        ),
    },
    {
        'scenario_number': 10,
        'title': 'Making Plans',
        'ai_persona': 'best friend',
        'difficulty': 'intermediate',
        'min_turns': 5,
        'max_turns': 10,
        'unlock_after_scenario': 9,
        'context_description': (
            "The student and their best friend are making plans for the weekend. "
            "They discuss where to go, what time to meet, and what to bring. "
            "They use future tense expressions and negotiation language."
        ),
        'opening_prompt_template': (
            "Hey! What shall we do this weekend? "
            "Let us plan something fun — tell me your idea in {target_language}!"
        ),
    },
    {
        'scenario_number': 11,
        'title': 'Hobbies and Interests',
        'ai_persona': 'hobby club coordinator',
        'difficulty': 'intermediate',
        'min_turns': 5,
        'max_turns': 10,
        'unlock_after_scenario': 10,
        'context_description': (
            "The school hobby club coordinator wants to know about the student's "
            "interests so they can be placed in the right group. The student "
            "talks about hobbies, why they enjoy them, and how often they do them."
        ),
        'opening_prompt_template': (
            "Welcome to the Hobby Club! What do you enjoy doing in your free time? "
            "Tell me all about it in {target_language}."
        ),
    },
    {
        'scenario_number': 12,
        'title': 'Birthday Party',
        'ai_persona': 'party host',
        'difficulty': 'intermediate',
        'min_turns': 5,
        'max_turns': 10,
        'unlock_after_scenario': 11,
        'context_description': (
            "The student is attending a classmate's birthday party. The host greets "
            "guests, introduces activities, and asks guests to describe their "
            "favourite birthday memory."
        ),
        'opening_prompt_template': (
            "Welcome to my birthday party! I am so glad you came! "
            "Tell me your favourite birthday memory in {target_language}."
        ),
    },
    {
        'scenario_number': 13,
        'title': 'At the Bus Station',
        'ai_persona': 'ticket counter clerk',
        'difficulty': 'intermediate',
        'min_turns': 5,
        'max_turns': 10,
        'unlock_after_scenario': 12,
        'context_description': (
            "The student is at the bus station and needs to buy a ticket to visit "
            "a relative in another town. The clerk asks for the destination, "
            "preferred time, and number of tickets."
        ),
        'opening_prompt_template': (
            "Good morning! Where would you like to travel today? "
            "Please tell me your destination in {target_language}."
        ),
    },
    {
        'scenario_number': 14,
        'title': 'About Studies',
        'ai_persona': 'school principal',
        'difficulty': 'intermediate',
        'min_turns': 5,
        'max_turns': 10,
        'unlock_after_scenario': 13,
        'context_description': (
            "The principal calls the student to discuss their academic progress. "
            "The student explains their favourite subject, challenges they face, "
            "and goals for the rest of the year."
        ),
        'opening_prompt_template': (
            "Hello! Please sit down. I would love to hear about your studies. "
            "What is your favourite subject and why? Tell me in {target_language}."
        ),
    },
    {
        'scenario_number': 15,
        'title': 'Shopping for Clothes',
        'ai_persona': 'clothing store assistant',
        'difficulty': 'advanced',
        'min_turns': 6,
        'max_turns': 10,
        'unlock_after_scenario': 14,
        'context_description': (
            "The student is shopping for new clothes for a festival. The shop "
            "assistant helps find the right size and colour, discusses the price, "
            "and offers alternatives. The student must negotiate and make a decision."
        ),
        'opening_prompt_template': (
            "Welcome to our store! We have a wonderful collection for the festival season. "
            "What kind of clothes are you looking for? Tell me in {target_language}."
        ),
    },
    {
        'scenario_number': 16,
        'title': 'At the Doctor',
        'ai_persona': 'friendly doctor',
        'difficulty': 'advanced',
        'min_turns': 6,
        'max_turns': 10,
        'unlock_after_scenario': 15,
        'context_description': (
            "The student is visiting the doctor because they have not been feeling well. "
            "The doctor asks about symptoms, how long they have lasted, and advises "
            "on treatment. The student must describe their health clearly."
        ),
        'opening_prompt_template': (
            "Hello! Please tell me how you are feeling. "
            "Describe your symptoms in {target_language} so I can help you."
        ),
    },
    {
        'scenario_number': 17,
        'title': 'About the City',
        'ai_persona': 'tourist guide',
        'difficulty': 'advanced',
        'min_turns': 6,
        'max_turns': 10,
        'unlock_after_scenario': 16,
        'context_description': (
            "A tourist has arrived in the student's city and asks for a guided tour. "
            "The student acts as a proud local, describing famous landmarks, food, "
            "culture, and history of their city."
        ),
        'opening_prompt_template': (
            "Hello! I have just arrived in your city. I heard it is wonderful! "
            "Can you tell me about it in {target_language}?"
        ),
    },
    {
        'scenario_number': 18,
        'title': 'In Nature',
        'ai_persona': 'nature documentary narrator',
        'difficulty': 'advanced',
        'min_turns': 6,
        'max_turns': 10,
        'unlock_after_scenario': 17,
        'context_description': (
            "A documentary filmmaker is visiting a nature park and asks the student "
            "to describe the plants, animals, and environment they can observe. "
            "The student uses descriptive language about nature."
        ),
        'opening_prompt_template': (
            "We are filming a nature documentary! Look around you — "
            "describe what you see in {target_language} for our viewers."
        ),
    },
    {
        'scenario_number': 19,
        'title': 'Festival Discussion',
        'ai_persona': 'cultural journalist',
        'difficulty': 'advanced',
        'min_turns': 6,
        'max_turns': 10,
        'unlock_after_scenario': 18,
        'context_description': (
            "A cultural journalist is writing an article about how different families "
            "celebrate festivals in India. The student describes how their family "
            "celebrates their favourite festival — food, clothes, rituals, and feelings."
        ),
        'opening_prompt_template': (
            "Hello! I am writing about festival celebrations across India. "
            "Which festival is most special to you? Tell me in {target_language}."
        ),
    },
    {
        'scenario_number': 20,
        'title': 'Helping a Neighbour',
        'ai_persona': 'elderly neighbour',
        'difficulty': 'advanced',
        'min_turns': 6,
        'max_turns': 10,
        'unlock_after_scenario': 19,
        'context_description': (
            "An elderly neighbour needs help with some tasks — carrying groceries, "
            "explaining how to use a phone, or writing a letter. The student "
            "offers help, listens to needs, and explains things clearly and patiently."
        ),
        'opening_prompt_template': (
            "Oh, hello! I am so glad to see you. I need a little help today. "
            "Can I explain my problem in {target_language}? Will you help me?"
        ),
    },
]
