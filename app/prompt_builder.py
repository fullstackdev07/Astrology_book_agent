# app/prompt_builder.py
import json

# NEW PROMPT for parsing user input
def build_data_extraction_prompt(user_prompt: str) -> str:
    """
    Builds a prompt to ask the LLM to extract structured birth data from a text string.
    This includes geocoding the location and determining the correct timezone offset.
    """
    return f"""
From the user's text prompt, extract the birth information and return it as a JSON object.
Your tasks are:
1.  Parse the date into day, month, and year.
2.  Parse the time into hour (0-23 format) and minute.
3.  Identify the city and state/country.
4.  Find the geographic latitude and longitude for that city.
5.  **Crucially**, determine the correct UTC timezone offset number for that specific location *on that specific date* (to account for Daylight Saving Time).

USER PROMPT: "{user_prompt}"

Return ONLY the JSON object with the following keys: "day", "month", "year", "hour", "min", "latitude", "longitude", "timezone_offset".

Example:
User Prompt: "October 31, 1995 at 8:15 AM in Chicago, Illinois"
JSON Response:
{{
  "day": 31,
  "month": 10,
  "year": 1995,
  "hour": 8,
  "min": 15,
  "latitude": 41.8781,
  "longitude": -87.6298,
  "timezone_offset": -6.0
}}
"""


def build_astrology_section_prompt(section_title: str, natal_chart_json: dict, word_target: int) -> str:
    """
    Builds the main prompt for generating a section of the book, with a strict no-jargon rule.
    """
    return f"""
You are an expert, insightful, and compassionate writer, creating a deeply personal book for an individual.
Your task is to interpret a set of symbolic data about a person and translate it into beautiful, flowing, narrative prose.

**CRITICAL INSTRUCTION: You MUST NOT use any astrological or technical terminology.** Do not mention "Sun sign," "Moon," "ascendant," "Virgo," "Capricorn," "houses," "aspects," "trine," "zodiac," "astrology," or any similar jargon. Your task is to **TRANSLATE** the meaning of the data into plain, insightful language about the person's personality, emotions, and life path.

Write in a warm, knowing, second-person voice ("You are...", "You find...", "Your nature is...").

THEME OF THIS SECTION: "{section_title}"

SYMBOLIC DATA (Your sole source of truth for this interpretation):
---
{json.dumps(natal_chart_json, indent=2)}
---

YOUR TASK:
Write a flowing and insightful interpretation for the section titled "{section_title}".
Infer the personality traits from the symbolic data. For example, instead of saying "Your Sun is in Virgo," write "At your core, you possess a meticulous nature and a deep-seated need to be of service and to improve the world around you." Instead of "Your Moon is in Capricorn," write "On an emotional level, you build your security on a foundation of discipline, responsibility, and tangible accomplishment."

Focus on creating a meaningful and inspiring narrative. Aim for a word count of approximately {word_target} words.
Begin writing the content directly. Do not repeat the section title or add any introductory pleasantries.
"""

def build_summarization_prompt(section_text: str) -> str:
    """Builds a prompt to summarize a generated section for image generation."""
    return f"""
Summarize the following block of text in 2-3 sentences. Focus on the core themes, archetypes, and emotional tone. This summary will be used to generate a symbolic piece of artwork.

TEXT TO SUMMARIZE:
---
{section_text}
---
"""

def build_safe_image_prompt_generation_prompt(section_summary: str) -> str:
    """Asks the LLM to generate a safe, symbolic, and artistic prompt for DALL-E."""
    return f"""
Based on the following summary of a personal interpretation, write a single, descriptive paragraph for an AI image generator (like DALL-E 3).

**CRITICAL INSTRUCTIONS:**
- The prompt must be symbolic, artistic, and abstract.
- Focus on archetypal themes, natural elements, and cosmic energy.
- Do NOT depict specific, recognizable human figures. Use archetypal descriptions like "a veiled feminine figure made of starlight," "a powerful craftsman forging a sword from a fallen star," or "a seeker looking out over a vast, otherworldly landscape."
- The mood should be mystical, elegant, and awe-inspiring.
- The style should be "A beautiful and evocative digital painting with rich, deep colors and ethereal light, in a vertical 1024x1792 aspect ratio."

**Interpretation Summary:** "{section_summary}"

**Your Task:**  
Create a single-paragraph DALL-E prompt that captures the symbolic essence of this summary. Make it safe for all audiences and focus on visual metaphor.
"""

