#!/usr/bin/env python3
"""Generate assets/activity.svg from the public GitHub contribution calendar (no token required)."""
import datetime
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request

USERNAME = "taskincelalmert"
OUTPUT = os.path.join(os.path.dirname(__file__), "..", "assets", "activity.svg")

BG, ACCENT, TEXT_COLOR, DATE_COLOR, LINE_COLOR = "#0d1117", "#A855F7", "#c9d1d9", "#6e7681", "#21262d"

DAY_RE = re.compile(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*id="(contribution-day-component-[\d-]+)"')
TOOLTIP_RE = re.compile(r'<tool-tip[^>]*for="(contribution-day-component-[\d-]+)"[^>]*>([^<]*)</tool-tip>')
COUNT_RE = re.compile(r"^([\d,]+) contribution")


def fetch_year(year):
    """Return {date: count} for one calendar year of the user's contribution graph."""
    url = (f"https://github.com/users/{USERNAME}/contributions"
           f"?from={year}-01-01&to={year}-12-31")
    req = urllib.request.Request(url, headers={"User-Agent": f"{USERNAME}-readme-chart"})
    with urllib.request.urlopen(req) as resp:
        page = resp.read().decode("utf-8")

    ids = {cell_id: date for date, cell_id in DAY_RE.findall(page)}
    days = {}
    for cell_id, label in TOOLTIP_RE.findall(page):
        if cell_id not in ids:
            continue
        match = COUNT_RE.match(html.unescape(label).strip())
        days[ids[cell_id]] = int(match.group(1).replace(",", "")) if match else 0
    return days


def fetch_days():
    """Collect every day from the account's first contribution year through today."""
    today = datetime.date.today()
    start_year = today.year
    try:
        req = urllib.request.Request(f"https://api.github.com/users/{USERNAME}",
                                     headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req) as resp:
            start_year = int(json.load(resp)["created_at"][:4])
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, ValueError) as e:
        print(f"warning: could not read account creation year ({e}), using current year", file=sys.stderr)

    days = {}
    for year in range(start_year, today.year + 1):
        days.update({d: c for d, c in fetch_year(year).items() if d <= today.isoformat()})
    if not days:
        sys.exit("error: no contribution data found")
    return days


def streaks(days):
    """Return (current, longest) streaks as (length, first_date, last_date)."""
    dates = sorted(days)
    empty = (0, dates[-1], dates[-1])

    longest, run_start = empty, None
    for i, date in enumerate(dates):
        if not days[date]:
            run_start = None
            continue
        run_start = i if run_start is None else run_start
        if i - run_start + 1 > longest[0]:
            longest = (i - run_start + 1, dates[run_start], date)

    # Today with no contributions yet does not break the streak.
    end = len(dates) - 1
    if not days[dates[end]]:
        end -= 1
    start = end
    while start >= 0 and days[dates[start]]:
        start -= 1
    current = (end - start, dates[start + 1], dates[end]) if end > start else empty
    return current, longest


def fmt(date, with_year=True):
    parsed = datetime.date.fromisoformat(date)
    return parsed.strftime("%b %-d, %Y") if with_year else parsed.strftime("%b %-d")


def span(start, end):
    return fmt(start, False) if start == end else f"{fmt(start, False)} - {fmt(end, False)}"


def panel(cx, number, label, dates, ring=False):
    parts = []
    if ring:
        parts.append(f'<circle cx="{cx}" cy="66" r="38" fill="none" stroke="{ACCENT}" stroke-width="4"/>')
    parts += [
        f'<text x="{cx}" y="78" text-anchor="middle" font-family="\'Segoe UI\', Ubuntu, Sans-Serif" '
        f'font-size="34" font-weight="700" fill="{TEXT_COLOR}">{number}</text>',
        f'<text x="{cx}" y="128" text-anchor="middle" font-family="\'Segoe UI\', Ubuntu, Sans-Serif" '
        f'font-size="14" font-weight="600" fill="{ACCENT}">{label}</text>',
        f'<text x="{cx}" y="150" text-anchor="middle" font-family="\'Segoe UI\', Ubuntu, Sans-Serif" '
        f'font-size="12" fill="{DATE_COLOR}">{dates}</text>',
    ]
    return parts


def main():
    days = fetch_days()
    current, longest = streaks(days)
    total = sum(days.values())
    first_day = min(d for d, c in days.items() if c) if total else min(days)

    width, height = 495, 180
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" fill="none" role="img" aria-label="Contribution activity">',
        f'<rect width="{width}" height="{height}" rx="4.5" fill="{BG}"/>',
        f'<line x1="165" y1="26" x2="165" y2="154" stroke="{LINE_COLOR}" stroke-width="1"/>',
        f'<line x1="330" y1="26" x2="330" y2="154" stroke="{LINE_COLOR}" stroke-width="1"/>',
    ]
    parts += panel(82.5, total, "Total Contributions", f"{fmt(first_day)} - Present")
    parts += panel(247.5, current[0], "Current Streak", span(current[1], current[2]), ring=True)
    parts += panel(412.5, longest[0], "Longest Streak", span(longest[1], longest[2]))
    parts.append("</svg>")

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w") as f:
        f.write("\n".join(parts) + "\n")
    print(f"wrote {os.path.normpath(OUTPUT)}: {total} total, "
          f"{current[0]} day current streak, {longest[0]} day longest streak")


if __name__ == "__main__":
    main()
