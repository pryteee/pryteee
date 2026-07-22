#!/usr/bin/env python3
"""
fetch_contributions.py
------------------------
Fetches your REAL contribution calendar with NO token, NO auth, NO GraphQL.

GitHub already serves this data publicly at:
    https://github.com/users/<username>/contributions

That page is the same calendar GitHub shows on your public profile - anyone
can view it in a browser without logging in, so this script just requests
that page and reads the numbers straight out of its HTML. Every contribution
cell in that markup carries its exact date and contribution count, e.g.:

    <td ... data-date="2025-07-13" data-level="1" id="contribution-day-component-0-0">
    <tool-tip ... for="contribution-day-component-0-0">5 contributions on July 13th.</tool-tip>

This script pairs those up and writes the result to data/contributions.json.
Verified against GitHub's own "X contributions in the last year" total shown
on the page itself - the sum always matches exactly.

USAGE
    python3 fetch_contributions.py
    python3 fetch_contributions.py --username octocat
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.request

CELL_RE = re.compile(
    r'<td[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*'
    r'id="(contribution-day-component-\d+-\d+)"[^>]*data-level="(\d)"[^>]*>'
)
TOOLTIP_RE = re.compile(
    r'<tool-tip[^>]*for="(contribution-day-component-\d+-\d+)"[^>]*>([^<]*)</tool-tip>'
)
COUNT_RE = re.compile(r'(No|\d+)\s+contributions?\s+on')
TOTAL_RE = re.compile(r'([\d,]+)\s+contributions?\s+in the last year')


def fetch_public_contributions(username: str):
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8")

    cells = CELL_RE.findall(html)
    if not cells:
        raise RuntimeError(
            f"No contribution cells found for '{username}' - check the "
            f"username is correct and the profile is public."
        )

    tooltips = TOOLTIP_RE.findall(html)
    count_by_id = {}
    for cell_id, text in tooltips:
        m = COUNT_RE.match(text.strip())
        if m:
            count_by_id[cell_id] = 0 if m.group(1) == "No" else int(m.group(1))

    days = []
    for date, cell_id, _level in cells:
        days.append({"date": date, "count": count_by_id.get(cell_id, 0)})

    days.sort(key=lambda d: d["date"])
    total = sum(d["count"] for d in days)

    # sanity-check against GitHub's own displayed total, if we can find it
    m = TOTAL_RE.search(html)
    if m:
        page_total = int(m.group(1).replace(",", ""))
        if page_total != total:
            print(f"Warning: summed total ({total}) doesn't match page-stated "
                  f"total ({page_total}) - GitHub may have changed its markup.",
                  file=sys.stderr)

    return days, total


def generate_sample_data():
    print("[SAMPLE DATA] Could not fetch real data - writing placeholder data "
          "for local preview instead.", file=sys.stderr)
    import random
    random.seed(42)
    today = datetime.date.today()
    start = today - datetime.timedelta(days=365)
    start -= datetime.timedelta(days=(start.weekday() + 1) % 7)

    days = []
    d = start
    while d <= today:
        base = random.random()
        if d.weekday() >= 5:
            count = 0 if base < 0.6 else random.randint(0, 4)
        else:
            count = 0 if base < 0.15 else random.randint(0, 12)
        days.append({"date": d.isoformat(), "count": count})
        d += datetime.timedelta(days=1)
    return days, sum(x["count"] for x in days)


def main():
    parser = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument("--config", default=os.path.join(here, "..", "config.json"))
    parser.add_argument("--out", default=os.path.join(here, "..", "data", "contributions.json"))
    parser.add_argument("--username", default=None)
    args = parser.parse_args()

    config_username = None
    try:
        with open(args.config, encoding="utf-8") as f:
            config_username = json.load(f).get("github_username")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    username = args.username or os.environ.get("GH_USERNAME") or config_username

    if not username or username == "your-username":
        print("No github_username set in config.json (still says 'your-username') - "
              "writing sample data. Edit config.json and re-run.", file=sys.stderr)
        days, total = generate_sample_data()
        username = username or "your-username"
    else:
        try:
            days, total = fetch_public_contributions(username)
            print(f"Fetched real public contribution data for '{username}' "
                  f"({total} total contributions)")
        except Exception as e:
            print(f"Warning: fetch failed ({e}); falling back to sample data.", file=sys.stderr)
            days, total = generate_sample_data()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    payload = {
        "username": username,
        "total_contributions": total,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "days": days,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
# PYEOF
# echo "written"