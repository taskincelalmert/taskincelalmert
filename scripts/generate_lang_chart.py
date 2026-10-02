#!/usr/bin/env python3
# /// script
# dependencies = ["fonttools"]
# ///
"""Generate assets/stack-{light,dark}.svg from GitHub language stats (private repos included when the token allows)."""
import json
import os
import sys
import urllib.error
import urllib.request

from render import WIDTH, icon, label, measure, text, write

USERNAME = "taskincelalmert"
LANGS_COUNT = 8

SECTIONS = [
    ("LANGUAGES", ["Java", "C#", "Dart", "Python", "C++", "TypeScript", "JavaScript", "HTML", "CSS", "Swift",
                   "Kotlin", "Ruby"]),
    ("FRAMEWORKS", ["Flutter", "React", ".NET", "Next.js", "Vite"]),
    ("TOOLS", ["Docker", "Firebase", "Git", "IntelliJ IDEA", "VS Code"]),
]

# The top language takes the accent; the rest fade out in the text color.
OPACITIES = [1, 0.72, 0.56, 0.43, 0.33, 0.25, 0.19, 0.14]

BAR_Y, BAR_H, GAP = 32, 8, 3
COLS, COL_W, ROW_H = 5, 168, 30


def api_get(path, token):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def fetch_repos(token):
    # /user/repos sees private repos with a PAT; the Actions GITHUB_TOKEN
    # cannot use /user endpoints, so fall back to public repos only.
    for base in (f"/user/repos?affiliation=owner&per_page=100&page=",
                 f"/users/{USERNAME}/repos?type=owner&per_page=100&page="):
        try:
            repos, page = [], 1
            while True:
                batch = api_get(base + str(page), token)
                repos.extend(batch)
                if len(batch) < 100:
                    return repos
                page += 1
        except urllib.error.HTTPError as e:
            print(f"warning: {base} failed ({e.code}), trying fallback", file=sys.stderr)
    sys.exit("error: could not list repositories")


def item(i, y, name, theme, color=None, note=""):
    """One icon + name cell of the grid; `y` is the text baseline of the grid's first row."""
    x, y = (i % COLS) * COL_W, y + (i // COLS) * ROW_H
    parts = [icon(x, y, name, color or theme["text"]), text(x + 28, y, name, 15, theme["text"])]
    if note:
        parts.append(text(x + 36 + measure(name, 15), y, note, 13, theme["muted"]))
    return "".join(parts)


def render(langs, theme):
    parts = [label(0, 14, "MOST USED LANGUAGES", theme)]

    fills = [(theme["accent"], 1)] + [(theme["text"], o) for o in OPACITIES[1:]]
    usable = WIDTH - GAP * (len(langs) - 1)
    x = 0.0
    for (_, pct), (color, opacity) in zip(langs, fills):
        w = pct / 100 * usable
        parts.append(f'<rect x="{x:.1f}" y="{BAR_Y}" width="{w:.1f}" height="{BAR_H}" rx="2" '
                     f'fill="{color}" fill-opacity="{opacity}"/>')
        x += w + GAP

    y = 74
    for i, (name, pct) in enumerate(langs):
        parts.append(item(i, y, name, theme, theme["accent"] if i == 0 else None, f"{pct:.1f}%"))
    y += -(-len(langs) // COLS) * ROW_H

    for title, names in SECTIONS:
        y += 18
        parts.append(label(0, y, title, theme))
        y += 32
        for i, name in enumerate(names):
            parts.append(item(i, y, name, theme))
        y += -(-len(names) // COLS) * ROW_H

    return parts, y + 10


def main():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    totals = {}
    for repo in fetch_repos(token):
        if repo["fork"]:
            continue
        for lang, size in api_get(f"/repos/{repo['full_name']}/languages", token).items():
            totals[lang] = totals.get(lang, 0) + size

    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:LANGS_COUNT]
    total = sum(size for _, size in top)
    langs = [(name, size / total * 100) for name, size in top]

    write("stack", "Languages, frameworks and tools", lambda theme: render(langs, theme))
    print("wrote stack-light.svg, stack-dark.svg: " + ", ".join(f"{n} {p:.1f}%" for n, p in langs))


if __name__ == "__main__":
    main()
