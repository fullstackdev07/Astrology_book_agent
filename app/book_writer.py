# app/book_writer.py

from openai import AsyncOpenAI
import os
import asyncio
import json
import random
import string
import httpx
from app.prompt_builder import (
    build_book_structure_prompt, # <-- NEW
    build_dynamic_chapter_prompt, # <-- NEW
    build_summarization_prompt,
    build_safe_image_prompt_generation_prompt
)
from dotenv import load_dotenv

load_dotenv()

openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_TEXT = "gpt-4-1106-preview"
MODEL_IMAGE = "dall-e-3"
# We no longer use WORDS_PER_SECTION_TARGET as the chapter sizes are now dynamic

# generate_chapter_image and summarize_section remain unchanged.
# ... (paste your existing generate_chapter_image and summarize_section functions here) ...

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


async def generate_content_block(prompt: str) -> str: # Simplified to just take a prompt
    """Generates a block of text from a given prompt."""
    print(f"  - Generating content block...")
    # This function is now simpler. The complex logic is in the prompt itself.
    # For very large word counts per chapter, you might re-introduce the sectioning logic here.
    response = await openai.chat.completions.create(
        model=MODEL_TEXT, messages=[{"role": "user", "content": prompt}], temperature=0.75
    )
    return response.choices[0].message.content.strip()


async def generate_astrology_book(natal_chart_json: dict, target_word_count: int):
    """
    Generates a thematically structured book by first analyzing the chart for core
    dynamics, then writing chapters based on that analysis.
    """
    print("\n--- STAGE 1: ARCHITECTING THE BOOK STRUCTURE ---")
    
    # Determine the word count tier for the Architect prompt
    if target_word_count <= 20000:
        word_count_tier = "Core Dynamics (~15k words)"
    elif target_word_count <= 40000:
        word_count_tier = "Primary & Secondary Themes (~30k words)"
    else:
        word_count_tier = "Full Arc (~50k+ words)"
        
    print(f"Targeting {word_count_tier} for a ~{target_word_count} word book.")

    # 1. Call the Architect AI to get the book's structure
    structure_prompt = build_book_structure_prompt(natal_chart_json, word_count_tier)
    structure_response = await openai.chat.completions.create(
        model=MODEL_TEXT,
        messages=[{"role": "user", "content": structure_prompt}],
        response_format={"type": "json_object"},
        temperature=0.2
    )
    book_structure = json.loads(structure_response.choices[0].message.content)
    dynamic_chapters = book_structure.get("chapters", [])

    if not dynamic_chapters:
        raise ValueError("The AI Architect failed to generate a book structure.")
        
    print(f"--- Book structure defined with {len(dynamic_chapters)} thematic chapters. ---")
    for i, chap in enumerate(dynamic_chapters):
        print(f"  Chapter {i+1}: {chap['theme_title']}")

    # 2. Allocate word counts and generate content for each dynamic chapter
    # Simple allocation for now. Can be made more sophisticated later.
    words_per_chapter = int(target_word_count / len(dynamic_chapters))
    
    chapters_data = []
    print("\n--- STAGE 2: WRITING THE CHAPTERS ---")
    for i, chapter_details in enumerate(dynamic_chapters):
        section_title = chapter_details["theme_title"]
        print(f"\n[Generating Content for Chapter {i+1}: {section_title}]")
        
        # Build the specific prompt for this chapter
        chapter_prompt = build_dynamic_chapter_prompt(chapter_details, natal_chart_json, words_per_chapter)
        
        # Generate the chapter text
        section_text = await generate_content_block(chapter_prompt)
        
        # Generate the summary and image for the chapter
        image_summary = await summarize_section(section_text)
        image_path = await generate_chapter_image(image_summary)
        
        chapters_data.append({"heading": section_title, "content": section_text, "image_path": image_path})
        await asyncio.sleep(5) # Rate limiting

    # 3. Generate static Preface/Intro/Outro (optional, but good for framing)
    # You can keep these or remove them for a purely analytical book.
    preface_text = """What you hold in your hands is not a book of predictions, but a mirror. It reflects the intricate, invisible architecture of your inner world, drawn from a single, powerful moment in time: your beginning. The following chapters are not a breakdown of cosmic mechanics, but an exploration of the core themes, tensions, and potentials that make you who you are. This is a journey into the 'why' behind your drives, the 'how' of your connections, and the 'what' of your unique purpose. May it serve as a guide to deeper self-understanding and a celebration of the complex, beautiful story that is you."""
    intro_text = "Before we delve into the specific themes of your personal narrative, let us first set the stage. This introduction serves as an overture, touching upon the overarching energetic signature of your being—the fundamental rhythm to which your life tends to move. It is the backdrop against which all the individual stories, conflicts, and triumphs detailed in the coming chapters will unfold."
    outro_text = "The journey through these pages has been a journey inward. We have explored the foundational pillars of your being, navigated the currents of your internal conflicts, and illuminated the pathways of your greatest potential. This book is a snapshot, a single interpretation of a vast and dynamic inner landscape. The map is not the territory. The ultimate author of your story is, and always will be, you. May you walk forward with a renewed sense of clarity, self-compassion, and purpose."

    return {
        "swapi_call_text": "Symbolic data based on birth details.",
        "swapi_json_output": json.dumps(natal_chart_json, indent=4),
        "preface_text": preface_text,
        "prologue_text": intro_text, # Using "prologue" for the introduction
        "epilogue_text": outro_text, # Using "epilogue" for the conclusion
        "chapters": chapters_data,
    }