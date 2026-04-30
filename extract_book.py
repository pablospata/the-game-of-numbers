"""
Extract "The Game of Numbers" by Nick Murray from the flipbook's search.json
and organize it into Markdown files by Part and Chapter.
"""

import json
import os
import re
import urllib.request

# ── Configuration ──────────────────────────────────────────────────────────
JSON_URL = "https://nickmurraynewsletters.s3.amazonaws.com/TGON-2021/files/data/search.json"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "src")

# ── Chapter/Section mapping (pageNumber → chapter info) ───────────────────
# Derived from the Table of Contents (pages 8-13) of the flipbook.
# Format: (start_page, chapter_num_or_id, title, part)
# Page numbers here refer to the BOOK's page numbers shown in the JSON.

STRUCTURE = [
    # Front matter
    (1, "00", "Title Page", "front"),
    (3, "00b", "Title Page (Full)", "front"),
    (4, "00c", "Copyright", "front"),
    (5, "00d", "Epigraph", "front"),
    (6, "00e", "Dedication", "front"),
    (7, "00f", "Contents", "front"),
    
    # Preface & Introduction
    (14, "preface", "Preface", "preface"),
    (16, "introduction", "Introduction — So Many Prospects, So Little Time", "introduction"),
    
    # PART ONE: BELIEF
    (22, "part1_cover", "Part One: Belief", "part1"),
    (23, "01", "Belief Drives Behavior", "part1"),
    (26, "02", "A Business of Doing, Not of Knowing", "part1"),
    (29, "03", "You're Building Your Own Business", "part1"),
    (34, "04", "Faith", "part1"),
    (37, "05", "The Myth of Motivation", "part1"),
    (39, "06", "Gratitude", "part1"),
    (44, "07", "Prospecting Ends", "part1"),
    (47, "08", "Fear, Part One", "part1"),
    (49, "09", "Fear, Part Two", "part1"),
    (52, "10", "Today", "part1"),
    (54, "11", "Authenticity", "part1"),
    (56, "12", "A Sense of Who You Are", "part1"),
    (62, "13", "A Positive Value Proposition, From Day One", "part1"),
    (65, "14", "Toward a First Draft", "part1"),
    (66, "15", "Belief System 1.0", "part1"),
    (77, "16", "It's All Just a Test, Anyway", "part1"),
    
    # PART TWO: BEHAVIOR
    (78, "part2_cover", "Part Two: Behavior", "part2"),
    (79, "17", "You Are What You Do", "part2"),
    (83, "18", "Risking 'No'", "part2"),
    (87, "19", "The Golden 'Almost'", "part2"),
    (90, "20", "'No' Is Not 'Rejection'", "part2"),
    (93, "21", "'No' Doesn't Hurt", "part2"),
    (96, "22", "The Way We Experience 'No'", "part2"),
    (98, "23", "Why We Think 'No' Hurts", "part2"),
    (101, "24", "Why Prospecting Programs Fail", "part2"),
    (103, "25", "How Do You Prospect?", "part2"),
    (106, "26", "Method Doesn't Matter", "part2"),
    (109, "27", "Overcoming Method Anxiety", "part2"),
    (111, "28", "A Pre-Approach Letter for These Times", "part2"),
    (113, "29", "If It Feels Good, Do It", "part2"),
    (115, "30", "Once More with Feeling: Marketing Isn't Prospecting", "part2"),
    (117, "31", "Whom Do You Prospect?", "part2"),
    (120, "32", "Two Words About Buying a Practice: Think Thrice", "part2"),
    (122, "33", "Goals, Plans, Numbers and Other Ephemera", "part2"),
    (124, "34", "'Comfort Zones'", "part2"),
    (125, "35", "Avoidance Poisons the Rest of Your Life", "part2"),
    (127, "36", "What Are We Prospecting for?", "part2"),
    (129, "37", "The Double-Tap Question", "part2"),
    (131, "38", "Words and Music", "part2"),
    (133, "39", "The Retirement Income Conversation: Non-Verbal Aspects", "part2"),
    (135, "40", "Double-Tap: Second Opinion", "part2"),
    (138, "41", "Second Opinion: Commentary", "part2"),
    (140, "42", "Double-Tap Variations", "part2"),
    (142, "43", "What Are These Scripts for?", "part2"),
    (144, "44", "Prospecting with Your Authentic Self", "part2"),
    (146, "45", "A Valediction from Aristotle", "part2"),
    
    # PART THREE: ENDURANCE
    (148, "part3_cover", "Part Three: Endurance", "part3"),
    (149, "46", "Cosmic Habitforce", "part3"),
    (150, "47", "Getting Off the Couch", "part3"),
    (151, "48", "The Error of Judgment", "part3"),
    (153, "49", "Establishing a Baseline", "part3"),
    (155, "50", "What If You Can't?", "part3"),
    (157, "51", "Raising the Baseline", "part3"),
    (158, "52", "It's Not the Level; It's the Trajectory", "part3"),
    (159, "53", "Remember How We're Keeping Score", "part3"),
    (161, "54", "Record Your Activity", "part3"),
    (163, "55", "Shark Attack", "part3"),
    (165, "56", "Tactical—and Temporary—Retreat", "part3"),
    (168, "57", "Fun with Rewards", "part3"),
    (172, "58", "These Are the Fundamentals", "part3"),
    (175, "59", "A Special Guide for Re-Starters", "part3"),
    (177, "60", "Re-Starting, Part Deux: Clearing Away the Wreckage", "part3"),
    (179, "61", "Firing Your Biggest PITA", "part3"),
    (181, "62", "The Letter", "part3"),
    (183, "63", "Stop Buying Lottery Tickets", "part3"),
    (185, "64", "The Third Piece: Offloading Busywork", "part3"),
    (187, "65", "Oxygenating Your Attitude", "part3"),
    (188, "66", "Keep Those Cards and Letters Coming", "part3"),
    (190, "67", "Thank You for Everything…and Nothing", "part3"),
    (193, "68", "Tipping", "part3"),
    (196, "69", "Take It from Here", "part3"),
    (198, "70", "A Book of Essentials", "part3"),
    (200, "71", "The Next Right Thing", "part3"),
    
    # PART FOUR: SKILL
    (204, "part4_cover", "Part Four: Skill", "part4"),
    (205, "72", "Skill Follows Endurance", "part4"),
    (207, "73", "Lifestyle Is the Critical Variable in the Equation", "part4"),
    (209, "74", "'Selling' Is the Act of Principled Persuasion", "part4"),
    (211, "75", "The Single Greatest Skill", "part4"),
    (213, "76", "The First Rule of Discourse", "part4"),
    (216, "77", "The Second Rule of Discourse", "part4"),
    (218, "78", "The Third Rule of Discourse", "part4"),
    (220, "79", "Begin Drawing Your Circle of Competence", "part4"),
    (223, "80", "Portfolio Management: Outside Everybody's Circle", "part4"),
    (225, "81", "Behavior Is the Eight Hundred Pound Gorilla", "part4"),
    (227, "82", "Listen to Yourself, Too", "part4"),
    (229, "83", "Write Out What You're Going to Say", "part4"),
    (232, "84", "Q&A: What's the Question Behind the Question?", "part4"),
    (234, "85", "Perfecting the Non-Answer", "part4"),
    (237, "86", "At the End of Every 'Failed' Interview", "part4"),
    (238, "87", "Go Out with Class, and Leave the Door Open", "part4"),
    (240, "88", "Introductions, Not Referrals", "part4"),
    
    # CODA & Back matter
    (241, "coda", "Coda: Optimism Is the Only Realism", "coda"),
    (245, "resources", "Resources", "back"),
    (248, "companion", "Nick's Companion Book for Wealth Managers", "back"),
    (250, "acknowledgments", "Acknowledgments", "back"),
    (251, "about", "About the Author", "back"),
]


