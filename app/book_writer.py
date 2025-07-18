# app/book_writer.py
from openai import AsyncOpenAI
import os
import asyncio
import json
import random
import string
import httpx
from app.prompt_builder import (
    build_astrology_section_prompt,
    build_summarization_prompt,
    build_safe_image_prompt_generation_prompt
)
from dotenv import load_dotenv

load_dotenv()

openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_TEXT = "gpt-4-1106-preview"
MODEL_IMAGE = "dall-e-3"
WORDS_PER_SECTION_TARGET = 750 # The size of each chunk sent to the LLM

async def generate_chapter_image(chapter_summary: str) -> str:
    """Generates a chapter image using a safer, two-step process."""
    print(f"  - Generating image based on summary: '{chapter_summary[:80]}...'")
    safe_prompt_request = build_safe_image_prompt_generation_prompt(chapter_summary)
    try:
        sanitized_prompt_response = await openai.chat.completions.create(
            model=MODEL_TEXT, messages=[{"role": "user", "content": safe_prompt_request}], 
            temperature=0.7, max_tokens=300
        )
        image_prompt = sanitized_prompt_response.choices[0].message.content.strip().strip('"')
        print(f"    - Sanitized DALL-E Prompt: {image_prompt}")

        response = await openai.images.generate(
            model=MODEL_IMAGE, prompt=image_prompt, size="1024x1792", quality="standard", n=1
        )
        image_url = response.data[0].url

        output_dir = "generated_images"
        os.makedirs(output_dir, exist_ok=True)
        image_filename = f"{''.join(random.choices(string.ascii_letters + string.digits, k=12))}.png"
        output_path = os.path.join(output_dir, image_filename)
        
        async with httpx.AsyncClient() as client:
            image_response = await client.get(image_url)
            image_response.raise_for_status()
            with open(output_path, "wb") as f: f.write(image_response.content)
                
        print(f"  - Chapter image saved to: {output_path}")
        return output_path
    except Exception as e:
        print(f"  - Could not generate chapter image: {e}")
        return None

async def summarize_section(text: str) -> str:
    """Summarizes text for image generation."""
    summary_prompt = build_summarization_prompt(text)
    try:
        response = await openai.chat.completions.create(
            model=MODEL_TEXT, messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.2, max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return text[:300] + "..."

async def generate_content_block(title: str, context: dict, word_target: int) -> str:
    """Generates a full section of content, breaking it into smaller parts if necessary."""
    print(f"--- Generating content for: '{title}' (Target: {word_target} words) ---")
    if word_target <= 0: return ""

    prompt = build_astrology_section_prompt(title, context, word_target)
    
    # For simplicity and quality, generate in one shot if possible, otherwise break it down.
    # The new prompt is complex, so a single large call might be better.
    if word_target <= 1500:
        print(f"  - Generating single section of {word_target} words...")
        response = await openai.chat.completions.create(
            model=MODEL_TEXT, messages=[{"role": "user", "content": prompt}], temperature=0.75
        )
        return response.choices[0].message.content.strip()

    num_sections = round(word_target / WORDS_PER_SECTION_TARGET)
    parts = []
    print(f"  - Content will be generated in {num_sections} parts.")
    for i in range(num_sections):
        print(f"  - Generating part {i+1}/{num_sections}...")
        part_prompt = build_astrology_section_prompt(f"{title} (focus on one key aspect)", context, WORDS_PER_SECTION_TARGET)
        response = await openai.chat.completions.create(
            model=MODEL_TEXT, messages=[{"role": "user", "content": part_prompt}], temperature=0.75
        )
        section_text = response.choices[0].message.content.strip()
        parts.append(section_text)
        await asyncio.sleep(2)
            
    print(f"--- Finished content for: '{title}' ---")
    return "\n\n".join(parts)

async def generate_astrology_book(natal_chart_json: dict, num_pages: int):
    """Generates all content for the book based on a jargon-free, life-theme structure."""
    
    # NEW BOOK STRUCTURE: Focused on life themes, not astrology.
    BOOK_STRUCTURE = [
        {"title": "Your Core Essence: The Person You Are at Heart"},
        {"title": "Your Inner World: Emotions, Security, and Instincts"},
        {"title": "How You Meet the World: Your Outward Persona and First Impressions"},
        {"title": "Thought and Connection: The Way You Think and Relate to Others"},
        {"title": "Drive and Ambition: Your Path to Achievement"},
        {"title": "Life's Deeper Currents: Areas of Growth, Challenge, and Transformation"},
    ]

    words_per_page = 250
    # Approx fixed pages: Debug(2), Blanks(8), Title(1), Date(1), TOC(1), Preface(1) = ~14
    # Overhead per section: Title page(1), Image page(1) = 2
    content_pages = num_pages - 14 - (len(BOOK_STRUCTURE) * 2)
    intro_outro_pages = 4
    content_pages -= intro_outro_pages
    words_per_section = int(max(500, (content_pages * words_per_page) / len(BOOK_STRUCTURE)))

    print(f"\nBook Target: {num_pages} pages.")
    print(f"Targeting {words_per_section} words for each of the {len(BOOK_STRUCTURE)} main sections.")
    
    # Generate Intro and Outro text first
    print("\n--- Generating Introduction and Conclusion ---")
    intro_text_task = generate_content_block("An Introduction: The Map of You", natal_chart_json, 400)
    outro_text_task = generate_content_block("A Concluding Reflection", natal_chart_json, 300)
    intro_text, outro_text = await asyncio.gather(intro_text_task, outro_text_task)
    
    chapters_data = []
    print("\n--- Starting Main Section and Image Generation ---")
    for i, section in enumerate(BOOK_STRUCTURE):
        section_title = section["title"]
        print(f"\n[Generating Content for Section {i+1}: {section_title}]")
        
        section_text = await generate_content_block(section_title, natal_chart_json, words_per_section)
        image_summary = await summarize_section(section_text)
        image_path = await generate_chapter_image(image_summary)
        
        chapters_data.append({"heading": section_title, "content": section_text, "image_path": image_path})
        await asyncio.sleep(5)

    preface_text = """What you hold in your hands is a mirror. It is not a mirror of your face or your form, but of the intricate, invisible architecture of your inner self. It is a portrait painted with the light of a specific moment in time—your moment. Contained within these pages is an interpretation of the unique patterns, potentials, and pathways that make you who you are. This is not a set of rigid predictions, but a guide to self-understanding. May it illuminate the beautiful complexity of the journey you were born to walk."""

    return {
        "swapi_call_text": "Symbolic data based on birth details.",
        "swapi_json_output": json.dumps(natal_chart_json, indent=4),
        "preface_text": preface_text,
        "prologue_text": intro_text,
        "epilogue_text": outro_text,
        "chapters": chapters_data,
    }