def build_book_structure_prompt(natal_chart_json: dict, word_count_tier: str) -> str:
    """
    Builds a prompt for an expert-level AI to analyze a natal chart and propose
    a book structure based on its core psychological dynamics.
    """
    return f"""
You are a master psychological interpreter and book architect. Your task is to analyze the provided symbolic data (a natal chart) and design a thematic structure for a deeply personal book.

**CRITICAL INSTRUCTIONS:**
1.  **Analyze Holistically:** Do not simply list placements. Instead, identify the most significant psychological patterns, energetic tensions, and core narratives. Look for:
    - Concentrated areas of activity (e.g., multiple points in one area suggesting a major life focus).
    - Internal tensions and motivational conflicts (e.g., data points suggesting a clash between security and freedom, or between intellect and emotion).
    - Emotional polarities (e.g., opposing emotional needs).
    - The subject's likely communication strategy (their natural tone, cognitive structure, emotional access points).
2.  **Define Thematic Chapters:** Based on your analysis, create a series of chapter themes. Each chapter should represent a core dynamic of the person's inner world.
3.  **No Jargon:** Your output themes and summaries MUST NOT contain any astrological jargon (planets, signs, houses, aspects, etc.). Translate everything into psychological and experiential language.
4.  **Adhere to Depth:** The number and complexity of your themes should match the requested book depth: '{word_count_tier}'.
    - **Core Dynamics (~15k words):** 3-4 major, foundational themes.
    - **Primary & Secondary Themes (~30k words):** 5-6 themes, including core dynamics and significant internal contradictions or secondary life patterns.
    - **Full Arc (~50k+ words):** 7-8+ themes, covering the full arc from core wounds and shadow aspects to pathways for transformation and potential.
5.  **Output JSON:** Return ONLY a JSON object with a single key "chapters", which is a list of chapter objects. Each chapter object must have these keys:
    - "theme_title": An evocative, insightful title for the chapter (e.g., "The Tug-of-War Between Your Heart and Your Mind," "The Architect of Your Own Security," "The Search for a Truth That Feels Like Home").
    - "summary": A 1-2 sentence summary of the psychological dynamic this chapter will explore.
    - "keywords": A list of 5-7 keywords that capture the essence of this theme (e.g., "responsibility, structure, emotional discipline, achievement, legacy").

**SYMBOLIC DATA TO ANALYZE:**
---
{json.dumps(natal_chart_json, indent=2)}
---

**EXAMPLE JSON OUTPUT STRUCTURE:**
{{
  "chapters": [
    {{
      "theme_title": "The Deep Current of Your Emotional World",
      "summary": "This chapter explores the foundational nature of your emotional security, which is built on privacy, intuitive depth, and a powerful, almost psychic connection to your past and heritage.",
      "keywords": ["intuition", "privacy", "security", "heritage", "empathy", "vulnerability"]
    }},
    {{
      "theme_title": "The Arena of Action: Where Drive Meets Structure",
      "summary": "This chapter examines the inherent tension between your assertive, ambitious drive and a deep-seated need for discipline and long-term planning, a conflict that can be the source of immense achievement.",
      "keywords": ["ambition", "discipline", "conflict", "strategy", "patience", "achievement"]
    }}
  ]
}}
"""


# ==============================================================================
# PROMPT 2: THE WRITER - Writes a single, dynamically-defined chapter
# ==============================================================================
def build_dynamic_chapter_prompt(chapter_details: dict, natal_chart_json: dict, word_target: int) -> str:
    """
    Builds the main prompt for generating a single, thematic chapter of the book.
    """
    return f"""
You are an expert, insightful, and compassionate writer, creating a deeply personal book for an individual.
Your task is to interpret a set of symbolic data about a person and translate it into beautiful, flowing, narrative prose for a specific chapter.

**CRITICAL INSTRUCTION: You MUST NOT use any astrological or technical terminology.** Do not mention "Sun sign," "Moon," "ascendant," "Virgo," "zodiac," "houses," or any similar jargon. Your task is to **TRANSLATE** the meaning of the data into plain, insightful language about the person's personality, emotions, and life path. Write in a warm, knowing, second-person voice ("You are...", "You find...", "Your nature is...").

**CHAPTER FOCUS:**
- **Title:** "{chapter_details['theme_title']}"
- **Core Idea:** "{chapter_details['summary']}"
- **Key Concepts to Weave In:** {', '.join(chapter_details['keywords'])}

Using the full symbolic data provided below as your source of truth, write a flowing, psychologically-grounded, and emotionally resonant chapter that fully explores this specific theme. Your interpretation must be directly supported by the data, but explained through the lens of lived experience.

**SYMBOLIC DATA (Your sole source of truth for this interpretation):**
---
{json.dumps(natal_chart_json, indent=2)}
---

YOUR TASK:
Write the full text for the chapter titled "{chapter_details['theme_title']}".
Aim for a word count of approximately {word_target} words.
Begin writing the content directly. Do not repeat the section title or add any introductory pleasantries.
"""

# (You can keep the summarization and safe image prompts as they are, they are still useful)
def build_summarization_prompt(section_text: str) -> str:
    """Builds a prompt to summarize a generated section for image generation."""
    return f"""
Summarize the following block of text in 2-3 sentences. Focus on the core themes, archetypes, and emotional tone. This summary will be used to generate a symbolic piece of artwork.

TEXT TO SUMMARIZE:
---
{section_text}
---
"""

def build_safe_image_prompt_generation_prompt(section_summary: str) -> str:
    """Asks the LLM to generate a safe, symbolic, and artistic prompt for DALL-E."""
    return f"""
Based on the following summary of a personal interpretation, write a single, descriptive paragraph for an AI image generator (like DALL-E 3).

**CRITICAL INSTRUCTIONS:**
- The prompt must be symbolic, artistic, and abstract.
- Focus on archetypal themes, natural elements, and cosmic energy.
- Do NOT depict specific, recognizable human figures. Use archetypal descriptions like "a veiled feminine figure made of starlight," "a powerful craftsman forging a sword from a fallen star," or "a seeker looking out over a vast, otherworldly landscape."
- The mood should be mystical, elegant, and awe-inspiring.
- The style should be "A beautiful and evocative digital painting with rich, deep colors and ethereal light, in a vertical 1024x1792 aspect ratio."

**Interpretation Summary:** "{section_summary}"

**Your Task:**
Create a single-paragraph DALL-E prompt that captures the symbolic essence of this summary. Make it safe for all audiences and focus on visual metaphor.
"""

# Note: build_data_extraction_prompt remains unchanged.
# Note: build_astrology_section_prompt is now OBSOLETE.