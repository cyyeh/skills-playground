#!/usr/bin/env python3
"""Build script for the Skills static website.

Scans skills/ for SKILL.md files, converts markdown to HTML,
and generates a self-contained single-page app in dist/.
"""

import json
import os
import re
import shutil
from pathlib import Path

try:
    import markdown
    import yaml
except ImportError:
    print("Installing dependencies...")
    os.system("pip install markdown pyyaml")
    import markdown
    import yaml

ROOT = Path(__file__).parent
SKILLS_DIR = ROOT / "skills"
DIST_DIR = ROOT / "dist"

md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "attr_list"])


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from markdown text."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if match:
        fm = yaml.safe_load(match.group(1)) or {}
        body = match.group(2)
        return fm, body
    return {}, text


def md_to_html(text: str) -> str:
    """Convert markdown to HTML."""
    md.reset()
    return md.convert(text)


def split_into_sections(body: str) -> tuple[str, list[dict]]:
    """Split markdown body into an overview and h2 sections.

    Returns (overview_md, sections) where each section has
    'title', 'slug', 'body_md', and 'subsections' (h3 titles).
    Handles skills with no h2 headings (all content becomes overview).
    Deduplicates slugs to avoid ID collisions.
    """
    lines = body.split("\n")
    overview_lines = []
    sections = []
    current_section = None
    seen_h1 = False
    slug_counts: dict[str, int] = {}

    for line in lines:
        h2_match = re.match(r"^## (.+)$", line)
        if h2_match:
            if current_section:
                sections.append(current_section)
            title = h2_match.group(1).strip()
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            # Deduplicate slugs
            slug_counts[slug] = slug_counts.get(slug, 0) + 1
            if slug_counts[slug] > 1:
                slug = f"{slug}-{slug_counts[slug]}"
            current_section = {
                "title": title,
                "slug": slug,
                "lines": [],
                "subsections": [],
            }
            continue

        if current_section is None:
            # Skip the first h1 title line (already shown in header)
            if not seen_h1 and re.match(r"^# .+$", line):
                seen_h1 = True
                continue
            overview_lines.append(line)
        else:
            current_section["lines"].append(line)
            h3_match = re.match(r"^### (.+)$", line)
            if h3_match:
                current_section["subsections"].append(h3_match.group(1).strip())

    if current_section:
        sections.append(current_section)

    overview_md = "\n".join(overview_lines).strip()
    for s in sections:
        s["body_md"] = "\n".join(s["lines"]).strip()
        del s["lines"]

    return overview_md, sections


def _search_dirs(skill_dir: Path, subdir_name: str):
    """Yield candidate directories for resources (references/, examples/, evals/).

    Searches as a sibling of SKILL.md first, then walks up to the skill's
    root within skills/. This handles both flat layouts:
        skills/my-skill/SKILL.md + skills/my-skill/examples/
    and nested layouts:
        skills/my-skill/inner/SKILL.md + skills/my-skill/examples/
    """
    # Sibling first
    candidate = skill_dir / subdir_name
    if candidate.is_dir():
        yield candidate
    # Walk up toward SKILLS_DIR
    parent = skill_dir.parent
    while parent != SKILLS_DIR and parent != SKILLS_DIR.parent:
        if (parent / "SKILL.md").is_file():
            break
        # If a namesake sibling (parent.name/) owns a SKILL.md and it's not us,
        # then resources at this level belong to that skill, not ours
        owner = parent / parent.name
        if owner.is_dir() and (owner / "SKILL.md").is_file() and owner != skill_dir:
            parent = parent.parent
            continue
        candidate = parent / subdir_name
        if candidate.is_dir():
            yield candidate
        parent = parent.parent


