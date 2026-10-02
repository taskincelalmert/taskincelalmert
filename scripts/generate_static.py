#!/usr/bin/env python3
# /// script
# dependencies = ["fonttools"]
# ///
"""Generate the hand-written README graphics: assets/{header,projects,contact}-{light,dark}.svg."""
from render import WIDTH, icon, label, text, write

NAME = "Celal Mert Taşkın"
ROLE = "Software engineer"
SUMMARY = "Full stack, mobile and desktop systems with TypeScript, Flutter and .NET"
META = ["izmir, tr", "since 2023"]

# (name, description, tech, private, site)
PROJECTS = [
    ("ChefSpecials", "Mobile app for restaurant specials", "Flutter  ·  Dart  ·  Swift  ·  Kotlin", False, ""),
    ("DetaApartProject", "Full stack apartment management system", "C#  ·  .NET  ·  TypeScript  ·  Docker", True, ""),
    ("Axon-Jira", "Project management tool", "Next.js  ·  Firebase  ·  TypeScript", True, "axonjira.com"),
]

LINKEDIN = "linkedin.com/in/celal-mert-taskin"


def header(theme):
    parts = [
        text(-2, 62, NAME, 52, theme["text"], "Light", -0.6),
        text(0, 100, ROLE, 18, theme["text"]),
        text(0, 125, SUMMARY, 15, theme["muted"]),
        f'<rect x="0" y="155" width="{WIDTH}" height="1" fill="{theme["rule"]}"/>',
        f'<rect x="0" y="153" width="72" height="3" fill="{theme["accent"]}"/>',
    ]
    parts += [label(WIDTH, 36 + i * 20, line, theme, "end") for i, line in enumerate(META)]
    return parts, 168


def project(index, theme):
    """One project per image so each row can carry its own link; the first holds the section label."""
    name, description, tech, private, site = PROJECTS[index]
    first, last = index == 0, index == len(PROJECTS) - 1
    y = 50 if first else 16
    parts = [label(0, 14, "PROJECTS", theme)] if first else []
    parts.append(text(0, y, name, 16, theme["text"], "Medium"))
    if private:
        parts.append(label(0, y + 21, "PRIVATE", theme))
    if site:
        parts.append(text(WIDTH, y, site, 15, theme["accent"], anchor="end"))
    parts.append(text(230, y, description, 15, theme["text"]))
    parts.append(text(230, y + 22, tech, 13, theme["muted"]))
    return parts, y + (60 if last else 36)


def contact(theme):
    return [
        label(0, 14, "CONTACT", theme),
        icon(0, 48, "LinkedIn", theme["text"]),
        text(28, 48, LINKEDIN, 15, theme["text"]),
    ], 64


if __name__ == "__main__":
    write("header", f"{NAME}. {ROLE}. {SUMMARY}.", header)
    for i, (name, *_) in enumerate(PROJECTS):
        write(f"project-{i + 1}", name, lambda theme: project(i, theme))
    write("contact", "Contact", contact)
    print("wrote header, projects and contact graphics")
