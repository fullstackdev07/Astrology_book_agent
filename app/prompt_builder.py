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