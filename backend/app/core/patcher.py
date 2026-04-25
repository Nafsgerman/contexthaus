import re
from typing import Optional


def get_section(markdown: str, section_name: str) -> Optional[str]:
    pattern = rf"## {re.escape(section_name)}\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, markdown, re.DOTALL)
    return match.group(1).strip() if match else None


def patch_section(markdown: str, section_name: str, new_content: str) -> str:
    pattern = rf"(## {re.escape(section_name)}\n)(.*?)(?=\n## |\Z)"
    replacement = rf"\g<1>{new_content}\n"
    result = re.sub(pattern, replacement, markdown, flags=re.DOTALL)
    if result == markdown:
        result = markdown.rstrip() + f"\n\n## {section_name}\n{new_content}\n"
    return result


def diff_sections(old_md: str, new_md: str) -> list[dict]:
    changes = []
    section_pattern = r"## (.+?)\n(.*?)(?=\n## |\Z)"
    old_sections = {m.group(1): m.group(2).strip()
                    for m in re.finditer(section_pattern, old_md, re.DOTALL)}
    new_sections = {m.group(1): m.group(2).strip()
                    for m in re.finditer(section_pattern, new_md, re.DOTALL)}

    for section, content in new_sections.items():
        if section not in old_sections:
            changes.append({"section": section, "type": "added", "content": content})
        elif old_sections[section] != content:
            changes.append({"section": section, "type": "updated",
                           "old": old_sections[section], "new": content})
    return changes
