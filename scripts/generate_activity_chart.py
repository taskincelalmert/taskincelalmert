#!/usr/bin/env python3
# /// script
# dependencies = ["fonttools"]
# ///
"""Generate assets/activity-{light,dark}.svg from the public GitHub contribution calendar (no token required)."""
import datetime
import html
import json
import re
import sys
import urllib.error
import urllib.request

from render import WIDTH, label, text, write

USERNAME = "taskincelalmert"

HEIGHT, COL_W = 234, 280
WEEKS, BARS_Y, BARS_H, BAR_GAP = 52, 136, 48, 4

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
    return f"{parsed:%b} {parsed.day}" + (f", {parsed.year}" if with_year else "")


def span(start, end):
    return fmt(start, False) if start == end else f"{fmt(start, False)} to {fmt(end, False)}"


def stat(col, number, caption, dates, theme):
    x = col * COL_W
    return [
        text(x - 1, 64, str(number), 40, theme["text"], "Light", -0.4),
        text(x, 88, caption, 15, theme["text"]),
        text(x, 108, dates, 13, theme["muted"]),
    ]


def render(days, theme):
    current, longest = streaks(days)
    total = sum(days.values())
    first_day = min(d for d, c in days.items() if c) if total else min(days)

    parts = [label(0, 14, "ACTIVITY", theme)]
    parts += stat(0, f"{total:,}", "Contributions", f"since {fmt(first_day)}", theme)
    parts += stat(1, current[0], "Day current streak", span(current[1], current[2]), theme)
    parts += stat(2, longest[0], "Day longest streak", span(longest[1], longest[2]), theme)

    # One bar per week, oldest first; the running week takes the accent.
    counts = [days[d] for d in sorted(days)][-WEEKS * 7:]
    weeks = [sum(counts[i:i + 7]) for i in range(0, len(counts), 7)]
    peak = max(weeks) or 1
    bar_w = (WIDTH - BAR_GAP * (len(weeks) - 1)) / len(weeks)
    for i, count in enumerate(weeks):
        h = max(2, count / peak * BARS_H)
        last = i == len(weeks) - 1
        parts.append(
            f'<rect x="{i * (bar_w + BAR_GAP):.1f}" y="{BARS_Y + BARS_H - h:.1f}" width="{bar_w:.1f}" '
            f'height="{h:.1f}" rx="2" fill="{theme["accent"] if last else theme["text"]}" '
            f'fill-opacity="{1 if last else 0.3}"/>'
        )
    parts.append(text(0, BARS_Y + BARS_H + 22, f"Contributions per week, last {len(weeks)} weeks",
                      13, theme["muted"]))
    return parts, HEIGHT


def main():
    days = fetch_days()
    write("activity", "Contribution activity", lambda theme: render(days, theme))
    current, longest = streaks(days)
    print(f"wrote activity-light.svg, activity-dark.svg: {sum(days.values())} total, "
          f"{current[0]} day current streak, {longest[0]} day longest streak")


if __name__ == "__main__":
    main()
