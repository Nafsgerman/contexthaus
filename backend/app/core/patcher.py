import re
from typing import Optional


def _find_section_header(markdown: str, section_name: str) -> Optional[str]:
    """Return the exact header text in the document that matches section_name case-insensitively."""
    for m in re.finditer(r"## (.+)", markdown):
        if m.group(1).strip().lower() == section_name.strip().lower():
            return m.group(1).strip()
    return None


def deduplicate_sections(markdown: str) -> str:
    """Remove earlier duplicate ## sections, keeping the last occurrence of each."""
    section_pattern = r"(## .+?\n.*?)(?=\n## |\Z)"
    matches = list(re.finditer(section_pattern, markdown, re.DOTALL))
    if not matches:
        return markdown

    # Build map of lowercase name -> last match index
    seen: dict[str, int] = {}
    for i, m in enumerate(matches):
        header = re.match(r"## (.+)", m.group(0))
        if header:
            seen[header.group(1).strip().lower()] = i

    # Collect preamble (text before the first section)
    preamble = markdown[: matches[0].start()]

    kept_parts = []
    for i, m in enumerate(matches):
        header = re.match(r"## (.+)", m.group(0))
        if header and seen.get(header.group(1).strip().lower()) == i:
            kept_parts.append(m.group(0).rstrip())

    return preamble + "\n\n".join(kept_parts) + "\n"


def get_section(markdown: str, section_name: str) -> Optional[str]:
    canonical = _find_section_header(markdown, section_name) or section_name
    pattern = rf"## {re.escape(canonical)}\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, markdown, re.DOTALL)
    return match.group(1).strip() if match else None


def patch_section(markdown: str, section_name: str, new_content: str) -> str:
    canonical = _find_section_header(markdown, section_name) or section_name
    pattern = rf"(## {re.escape(canonical)}\n)(.*?)(?=\n## |\Z)"
    replacement = rf"\g<1>{new_content}\n"
    result = re.sub(pattern, replacement, markdown, flags=re.DOTALL)
    if result == markdown:
        result = markdown.rstrip() + f"\n\n## {section_name}\n{new_content}\n"
    return deduplicate_sections(result)


def diff_sections(old_md: str, new_md: str) -> list[dict]:
    changes = []
    section_pattern = r"## (.+?)\n(.*?)(?=\n## |\Z)"
    old_sections = {m.group(1).strip().lower(): (m.group(1).strip(), m.group(2).strip())
                    for m in re.finditer(section_pattern, old_md, re.DOTALL)}
    new_sections = {m.group(1).strip().lower(): (m.group(1).strip(), m.group(2).strip())
                    for m in re.finditer(section_pattern, new_md, re.DOTALL)}

    for key, (section, content) in new_sections.items():
        if key not in old_sections:
            changes.append({"section": section, "type": "added", "content": content})
        elif old_sections[key][1] != content:
            changes.append({"section": section, "type": "updated",
                           "old": old_sections[key][1], "new": content})
    return changes
