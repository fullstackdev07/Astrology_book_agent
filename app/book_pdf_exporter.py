# app/book_pdf_exporter.py
from weasyprint import HTML, CSS
from jinja2 import Template
import os
from datetime import datetime
import pathlib

def save_book_as_pdf(title: str, book_data: dict, filename: str) -> str:
    """
    Generates the final, professionally formatted PDF with all structure requirements met.
    """
    output_dir = "generated_books"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    all_sections_for_toc = []
    has_prologue = bool(book_data.get('prologue_text'))
    has_epilogue = bool(book_data.get('epilogue_text'))
    
    if book_data.get('preface_text'):
        all_sections_for_toc.append({"title": "Preface", "href": "#preface"})
    if has_prologue:
        all_sections_for_toc.append({"title": "Introduction", "href": "#prologue"})
    for i, ch in enumerate(book_data.get("chapters", [])):
        all_sections_for_toc.append({"title": ch["heading"], "href": f"#chapter-{i+1}"})
    if has_epilogue:
        all_sections_for_toc.append({"title": "Conclusion", "href": "#epilogue"})

    template_context = {
        "book_title": title,
        "print_date": datetime.now().strftime("%B %d, %Y"),
        "toc_entries": all_sections_for_toc,
        "has_prologue": has_prologue,
        "has_epilogue": has_epilogue,
        **book_data
    }
    
    html_template = Template("""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>{{ book_title }}</title></head>
    <body>
        <div class="page debug-page"><h1>Data Source</h1><pre>{{ swapi_call_text }}</pre></div>
        <div class="page debug-page"><pre>{{ swapi_json_output }}</pre></div>
        
        <div class="page blank-page"></div><div class="page blank-page"></div>
        <div class="page blank-page"></div><div class="page blank-page"></div>
        
        <div class="page title-page">
            <div class="title-main-block">
                <div class="title-decoration">✧</div>
                <h1 class="book-title">{{ book_title }}</h1>
                <div class="title-decoration">✦</div>
                <h2 class="subtitle">A PERSONAL INTERPRETATION</h2>
            </div>
        </div>
        
        <div class="page print-date-page">
            <p>A personalized edition created on<br>{{ print_date }}</p>
        </div>

        <div class="page blank-page"></div><div class="page blank-page"></div>
        
        <div class="page toc-page">
            <h1>Contents</h1>
            <ul class="toc-list">
            {% for entry in toc_entries %}
                <li>
                    <a href="{{ entry.href }}">
                        <span class="entry-title">{{ entry.title }}</span>
                        <span class="leader"></span>
                        <span class="page-num"></span>
                    </a>
                </li>
            {% endfor %}
            </ul>
        </div>

        <div class="page blank-page"></div>
        
        {% if preface_text %}
        <div class="page content-page" id="preface">
            <h2>Preface</h2>
            <div class="content-block">{% for p in preface_text.split('\\n\\n') %}<p>{{ p }}</p>{% endfor %}</div>
        </div>
        <div class="page blank-page"></div>
        {% endif %}
        
        {% if has_prologue %}
        <div class="page content-page" id="prologue">
            <h2>Introduction</h2>
            <div class="content-block">{% for p in prologue_text.split('\\n\\n') %}<p>{{ p }}</p>{% endfor %}</div>
        </div>
        <div class="page blank-page"></div>
        {% endif %}

        {% for chapter in chapters %}
        <div class="page chapter-title-page">
            <!-- FIX #2: Restored the more interesting chapter title design -->
            <div class="chapter-title-content">
                <span class="chapter-number">Section {{ loop.index }}</span>
                <h2>{{ chapter.heading }}</h2>
            </div>
        </div>

        {% if chapter.image_path %}
        <div class="page image-page">
            <div class="image-container">
                <img src="{{ chapter.image_path }}" alt="Symbolic image for {{ chapter.heading }}">
            </div>
        </div>
        {% endif %}

        <div class="page content-page" id="chapter-{{ loop.index }}">
            <div class="content-block">
            {% for p in chapter.content.split('\\n\\n') %}<p>{{ p }}</p>{% endfor %}
            </div>
        </div>
        {% if not loop.last %}<div class="page blank-page"></div>{% endif %}
        {% endfor %} 
        
        {% if has_epilogue %}
        <div class="page blank-page"></div>
        <div class="page content-page" id="epilogue">
            <h2>Conclusion</h2>
            <div class="content-block">{% for p in epilogue_text.split('\\n\\n') %}<p>{{ p }}</p>{% endfor %}</div>
        </div>
        {% endif %}
    </body>
    </html>
    """)
    rendered_html = html_template.render(template_context)

    fonts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'fonts'))
    baskerville_regular_uri = pathlib.Path(os.path.abspath(os.path.join(fonts_dir, 'LibreBaskerville-Regular.ttf'))).as_uri()
    baskerville_italic_uri = pathlib.Path(os.path.abspath(os.path.join(fonts_dir, 'LibreBaskerville-Italic.ttf'))).as_uri()
    baskerville_bold_uri = pathlib.Path(os.path.abspath(os.path.join(fonts_dir, 'LibreBaskerville-Bold.ttf'))).as_uri()

    font_config = f"""
    @font-face  {{ font-family: 'Baskerville'; src: url('{baskerville_regular_uri}'); }}
    @font-face {{ font-family: 'Baskerville'; font-style: italic; src: url('{baskerville_italic_uri}'); }}
    @font-face {{ font-family: 'Baskerville'; font-weight: bold; src: url('{baskerville_bold_uri}'); }}
    """
    
    main_css = """
    @page { size: 140mm 216mm; margin: 25mm; }
    @page:blank { @bottom-center { content: ""; } }
    @page main { @bottom-center { content: counter(page); font-family: 'Baskerville', serif; font-size: 9pt; } }
    @page image-page-style { margin: 0; }
    body { font-family: 'Baskerville', serif; font-size: 11pt; line-height: 1.6; }
    .page { page-break-after: always; position: relative; height: 100%; }
    body > div:last-of-type { page-break-after: auto; }
    h1, h2, h3 { font-weight: bold; margin: 0; text-align: center; }
    
    /* FIX #3: Center the debug page content */
    .debug-page {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2em;
        box-sizing: border-box;
    }
    .debug-page pre { white-space: pre-wrap; word-wrap: break-word; font-size: 8pt; line-height: 1.5; }
    
    .image-page { page: image-page-style; display: flex; justify-content: center; align-items: center; width: 100%; height: 100%; background-color: #000000; }
    .image-container img { max-width: 100%; max-height: 100%; object-fit: contain; }
    .title-page { display: flex; flex-direction: column; align-items: center; text-align: center; }
    .title-main-block { margin: auto 0; }
    .book-title { font-size: 38pt; font-weight: bold; margin: 0.5em 0; line-height: 1.2; }
    .subtitle { font-size: 14pt; margin: 1em 0; letter-spacing: 0.2em; text-transform: uppercase; }
    .title-decoration { font-size: 24pt; margin: 1em 0; color: #555; }
    .print-date-page { display: flex; flex-direction: column; justify-content: flex-end; align-items: center; height: 100%; box-sizing: border-box; }
    .print-date-page p { font-style: italic; font-size: 10pt; margin-bottom: 20pt; }

    /* --- FIX #1: NEW, ROBUST TABLE OF CONTENTS STYLING --- */
    .toc-page { padding: 2em 0; page: main; }
    .toc-page h1 { font-size: 32pt; margin-bottom: 1.2em; letter-spacing: 0.1em; }
    .toc-list { list-style: none; padding: 0; width: 85%; margin: 0 auto; }
    .toc-list li { margin-bottom: 1.2em; }
    .toc-list a {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        text-decoration: none;
        color: black;
    }
    .toc-list .entry-title {
        order: 1; /* Title comes first */
        padding-right: 0.5em;
        line-height: 1.4; /* Allow space for wrapped lines */
    }
    .toc-list .leader {
        order: 2; /* Leader dots come second */
        flex-grow: 1;
        border-bottom: 1px dotted rgba(0,0,0,0.5);
        position: relative;
        top: -0.3em;
    }
    .toc-list .page-num {
        order: 3; /* Page number comes last */
        padding-left: 0.5em;
        font-size: 12pt;
    }
    .toc-list .page-num::before {
        content: target-counter(attr(href), page);
    }
    /* --- END OF TOC FIX --- */

    /* --- FIX #2: RESTORED CHAPTER TITLE STYLING --- */
    .chapter-title-page { display: flex; align-items: center; justify-content: center; text-align: center; }
    .chapter-title-content { padding: 2em; }
    .chapter-number {
        display: block;
        font-size: 16pt;
        font-style: italic;
        color: #666;
        margin-bottom: 1.5em;
        text-transform: uppercase;
    }
    .chapter-title-content h2 {
        font-size: 32pt;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        line-height: 1.3;
    }
    /* --- END OF CHAPTER TITLE FIX --- */
    
    .content-page { page: main; }
    .content-page h2 { font-size: 20pt; text-transform: uppercase; margin-bottom: 2.5em; letter-spacing: 0.1em; }
    .content-block { margin: 0 auto; max-width: 100%; }
    .content-block p { text-align: justify; text-indent: 2em; margin-bottom: 0; line-height: 1.7; hyphens: auto; }
    .content-block p:first-child { text-indent: 0; }
    .content-block p:first-child::first-letter { font-size: 3.5em; font-weight: bold;}
    """
    
    css = CSS(string=font_config + main_css)
    base_url = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    HTML(string=rendered_html, base_url=base_url).write_pdf(output_path, stylesheets=[css])
    
    return output_path