def discover_skills() -> list[dict]:
    """Find all skills in the skills/ directory."""
    skills = []
    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        skill_dir = skill_md.parent
        text = skill_md.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)

        name = fm.get("name", skill_dir.name)
        description = fm.get("description", "")

        overview_md, sections = split_into_sections(body)
        overview_html = md_to_html(overview_md) if overview_md else ""
        for s in sections:
            s["body_html"] = md_to_html(s["body_md"])

        # Collect reference docs — search sibling and ancestor dirs
        refs = []
        for search_dir in _search_dirs(skill_dir, "references"):
            for ref_file in sorted(search_dir.glob("*.md")):
                ref_text = ref_file.read_text(encoding="utf-8")
                _, ref_body = parse_frontmatter(ref_text)
                refs.append({
                    "name": ref_file.stem.replace("-", " ").replace("_", " ").title(),
                    "filename": ref_file.name,
                    "html": md_to_html(ref_body),
                })
            break  # Use first found

        # Collect example files — search sibling and ancestor dirs
        examples = []
        example_files_to_copy = []
        example_exts = {".html", ".py", ".js", ".ts", ".json", ".png", ".jpg", ".svg"}
        for search_dir in _search_dirs(skill_dir, "examples"):
            for item in sorted(search_dir.iterdir()):
                if item.is_file() and item.suffix.lower() in example_exts:
                    web_path = f"examples/{name}/{item.name}"
                    examples.append({
                        "name": item.stem.replace("-", " ").replace("_", " ").title(),
                        "filename": item.name,
                        "src_path": str(item),
                        "web_path": web_path,
                    })
                    example_files_to_copy.append({
                        "src_path": str(item),
                        "web_path": web_path,
                    })
                elif item.is_dir():
                    # Subdirectory example project — copy all files
                    sub_files = []
                    for f in sorted(item.rglob("*")):
                        if f.is_file():
                            rel = f.relative_to(search_dir)
                            sub_files.append({
                                "src_path": str(f),
                                "web_path": f"examples/{name}/{rel}",
                            })
                    if sub_files:
                        example_files_to_copy.extend(sub_files)
                        # Find entry point for UI card
                        entry_wp = next(
                            (sf["web_path"] for sf in sub_files if sf["web_path"].endswith("/index.html")),
                            next(
                                (sf["web_path"] for sf in sub_files if sf["web_path"].endswith(".html")),
                                sub_files[0]["web_path"],
                            ),
                        )
                        examples.append({
                            "name": item.name.replace("-", " ").replace("_", " ").title(),
                            "filename": item.name,
                            "src_path": next(sf["src_path"] for sf in sub_files if sf["web_path"] == entry_wp),
                            "web_path": entry_wp,
                        })
            break  # Use first found

        # Collect evals — search sibling and ancestor dirs
        evals = []
        for search_dir in _search_dirs(skill_dir, "evals"):
            evals_file = search_dir / "evals.json"
            if evals_file.is_file():
                evals_data = json.loads(evals_file.read_text(encoding="utf-8"))
                evals = evals_data.get("evals", [])
                break

        skills.append({
            "id": name,
            "name": name,
            "description": description,
            "overview_html": overview_html,
            "sections": sections,
            "references": refs,
            "examples": examples,
            "example_files": example_files_to_copy,
            "evals": evals,
        })

    return skills


def build_sidebar_structure(skills: list[dict]) -> list[dict]:
    """Organize skills into groups by top-level directory under skills/.

    Every top-level directory becomes a group with its skills and
    pooled examples.
    """
    skill_groups: dict[str, list[dict]] = {}
    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        top_dir = skill_md.relative_to(SKILLS_DIR).parts[0]
        name = skill_md.parent.name
        skill_obj = next((s for s in skills if s["id"] == name), None)
        if skill_obj:
            skill_groups.setdefault(top_dir, []).append(skill_obj)

    structure = []
    seen: set[str] = set()
    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        top_dir = skill_md.relative_to(SKILLS_DIR).parts[0]
        if top_dir in seen:
            continue
        seen.add(top_dir)
        group_skills = skill_groups.get(top_dir, [])
        # Pool all unique examples across skills in this group
        all_examples = []
        seen_paths: set[str] = set()
        for s in group_skills:
            for ex in s["examples"]:
                if ex["web_path"] not in seen_paths:
                    seen_paths.add(ex["web_path"])
                    all_examples.append(ex)
        structure.append({
            "name": top_dir,
            "skills": group_skills,
            "examples": all_examples,
        })

    return structure


