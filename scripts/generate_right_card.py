#!/usr/bin/env python3
"""
generate_right_card.py
------------------------
Generates the right-side "neofetch style" info terminal card as a static SVG.

FULLY DATA-DRIVEN: this script has no idea what "Stack" or "Projects" even
means - it just loops over whatever sections you define in config.json's
right_card.sections list. That means adding a brand new section (Projects,
Tools, Awards, anything) is a config.json-only change - you never need to
touch this file again to add/remove/reorder a section.

USAGE
    python3 generate_right_card.py
    python3 generate_right_card.py --config ../config.json --out ../assets/right_card.svg
"""

import argparse
import json
import os

CARD_W = 560
PADDING = 24
TITLEBAR_H = 40
LINE_H = 24
SECTION_GAP = 14

BG_COLOR = "#0d1117"
TITLEBAR_COLOR = "#161b22"
BORDER_COLOR = "#30363d"
TITLE_TEXT_COLOR = "#8b949e"
USER_COLOR = "#7ee787"
LABEL_COLOR = "#ffa657"
VALUE_COLOR = "#c9d1d9"
SECTION_HEADER_COLOR = "#79c0ff"
BULLET_COLOR = "#7ee787"
RULE_COLOR = "#30363d"
FONT_FAMILY = "SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace"
DOT_COLORS = ["#ff5f56", "#ffbd2e", "#27c93f"]


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def all_field_items(rc):
    """Collect every {label,...} dict across top_fields + every fields-type
    section, purely to compute a consistent label column width."""
    items = list(rc.get("top_fields", []))
    for section in rc.get("sections", []):
        if section.get("type") == "fields":
            items += section.get("items", [])
    return items


def build_svg(cfg: dict) -> str:
    rc = cfg["right_card"]
    field_items = all_field_items(rc)
    label_col_w = (max((len(f["label"]) for f in field_items), default=4) * 9) + 30

    lines = []
    lines.append(("user", cfg.get("footer", {}).get("name", "") or rc.get("user_line", "")))
    for f in rc.get("top_fields", []):
        lines.append(("field", f["label"], f["value"]))

    for section in rc.get("sections", []):
        lines.append(("rule",))
        lines.append(("header", section.get("header", "")))
        sec_type = section.get("type", "fields")
        for item in section.get("items", []):
            if sec_type == "bullets":
                lines.append(("bullet", item))
            else:
                lines.append(("field", item["label"], item["value"]))

    row_ys = []
    y = PADDING + 10
    for item in lines:
        row_ys.append(y)
        y += SECTION_GAP if item[0] == "rule" else LINE_H
    content_h = y + PADDING - 10
    card_h = TITLEBAR_H + content_h

    body = []
    for item, y in zip(lines, row_ys):
        ty = y + TITLEBAR_H
        if item[0] == "user":
            body.append(
                f'<text x="{PADDING}" y="{ty}" font-family="{FONT_FAMILY}" '
                f'font-size="15" font-weight="bold" fill="{USER_COLOR}">{esc(item[1])}</text>'
            )
        elif item[0] == "field":
            _, label, value = item
            body.append(
                f'<text x="{PADDING}" y="{ty}" font-family="{FONT_FAMILY}" font-size="13" '
                f'font-weight="bold" fill="{LABEL_COLOR}">{esc(label)}</text>'
                f'<text x="{PADDING + label_col_w}" y="{ty}" font-family="{FONT_FAMILY}" '
                f'font-size="13" fill="{VALUE_COLOR}">{esc(value)}</text>'
            )
        elif item[0] == "header":
            body.append(
                f'<text x="{PADDING}" y="{ty}" font-family="{FONT_FAMILY}" font-size="13" '
                f'font-weight="bold" fill="{SECTION_HEADER_COLOR}">\u2500 {esc(item[1])}</text>'
            )
        elif item[0] == "bullet":
            body.append(
                f'<text x="{PADDING}" y="{ty}" font-family="{FONT_FAMILY}" font-size="13" '
                f'fill="{BULLET_COLOR}">\u2022</text>'
                f'<text x="{PADDING + 18}" y="{ty}" font-family="{FONT_FAMILY}" font-size="13" '
                f'fill="{VALUE_COLOR}">{esc(item[1])}</text>'
            )
        elif item[0] == "rule":
            body.append(
                f'<line x1="{PADDING}" y1="{ty - 14}" x2="{CARD_W - PADDING}" y2="{ty - 14}" '
                f'stroke="{RULE_COLOR}" stroke-width="1"/>'
            )

    body_svg = "\n    ".join(body)
    title = rc["window_title"]

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{card_h}"
     viewBox="0 0 {CARD_W} {card_h}">
  <defs>
    <clipPath id="roundedCard2">
      <rect x="0" y="0" width="{CARD_W}" height="{card_h}" rx="12" ry="12"/>
    </clipPath>
  </defs>
  <g clip-path="url(#roundedCard2)">
    <rect x="0" y="0" width="{CARD_W}" height="{card_h}" fill="{BG_COLOR}"/>
    <rect x="0" y="0" width="{CARD_W}" height="{TITLEBAR_H}" fill="{TITLEBAR_COLOR}"/>
    <circle cx="22" cy="{TITLEBAR_H/2}" r="6" fill="{DOT_COLORS[0]}"/>
    <circle cx="42" cy="{TITLEBAR_H/2}" r="6" fill="{DOT_COLORS[1]}"/>
    <circle cx="62" cy="{TITLEBAR_H/2}" r="6" fill="{DOT_COLORS[2]}"/>
    <text x="{CARD_W/2}" y="{TITLEBAR_H/2 + 4}" text-anchor="middle"
          font-family="{FONT_FAMILY}" font-size="12" fill="{TITLE_TEXT_COLOR}">{esc(title)}</text>

    {body_svg}

    <rect x="0.5" y="0.5" width="{CARD_W-1}" height="{card_h-1}" rx="12" ry="12"
          fill="none" stroke="{BORDER_COLOR}" stroke-width="1"/>
  </g>
</svg>'''
    return svg


def main():
    parser = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument("--config", default=os.path.join(here, "..", "config.json"))
    parser.add_argument("--out", default=os.path.join(here, "..", "assets", "right_card.svg"))
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)

    svg = build_svg(cfg)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()