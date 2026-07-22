#!/usr/bin/env python3
"""
generate_heatmap.py
---------------------
Pure renderer: reads data/contributions.json (written by fetch_contributions.py)
and draws assets/heatmap.svg. Touches NO token, makes NO network calls -
that's entirely fetch_contributions.py's job. This split means you can
re-style the heatmap (colors, spacing, layout) and re-run this script freely
without needing a token on hand or re-hitting the GitHub API every time.

USAGE
    python3 fetch_contributions.py   # run this first, at least once
    python3 generate_heatmap.py
"""

import argparse
import datetime
import json
import os

LEVEL_COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level_for_count(count, thresholds=(0, 2, 5, 9)):
    if count <= thresholds[0]:
        return 0
    if count <= thresholds[1]:
        return 1
    if count <= thresholds[2]:
        return 2
    if count <= thresholds[3]:
        return 3
    return 4


def compute_streaks(days):
    longest = current = 0
    best_run = 0
    for d in days:
        if d["count"] > 0:
            current += 1
            best_run = max(best_run, current)
        else:
            current = 0
    longest = best_run

    streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            streak += 1
        else:
            break
    return streak, longest


def build_svg(days, total, username):
    days_sorted = sorted(days, key=lambda x: x["date"])
    start_date = datetime.date.fromisoformat(days_sorted[0]["date"])
    start_date -= datetime.timedelta(days=(start_date.weekday() + 1) % 7)

    cell = 11
    gap = 3
    left_margin = 40
    top_margin = 34
    n_weeks = -(-((datetime.date.fromisoformat(days_sorted[-1]["date"]) - start_date).days + 1) // 7)

    grid_w = n_weeks * (cell + gap)
    grid_h = 7 * (cell + gap)
    card_w = left_margin + grid_w + 40
    legend_h = 24
    stats_h = 46
    titlebar_h = 34
    card_h = titlebar_h + top_margin + grid_h + legend_h + stats_h

    count_by_date = {d["date"]: d["count"] for d in days_sorted}

    cells_svg = []
    month_labels = []
    last_month = None
    d = start_date
    col = 0
    while d <= datetime.date.fromisoformat(days_sorted[-1]["date"]):
        row = d.weekday()
        row = (row + 1) % 7
        x = left_margin + col * (cell + gap)
        y = titlebar_h + top_margin + row * (cell + gap)

        if d.day <= 7 and d.month != last_month:
            month_labels.append((x, titlebar_h + top_margin - 12, MONTH_NAMES[d.month - 1]))
            last_month = d.month

        count = count_by_date.get(d.isoformat(), 0)
        level = level_for_count(count)
        color = LEVEL_COLORS[level]
        cells_svg.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" ry="2" fill="{color}">'
            f'<title>{d.isoformat()}: {count} contributions</title></rect>'
        )

        if row == 6:
            col += 1
        d += datetime.timedelta(days=1)

    day_labels = []
    for label, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        ly = titlebar_h + top_margin + row * (cell + gap) + cell - 2
        day_labels.append(
            f'<text x="{left_margin - 10}" y="{ly}" text-anchor="end" '
            f'font-family="SFMono-Regular, Consolas, monospace" font-size="10" fill="#8b949e">{label}</text>'
        )

    current_streak, longest_streak = compute_streaks(days_sorted)
    best_day = max(days_sorted, key=lambda x: x["count"])
    from_str = days_sorted[0]["date"]
    to_str = days_sorted[-1]["date"]

    legend_x = left_margin + grid_w - (5 * (cell + gap)) - 40
    legend_y = titlebar_h + top_margin + grid_h + 16
    legend_swatches = "".join(
        f'<rect x="{legend_x + 34 + i*(cell+gap)}" y="{legend_y - 9}" width="{cell}" height="{cell}" '
        f'rx="2" ry="2" fill="{LEVEL_COLORS[i]}"/>'
        for i in range(5)
    )

    stats_y1 = titlebar_h + top_margin + grid_h + legend_h + 20
    stats_y2 = stats_y1 + 22

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{card_w}" height="{card_h}"
     viewBox="0 0 {card_w} {card_h}">
  <defs>
    <clipPath id="roundedCard3">
      <rect x="0" y="0" width="{card_w}" height="{card_h}" rx="12" ry="12"/>
    </clipPath>
  </defs>
  <g clip-path="url(#roundedCard3)">
    <rect x="0" y="0" width="{card_w}" height="{card_h}" fill="#0d1117"/>
    <rect x="0" y="0" width="{card_w}" height="{titlebar_h}" fill="#161b22"/>
    <circle cx="20" cy="{titlebar_h/2}" r="5.5" fill="#ff5f56"/>
    <circle cx="38" cy="{titlebar_h/2}" r="5.5" fill="#ffbd2e"/>
    <circle cx="56" cy="{titlebar_h/2}" r="5.5" fill="#27c93f"/>
    <text x="{card_w/2}" y="{titlebar_h/2 + 4}" text-anchor="middle"
          font-family="SFMono-Regular, Consolas, monospace" font-size="12" fill="#8b949e">{username}: ~/contributions --graph</text>

    {''.join(f'<text x="{x}" y="{y}" font-family="SFMono-Regular, Consolas, monospace" font-size="10" fill="#8b949e">{m}</text>' for x, y, m in month_labels)}
    {''.join(day_labels)}
    {''.join(cells_svg)}

    <text x="{legend_x}" y="{legend_y}" font-family="SFMono-Regular, Consolas, monospace" font-size="10" fill="#8b949e">Less</text>
    {legend_swatches}
    <text x="{legend_x + 34 + 5*(cell+gap) + 6}" y="{legend_y}" font-family="SFMono-Regular, Consolas, monospace" font-size="10" fill="#8b949e">More</text>

    <line x1="0" y1="{titlebar_h + top_margin + grid_h + legend_h + 2}" x2="{card_w}" y2="{titlebar_h + top_margin + grid_h + legend_h + 2}" stroke="#21262d" stroke-width="1"/>

    <text x="{left_margin}" y="{stats_y1}" font-family="SFMono-Regular, Consolas, monospace" font-size="13" fill="#e6edf3">
      <tspan fill="#39d353" font-weight="bold">{total:,}</tspan> contributions in the last year
    </text>

    <!-- commented out per request - date range text. uncomment to restore:
    <text x="{card_w - 40}" y="{stats_y1}" text-anchor="end" font-family="SFMono-Regular, Consolas, monospace" font-size="12" fill="#8b949e">{from_str} \u2192 {to_str}</text>
    -->

    <!-- commented out per request - streak line. uncomment to restore:
    <text x="{left_margin}" y="{stats_y2}" font-family="SFMono-Regular, Consolas, monospace" font-size="13" fill="#e6edf3">
      current streak <tspan fill="#39d353" font-weight="bold">{current_streak} days</tspan> \u00b7 longest <tspan fill="#79c0ff" font-weight="bold">{longest_streak} days</tspan>
    </text>
    -->

    <!-- commented out per request - best day text. uncomment to restore:
    <text x="{card_w - 40}" y="{stats_y2}" text-anchor="end" font-family="SFMono-Regular, Consolas, monospace" font-size="12" fill="#8b949e">best day <tspan fill="#ffa657" font-weight="bold">{best_day['count']}</tspan> on {best_day['date']}</text>
    -->

    <rect x="0.5" y="0.5" width="{card_w-1}" height="{card_h-1}" rx="12" ry="12" fill="none" stroke="#30363d" stroke-width="1"/>
  </g>
</svg>'''
    return svg


def main():
    parser = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument("--data", default=os.path.join(here, "..", "data", "contributions.json"))
    parser.add_argument("--out", default=os.path.join(here, "..", "assets", "heatmap.svg"))
    args = parser.parse_args()

    if not os.path.exists(args.data):
        raise SystemExit(
            f"No data file found at {args.data}.\n"
            f"Run fetch_contributions.py first to create it."
        )

    with open(args.data, encoding="utf-8") as f:
        payload = json.load(f)

    svg = build_svg(payload["days"], payload["total_contributions"], payload["username"])
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()