def download_json():
    """Download the search.json from AWS."""
    print(f"Downloading search.json from {JSON_URL}...")
    req = urllib.request.Request(JSON_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    pages = data["results"]["page"]
    print(f"  -> {len(pages)} pages loaded.")
    return {p["pageNumber"]: p["data"] for p in pages}


def clean_text(text):
    """Clean up text extracted from the search JSON."""
    # Remove header artifacts like "N I CK M URRA Y'S THE G AME O F N U MBE R S"
    # Handle both straight and curly apostrophes
    text = re.sub(r"N\s+I\s+CK\s+M\s+URRA\s+Y['\u2019']S\s+THE\s+G\s+AME\s+O\s+F\s+N\s+U\s+MBE\s+R\s+S\s*", "", text)
    # Remove section headers like "B EL IEF", "B EH A V IO R", etc.
    text = re.sub(r"B EL IEF ", " ", text)
    text = re.sub(r"B EH A V IO R ", " ", text)
    text = re.sub(r"INT R O D U C T IO N ", " ", text)
    text = re.sub(r"P R EF A C E ", " ", text)
    text = re.sub(r"END U R A NC E ", " ", text)
    text = re.sub(r"S K IL L ", " ", text)
    text = re.sub(r"^CODA ", " ", text)
    # Remove trailing page numbers (standalone number at end)
    text = re.sub(r"\s+\d{1,3}\s*$", "", text.strip())
    # Fix common OCR/extraction artifacts
    text = text.replace("\\t", "\t")
    text = text.replace("  ", " ")
    # Clean up bullet points with N tab
    text = re.sub(r"N\t", "- ", text)
    # Fix hyphenated words at line breaks
    text = re.sub(r"(\w)- (\w)", r"\1\2", text)
    return text.strip()


def get_chapter_pages(idx):
    """Return the range of pages for a given chapter index."""
    start_page = STRUCTURE[idx][0]
    if idx + 1 < len(STRUCTURE):
        end_page = STRUCTURE[idx + 1][0] - 1
    else:
        end_page = 254  # last page
    return start_page, end_page


def build_chapter_text(pages_dict, start_page, end_page, chapter_num=None, title=None):
    """Concatenate and clean text for a range of pages."""
    parts = []
    for pn in range(start_page, end_page + 1):
        if pn in pages_dict:
            cleaned = clean_text(pages_dict[pn])
            if cleaned:
                parts.append(cleaned)
    text = "\n\n".join(parts)
    # Remove leading chapter number + title that duplicates our H1 heading
    if chapter_num and chapter_num.isdigit() and title:
        # Try to remove "1 Belief Drives Behavior " or "28 A Pre-Approach Letter..."
        pattern = re.escape(f"{int(chapter_num)} {title}")
        # Also handle slight variations (tab/spaces)
        pattern = pattern.replace(r"\ ", r"\s+")
        text = re.sub(r"^\s*" + pattern + r"\s*", "", text, count=1)
    return text.strip()


def make_filename(chapter_id, title):
    """Create a clean filename from chapter ID and title."""
    # Sanitize title for filename
    safe = title.lower()
    safe = re.sub(r"[''\":]", "", safe)
    safe = re.sub(r"[^a-z0-9]+", "-", safe)
    safe = safe.strip("-")
    if safe.startswith("chapter-"):
        safe = safe[8:]
    return f"{chapter_id}-{safe}.md"


def write_chapter(filepath, chapter_num, title, text, part_label=None):
    """Write a single chapter markdown file."""
    with open(filepath, "w", encoding="utf-8") as f:
        # Chapter heading
        if chapter_num and chapter_num.isdigit():
            f.write(f"# Chapter {int(chapter_num)}: {title}\n\n")
        else:
            f.write(f"# {title}\n\n")
        
        f.write(text)
        f.write("\n")


def main():
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Download and parse JSON
    pages = download_json()
    
    # Track what we generate
    generated = []
    
    # Group chapters by part for the README
    part_names = {
        "front": "Front Matter",
        "preface": "Preface",
        "introduction": "Introduction",
        "part1": "Part One: Belief (Chapters 1–16)",
        "part2": "Part Two: Behavior (Chapters 17–45)",
        "part3": "Part Three: Endurance (Chapters 46–71)",
        "part4": "Part Four: Skill (Chapters 72–88)",
        "coda": "Coda",
        "back": "Back Matter",
    }
    
    # Skip front matter pages (title, copyright, TOC, etc.) — just chapters
    skip_front = {"00", "00b", "00c", "00d", "00e", "00f"}
    
    for idx, (start_page, ch_id, title, part) in enumerate(STRUCTURE):
        if ch_id in skip_front:
            continue
        
        start_p, end_p = get_chapter_pages(idx)
        text = build_chapter_text(pages, start_p, end_p, chapter_num=ch_id, title=title)
        
        if not text.strip():
            print(f"  [!] Skipping empty: {ch_id} - {title}")
            continue
        
        # Part cover pages — just a title, merge into the first chapter of that part
        if ch_id.startswith("part") and ch_id.endswith("_cover"):
            continue
        
        filename = make_filename(ch_id, title)
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        write_chapter(filepath, ch_id, title, text, part)
        generated.append((ch_id, title, filename, part))
        print(f"  [OK] {filename}")
    
    # Generate README
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# The Game of Numbers — Nick Murray\n\n")
        f.write("**Client Acquisition for Financial Advisors**\n\n")
        f.write("Extracted from the 2021 edition flipbook.\n\n")
        f.write("---\n\n")
        f.write("## Table of Contents\n\n")
        
        current_part = None
        for ch_id, title, filename, part in generated:
            if part != current_part:
                current_part = part
                f.write(f"\n### {part_names.get(part, part)}\n\n")
            
            if ch_id.isdigit():
                f.write(f"- [{int(ch_id)}. {title}](src/{filename})\n")
            else:
                f.write(f"- [{title}](src/{filename})\n")
        
        f.write("\n---\n\n")
        f.write(f"*Total chapters extracted: {len(generated)}*\n")
    
    print(f"\nDone! {len(generated)} files written to {OUTPUT_DIR}")
    print(f"README generated at {readme_path}")


if __name__ == "__main__":
    main()
