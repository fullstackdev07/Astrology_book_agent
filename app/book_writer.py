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
WORDS_PER_SECTION_TARGET = 750

async def generate_chapter_image(chapter_summary: str) -> str:
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
    print(f"--- Generating content for: '{title}' (Target: {word_target} words) ---")
    if word_target <= 100:
        print("  - Word target too low, skipping generation.")
        return ""
    prompt = build_astrology_section_prompt(title, context, word_target)
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
    # --- FIX #2: DYNAMIC BOOK STRUCTURE ---
    # Define the full set of possible sections
    FULL_BOOK_STRUCTURE = [
        {"title": "Your Core Essence: The Person You Are at Heart"},
        {"title": "Your Inner World: Emotions, Security, and Instincts"},
        {"title": "How You Meet the World: Your Outward Persona and First Impressions"},
        {"title": "Thought and Connection: The Way You Think and Relate to Others"},
        {"title": "Drive and Ambition: Your Path to Achievement"},
        {"title": "Life's Deeper Currents: Areas of Growth, Challenge, and Transformation"},
    ]
    
    # Choose the number of sections based on the requested page count
    if num_pages <= 75:  # For 50-page books
        sections_to_generate = [FULL_BOOK_STRUCTURE[0], FULL_BOOK_STRUCTURE[2]] # Core Essence & Persona
    elif num_pages <= 125: # For 100-page books
        sections_to_generate = [FULL_BOOK_STRUCTURE[0], FULL_BOOK_STRUCTURE[1], FULL_BOOK_STRUCTURE[3], FULL_BOOK_STRUCTURE[4]]
    else: # For 150+ page books
        sections_to_generate = FULL_BOOK_STRUCTURE

    print(f"\n--- Building a {num_pages}-page book with {len(sections_to_generate)} main sections. ---")

    # --- More Accurate Page Count Calculation ---
    words_per_page = 250
    num_main_sections = len(sections_to_generate)

    # Count all non-text pages based on the template structure
    fixed_front_matter_pages = 10 # Debug(2), Blank(4), Title(1), Date(1), Blank(2)
    toc_pages = 1
    preface_overhead = 2 # Title page + blank page
    intro_overhead = 2 # Title page + image page
    conclusion_overhead = 2 # Blank page + title page
    per_section_overhead = 3 # Title page + image page + blank page

    total_overhead_pages = (
        fixed_front_matter_pages +
        toc_pages +
        preface_overhead +
        intro_overhead +
        conclusion_overhead +
        (num_main_sections * per_section_overhead)
    )
    
    available_content_pages = num_pages - total_overhead_pages
    
    if available_content_pages < (num_main_sections + 4):
        raise ValueError(f"Target of {num_pages} pages is too small for this book structure. Minimum required for {num_main_sections} sections is ~{total_overhead_pages + num_main_sections + 4} pages.")

    intro_text_pages = 2
    outro_text_pages = 1
    preface_text_pages = 1

    main_content_text_pages = available_content_pages - intro_text_pages - outro_text_pages - preface_text_pages
    
    words_per_section = int((main_content_text_pages * words_per_page) / num_main_sections) if num_main_sections > 0 else 0
    intro_words = intro_text_pages * words_per_page
    outro_words = outro_text_pages * words_per_page
    
    print(f"Target: {num_pages} pages. Calculated Overhead: {total_overhead_pages} pages.")
    print(f"Available for text: {available_content_pages} pages.")
    print(f"Words per main section: {words_per_section}, Intro words: {intro_words}, Outro words: {outro_words}")

    preface_text = """What you hold in your hands is a mirror. It is not a mirror of your face or your form, but of the intricate, invisible architecture of your inner self. It is a portrait painted with the light of a specific moment in time—your moment. Contained within these pages is an interpretation of the unique patterns, potentials, and pathways that make you who you are. This is not a set of rigid predictions, but a guide to self-understanding. May it illuminate the beautiful complexity of the journey you were born to walk."""

    print("\n--- Generating Introduction and Conclusion ---")
    intro_text_task = generate_content_block("An Introduction: The Map of You", natal_chart_json, intro_words)
    outro_text_task = generate_content_block("A Concluding Reflection", natal_chart_json, outro_words)
    intro_text, outro_text = await asyncio.gather(intro_text_task, outro_text_task)
    
    chapters_data = []
    print("\n--- Starting Main Section and Image Generation ---")
    for i, section in enumerate(sections_to_generate):
        section_title = section["title"]
        print(f"\n[Generating Content for Section {i+1}: {section_title}]")
        section_text = await generate_content_block(section_title, natal_chart_json, words_per_section)
        image_summary = await summarize_section(section_text)
        image_path = await generate_chapter_image(image_summary)
        chapters_data.append({"heading": section_title, "content": section_text, "image_path": image_path})
        await asyncio.sleep(5)

    return {
        "swapi_call_text": "Symbolic data based on birth details.",
        "swapi_json_output": json.dumps(natal_chart_json, indent=4),
        "preface_text": preface_text,
        "prologue_text": intro_text,
        "epilogue_text": outro_text,
        "chapters": chapters_data,
    }