def copy_examples(skills: list[dict]) -> None:
    """Copy example files to dist/examples/."""
    for skill in skills:
        for ef in skill["example_files"]:
            dest = DIST_DIR / ef["web_path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ef["src_path"], dest)


def generate_html(skills: list[dict], structure: list[dict]) -> str:
    """Generate the full SPA HTML."""
    first_skill_id = skills[0]["id"] if skills else None

    # Build sidebar items — each top-level dir is a group with skills + examples
    sidebar_items = ""
    for i, entry in enumerate(structure):
        group_name = entry["name"]
        open_class = "open" if i == 0 else ""
        sidebar_items += f'''<div class="sidebar-group {open_class}">
            <button class="sidebar-group-toggle" onclick="toggleGroup(this)"><span class="group-arrow">&#x25B6;</span>{group_name}</button>
            <div class="sidebar-group-content">
                <div class="sidebar-section-label">skills</div>\n'''
        for skill in entry["skills"]:
            active = "active" if skill["id"] == first_skill_id else ""
            sidebar_items += f'''                <button class="sidebar-item {active}" data-skill="{skill['id']}" onclick="selectSkill('{skill['id']}', this)">{skill['name']}</button>\n'''
        if entry["examples"]:
            sidebar_items += '''                <div class="sidebar-section-label">examples</div>\n'''
            for ex in entry["examples"]:
                sidebar_items += f'''                <a href="{ex["web_path"]}" target="_blank" rel="noopener" class="sidebar-example-link">{ex["name"]}</a>\n'''
        sidebar_items += '''            </div></div>\n'''

    # Build content sections
    content_sections = ""
    for i, skill in enumerate(skills):
        display = "block" if i == 0 else "none"

        # References
        refs_html = ""
        if skill["references"]:
            refs_html += '<div class="references-section"><h2>Reference Documents</h2>'
            for ref in skill["references"]:
                refs_html += f'''
                <details class="reference-block">
                    <summary>{ref['name']}</summary>
                    <div class="reference-content">{ref['html']}</div>
                </details>'''
            refs_html += "</div>"

        # Evals
        evals_html = ""
        if skill["evals"]:
            evals_html += '<div class="evals-section"><h2>Evaluation Prompts</h2><div class="evals-list">'
            for ev in skill["evals"]:
                evals_html += f'''
                <div class="eval-card">
                    <div class="eval-prompt">{ev['prompt']}</div>
                    <div class="eval-expected">{ev['expected_output']}</div>
                </div>'''
            evals_html += "</div></div>"

        # Table of contents
        toc_html = ""
        if skill["sections"]:
            toc_items = ""
            for s in skill["sections"]:
                sub_items = ""
                if s["subsections"]:
                    sub_items = "<ul>" + "".join(
                        f'<li>{sub}</li>' for sub in s["subsections"]
                    ) + "</ul>"
                toc_items += f'<li><a href="javascript:void(0)" onclick="openSection(\'{skill["id"]}\', \'{s["slug"]}\')">{s["title"]}</a>{sub_items}</li>'
            toc_html = f'<nav class="toc"><h3>Contents</h3><ol>{toc_items}</ol></nav>'

        # Sections as collapsible blocks
        sections_html = ""
        for s in skill["sections"]:
            sections_html += f'''
            <details class="section-block" id="section-{skill['id']}-{s['slug']}">
                <summary class="section-summary">{s['title']}</summary>
                <div class="section-content skill-body">{s['body_html']}</div>
            </details>'''

        content_sections += f'''
        <div class="skill-content" id="skill-{skill['id']}" style="display:{display}">
            <div class="skill-header">
                <h1>{skill['name']}</h1>
                <p class="skill-description">{skill['description']}</p>
            </div>
            <div class="skill-overview skill-body">{skill['overview_html']}</div>
            {toc_html}
            <div class="skill-sections">{sections_html}</div>
            {refs_html}
            {evals_html}
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skills Browser</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        :root {{
            --bg: #0f172a;
            --bg-sidebar: #111827;
            --bg-code: #1e293b;
            --bg-hover: #1e293b;
            --bg-active: rgba(52, 211, 153, 0.1);
            --text: #e2e8f0;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --heading: #f1f5f9;
            --accent: #34d399;
            --accent-dim: rgba(52, 211, 153, 0.15);
            --border: #334155;
            --border-light: #1e293b;
            --sidebar-w: 280px;
            --font-mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
            --font-sans: system-ui, -apple-system, 'Segoe UI', sans-serif;
        }}

        html {{ height: 100%; }}
        body {{
            font-family: var(--font-sans);
            font-size: 16px;
            line-height: 1.7;
            color: var(--text);
            background: var(--bg);
            height: 100%;
            overflow: hidden;
        }}

        /* Layout */
        .app {{
            display: flex;
            height: 100%;
        }}

        /* Sidebar */
        .sidebar {{
            width: var(--sidebar-w);
            min-width: var(--sidebar-w);
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            height: 100%;
            overflow-y: auto;
        }}
        .sidebar-header {{
            padding: 24px 20px 16px;
            border-bottom: 1px solid var(--border);
        }}
        .sidebar-header h2 {{
            color: var(--heading);
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}
        .sidebar-list {{
            padding: 8px;
            flex: 1;
        }}
        .sidebar-item {{
            display: block;
            width: 100%;
            text-align: left;
            padding: 10px 16px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-family: var(--font-sans);
            font-size: 14px;
            cursor: pointer;
            border-radius: 6px;
            transition: all 0.15s ease;
            margin-bottom: 2px;
        }}
        .sidebar-item:hover {{
            background: var(--bg-hover);
            color: var(--text);
        }}
        .sidebar-item.active {{
            background: var(--bg-active);
            color: var(--accent);
            font-weight: 500;
        }}

        /* Sidebar groups */
        .sidebar-group {{
            margin-bottom: 4px;
        }}
        .sidebar-group-toggle {{
            display: flex;
            align-items: center;
            gap: 8px;
            width: 100%;
            text-align: left;
            padding: 10px 16px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-family: var(--font-sans);
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            border-radius: 6px;
            transition: all 0.15s ease;
        }}
        .sidebar-group-toggle:hover {{
            background: var(--bg-hover);
            color: var(--text);
        }}
        .group-arrow {{
            font-size: 8px;
            transition: transform 0.2s;
        }}
        .sidebar-group.open .group-arrow {{
            transform: rotate(90deg);
        }}
        .sidebar-group-content {{
            display: none;
            padding-left: 12px;
        }}
        .sidebar-group.open .sidebar-group-content {{
            display: block;
        }}
        .sidebar-section-label {{
            padding: 10px 16px 4px;
            color: var(--text-muted);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 600;
        }}
        .sidebar-example-link {{
            display: block;
            padding: 6px 16px;
            color: var(--text-muted);
            font-size: 13px;
            text-decoration: none;
            border-radius: 6px;
            transition: all 0.15s ease;
        }}
        .sidebar-example-link:hover {{
            color: var(--accent);
            background: var(--bg-hover);
        }}

        /* Mobile hamburger */
        .hamburger {{
            display: none;
            position: fixed;
            top: 16px;
            left: 16px;
            z-index: 1000;
            background: var(--bg-sidebar);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 20px;
        }}
        .sidebar-overlay {{
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.5);
            z-index: 998;
        }}

        /* Main content */
        .main {{
            flex: 1;
            overflow-y: auto;
            padding: 48px 64px;
            max-width: 100%;
        }}
        .main::-webkit-scrollbar {{ width: 8px; }}
        .main::-webkit-scrollbar-track {{ background: var(--bg); }}
        .main::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 4px; }}
        .main::-webkit-scrollbar-thumb:hover {{ background: var(--text-muted); }}

        .skill-content {{ max-width: 860px; }}

        /* Skill header */
        .skill-header {{
            margin-bottom: 40px;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border);
        }}
        .skill-header h1 {{
            color: var(--heading);
            font-size: 32px;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 8px;
        }}
        .skill-description {{
            color: var(--text-secondary);
            font-size: 15px;
            line-height: 1.6;
        }}

        /* Markdown body styles */
        .skill-body h1 {{
            color: var(--heading);
            font-size: 28px;
            font-weight: 700;
            margin: 48px 0 16px;
            letter-spacing: -0.02em;
        }}
        .skill-body h2 {{
            color: var(--heading);
            font-size: 22px;
            font-weight: 600;
            margin: 40px 0 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
        }}
        .skill-body h3 {{
            color: var(--heading);
            font-size: 18px;
            font-weight: 600;
            margin: 32px 0 8px;
        }}
        .skill-body h4 {{
            color: var(--text);
            font-size: 16px;
            font-weight: 600;
            margin: 24px 0 8px;
        }}
        .skill-body p {{
            margin: 0 0 16px;
        }}
        .skill-body a {{
            color: var(--accent);
            text-decoration: none;
        }}
        .skill-body a:hover {{
            text-decoration: underline;
        }}
        .skill-body strong {{
            color: var(--heading);
            font-weight: 600;
        }}
        .skill-body ul, .skill-body ol {{
            margin: 0 0 16px;
            padding-left: 24px;
        }}
        .skill-body li {{
            margin-bottom: 6px;
        }}
        .skill-body li > ul, .skill-body li > ol {{
            margin-top: 6px;
            margin-bottom: 0;
        }}
        .skill-body code {{
            font-family: var(--font-mono);
            font-size: 0.875em;
            background: var(--bg-code);
            padding: 2px 6px;
            border-radius: 4px;
            color: #f0abfc;
        }}
        .skill-body pre {{
            background: var(--bg-code);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px 20px;
            overflow-x: auto;
            margin: 0 0 16px;
        }}
        .skill-body pre code {{
            background: none;
            padding: 0;
            color: var(--text);
            font-size: 13px;
            line-height: 1.6;
        }}
        .skill-body blockquote {{
            border-left: 3px solid var(--accent);
            background: rgba(52, 211, 153, 0.05);
            padding: 12px 20px;
            margin: 0 0 16px;
            border-radius: 0 6px 6px 0;
        }}
        .skill-body blockquote p:last-child {{
            margin-bottom: 0;
        }}
        .skill-body hr {{
            border: none;
            border-top: 1px solid var(--border);
            margin: 32px 0;
        }}
        .skill-body table {{
            width: 100%;
            border-collapse: collapse;
            margin: 0 0 16px;
            font-size: 14px;
        }}
        .skill-body th {{
            background: var(--bg-code);
            color: var(--heading);
            font-weight: 600;
            text-align: left;
            padding: 10px 14px;
            border: 1px solid var(--border);
        }}
        .skill-body td {{
            padding: 10px 14px;
            border: 1px solid var(--border);
        }}
        .skill-body img {{
            max-width: 100%;
            border-radius: 8px;
        }}

        /* Table of contents */
        .toc {{
            background: var(--bg-code);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px 24px;
            margin-bottom: 24px;
        }}
        .toc h3 {{
            color: var(--heading);
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 12px;
        }}
        .toc ol {{
            margin: 0;
            padding-left: 20px;
        }}
        .toc ol li {{
            margin-bottom: 4px;
            font-size: 14px;
        }}
        .toc ol li a {{
            color: var(--accent);
            text-decoration: none;
            transition: color 0.15s;
        }}
        .toc ol li a:hover {{
            text-decoration: underline;
        }}
        .toc ol ul {{
            list-style: none;
            padding-left: 16px;
            margin: 4px 0 2px;
        }}
        .toc ol ul li {{
            color: var(--text-muted);
            font-size: 13px;
            margin-bottom: 2px;
        }}
        .toc ol ul li::before {{
            content: "\\2013\\00a0";
            color: var(--border);
        }}

        /* Section blocks */
        .skill-sections {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 24px;
        }}
        .section-block {{
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
            transition: border-color 0.15s;
        }}
        .section-block:hover {{
            border-color: var(--text-muted);
        }}
        .section-block[open] {{
            border-color: var(--accent);
        }}
        .section-summary {{
            padding: 14px 20px;
            cursor: pointer;
            color: var(--heading);
            font-weight: 600;
            font-size: 16px;
            background: var(--bg-code);
            user-select: none;
            transition: background 0.15s;
            list-style: none;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section-summary::-webkit-details-marker {{ display: none; }}
        .section-summary::before {{
            content: "\\25B6";
            font-size: 10px;
            color: var(--text-muted);
            transition: transform 0.2s;
        }}
        .section-block[open] .section-summary::before {{
            transform: rotate(90deg);
            color: var(--accent);
        }}
        .section-summary:hover {{
            background: var(--bg-hover);
        }}
        .section-block[open] .section-summary {{
            border-bottom: 1px solid var(--border);
        }}
        .section-content {{
            padding: 24px;
        }}

        /* Overview */
        .skill-overview {{
            margin-bottom: 24px;
        }}

        /* References */
        .references-section, .evals-section {{
            margin-top: 48px;
            padding-top: 32px;
            border-top: 1px solid var(--border);
        }}
        .references-section h2, .evals-section h2 {{
            color: var(--heading);
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 16px;
        }}
        .reference-block {{
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 8px;
            overflow: hidden;
        }}
        .reference-block summary {{
            padding: 12px 20px;
            cursor: pointer;
            color: var(--text);
            font-weight: 500;
            background: var(--bg-code);
            user-select: none;
            transition: background 0.15s;
        }}
        .reference-block summary:hover {{
            background: var(--bg-hover);
        }}
        .reference-block[open] summary {{
            border-bottom: 1px solid var(--border);
        }}
        .reference-content {{
            padding: 20px;
        }}
        /* Reuse skill-body styles in reference-content */
        .reference-content h1,
        .reference-content h2,
        .reference-content h3,
        .reference-content h4 {{ color: var(--heading); }}
        .reference-content h1 {{ font-size: 24px; margin: 32px 0 12px; }}
        .reference-content h2 {{ font-size: 20px; margin: 28px 0 10px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }}
        .reference-content h3 {{ font-size: 16px; margin: 20px 0 8px; }}
        .reference-content p {{ margin: 0 0 12px; }}
        .reference-content a {{ color: var(--accent); text-decoration: none; }}
        .reference-content a:hover {{ text-decoration: underline; }}
        .reference-content strong {{ color: var(--heading); }}
        .reference-content ul, .reference-content ol {{ margin: 0 0 12px; padding-left: 24px; }}
        .reference-content li {{ margin-bottom: 4px; }}
        .reference-content code {{
            font-family: var(--font-mono); font-size: 0.875em;
            background: var(--bg-code); padding: 2px 6px; border-radius: 4px; color: #f0abfc;
        }}
        .reference-content pre {{
            background: var(--bg-code); border: 1px solid var(--border);
            border-radius: 8px; padding: 14px 18px; overflow-x: auto; margin: 0 0 12px;
        }}
        .reference-content pre code {{ background: none; padding: 0; color: var(--text); font-size: 13px; }}
        .reference-content table {{ width: 100%; border-collapse: collapse; margin: 0 0 12px; font-size: 14px; }}
        .reference-content th {{ background: var(--bg); color: var(--heading); font-weight: 600; text-align: left; padding: 8px 12px; border: 1px solid var(--border); }}
        .reference-content td {{ padding: 8px 12px; border: 1px solid var(--border); }}
        .reference-content blockquote {{
            border-left: 3px solid var(--accent); background: rgba(52,211,153,0.05);
            padding: 10px 16px; margin: 0 0 12px; border-radius: 0 6px 6px 0;
        }}
        .reference-content hr {{ border: none; border-top: 1px solid var(--border); margin: 24px 0; }}

        /* Evals */
        .evals-list {{ display: flex; flex-direction: column; gap: 12px; }}
        .eval-card {{
            padding: 16px 20px;
            background: var(--bg-code);
            border: 1px solid var(--border);
            border-radius: 8px;
        }}
        .eval-prompt {{
            color: var(--heading);
            font-weight: 500;
            margin-bottom: 8px;
            font-size: 14px;
        }}
        .eval-prompt::before {{
            content: "Prompt: ";
            color: var(--accent);
            font-weight: 600;
        }}
        .eval-expected {{
            color: var(--text-secondary);
            font-size: 13px;
            line-height: 1.5;
        }}
        .eval-expected::before {{
            content: "Expected: ";
            color: var(--text-muted);
            font-weight: 600;
        }}

        /* Empty state */
        .empty-state {{
            display: flex;
            align-items: center;
            justify-content: center;
            height: 60vh;
            color: var(--text-muted);
            font-size: 18px;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .hamburger {{ display: block; }}
            .sidebar {{
                position: fixed;
                left: -100%;
                top: 0;
                z-index: 999;
                transition: left 0.2s ease;
                box-shadow: 4px 0 24px rgba(0,0,0,0.3);
            }}
            .sidebar.open {{ left: 0; }}
            .sidebar-overlay.open {{ display: block; }}
            .main {{
                padding: 60px 20px 32px;
            }}
        }}
        @media (min-width: 769px) {{
            .hamburger {{ display: none !important; }}
        }}
    </style>
</head>
<body>
    <button class="hamburger" onclick="toggleSidebar()" aria-label="Toggle menu">&#9776;</button>
    <div class="sidebar-overlay" onclick="toggleSidebar()"></div>

    <div class="app">
        <nav class="sidebar">
            <div class="sidebar-header">
                <h2>Skills</h2>
            </div>
            <div class="sidebar-list">
                {sidebar_items}
            </div>
        </nav>
        <main class="main">
            {content_sections if skills else '<div class="empty-state">No skills found in skills/ directory</div>'}
        </main>
    </div>

    <script>
        function selectSkill(id, el) {{
            // Hide all content
            document.querySelectorAll('.skill-content').forEach(s => s.style.display = 'none');
            // Deactivate all sidebar items
            document.querySelectorAll('.sidebar-item').forEach(s => s.classList.remove('active'));
            // Show selected
            const target = document.getElementById('skill-' + id);
            if (target) target.style.display = 'block';
            if (el) el.classList.add('active');
            // Update hash
            history.replaceState(null, '', '#' + id);
            // Scroll main to top
            document.querySelector('.main').scrollTop = 0;
            // Close mobile sidebar
            document.querySelector('.sidebar').classList.remove('open');
            document.querySelector('.sidebar-overlay').classList.remove('open');
        }}

        function openSection(skillId, slug) {{
            const section = document.getElementById('section-' + skillId + '-' + slug);
            if (section) {{
                section.open = true;
                section.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }}
        }}

        function toggleGroup(el) {{
            el.closest('.sidebar-group').classList.toggle('open');
        }}

        function toggleSidebar() {{
            document.querySelector('.sidebar').classList.toggle('open');
            document.querySelector('.sidebar-overlay').classList.toggle('open');
        }}

        // Handle hash on load
        window.addEventListener('DOMContentLoaded', () => {{
            const hash = location.hash.slice(1);
            if (hash) {{
                const btn = document.querySelector(`.sidebar-item[data-skill="${{hash}}"]`);
                if (btn) selectSkill(hash, btn);
            }}
        }});
    </script>
</body>
</html>'''


def main():
    print("Building skills site...")

    # Clean dist
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    # Discover skills
    skills = discover_skills()
    print(f"Found {len(skills)} skill(s): {', '.join(s['name'] for s in skills)}")

    # Copy examples
    copy_examples(skills)

    # Generate HTML
    structure = build_sidebar_structure(skills)
    html = generate_html(skills, structure)
    index_path = DIST_DIR / "index.html"
    index_path.write_text(html, encoding="utf-8")

    print(f"Built: {index_path}")
    print(f"Open: file://{index_path}")


if __name__ == "__main__":
    main()
