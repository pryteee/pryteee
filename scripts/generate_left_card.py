#!/usr/bin/env python3
"""
generate_left_card.py
----------------------
Wraps your existing ASCII portrait GIF (assets/ascii.gif) inside a macOS-style
terminal window frame, and outputs a single SVG: assets/left_card.svg

Why SVG-wrapping instead of just embedding the raw GIF in the README:
GitHub's markdown renderer strips most inline CSS/HTML styling for security,
so a hand-styled "terminal window" made of <div>/<style> tags won't render
on your profile page. SVG sidesteps this completely: the whole card (border,
macOS buttons, header/footer text, AND your embedded gif) becomes ONE static
image asset that GitHub just displays as-is - identical to how the reference
profile does it.

The gif is embedded as a base64 data URI directly inside the SVG XML (not a
relative file path) so it keeps animating correctly no matter how GitHub's
image proxy (camo) serves the file.

USAGE
    python3 generate_left_card.py
    python3 generate_left_card.py --gif ../assets/ascii.gif --config ../config.json

Requires: pip install pillow --break-system-packages
"""

import argparse
import base64
import json
import os
from PIL import Image

# ---- visual constants (tweak to taste) ----
PADDING = 24
TITLEBAR_H = 40
FOOTER_H = 44
BORDER_RADIUS = 12
BG_COLOR = "#0d1117"
TITLEBAR_COLOR = "#161b22"
BORDER_COLOR = "#30363d"
TITLE_TEXT_COLOR = "#8b949e"
FOOTER_PROMPT_COLOR = "#8b949e"
FOOTER_NAME_COLOR = "#ffffff"
FONT_FAMILY = "SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace"
DOT_COLORS = ["#ff5f56", "#ffbd2e", "#27c93f"]  # red, yellow, green


def build_svg(gif_path: str, cfg: dict) -> str:
    with open(gif_path, "rb") as f:
        gif_bytes = f.read()
    b64 = base64.b64encode(gif_bytes).decode("ascii")

    im = Image.open(gif_path)
    gif_w, gif_h = im.size

    # scale the gif down to a sane display width if it's huge
    max_display_w = 440
    scale = min(1.0, max_display_w / gif_w)
    disp_w = int(gif_w * scale)
    disp_h = int(gif_h * scale)

    card_w = disp_w + PADDING * 2
    card_h = TITLEBAR_H + disp_h + FOOTER_H

    title = cfg["left_card"]["window_title"]
    footer_prompt = cfg["left_card"]["footer_prompt"]
    footer_name = cfg["left_card"]["footer_name"]

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{card_w}" height="{card_h}"
     viewBox="0 0 {card_w} {card_h}">
  <defs>
    <clipPath id="roundedCard">
      <rect x="0" y="0" width="{card_w}" height="{card_h}" rx="{BORDER_RADIUS}" ry="{BORDER_RADIUS}"/>
    </clipPath>
  </defs>

  <g clip-path="url(#roundedCard)">
    <rect x="0" y="0" width="{card_w}" height="{card_h}" fill="{BG_COLOR}"/>

    <!-- title bar -->
    <rect x="0" y="0" width="{card_w}" height="{TITLEBAR_H}" fill="{TITLEBAR_COLOR}"/>
    <circle cx="22" cy="{TITLEBAR_H/2}" r="6" fill="{DOT_COLORS[0]}"/>
    <circle cx="42" cy="{TITLEBAR_H/2}" r="6" fill="{DOT_COLORS[1]}"/>
    <circle cx="62" cy="{TITLEBAR_H/2}" r="6" fill="{DOT_COLORS[2]}"/>
    <text x="{card_w/2}" y="{TITLEBAR_H/2 + 4}" text-anchor="middle"
          font-family="{FONT_FAMILY}" font-size="12" fill="{TITLE_TEXT_COLOR}">{title}</text>

    <!-- ascii gif -->
    <image x="{PADDING}" y="{TITLEBAR_H}" width="{disp_w}" height="{disp_h}"
           href="data:image/gif;base64,{b64}" preserveAspectRatio="xMidYMid meet"/>

    <!-- footer -->
    <rect x="0" y="{TITLEBAR_H + disp_h}" width="{card_w}" height="{FOOTER_H}" fill="{TITLEBAR_COLOR}"/>
    <text x="{PADDING}" y="{TITLEBAR_H + disp_h + FOOTER_H/2 + 4}"
          font-family="{FONT_FAMILY}" font-size="12" fill="{FOOTER_PROMPT_COLOR}">{footer_prompt} <tspan fill="{FOOTER_NAME_COLOR}" font-weight="bold">{footer_name}</tspan></text>

    <!-- border -->
    <rect x="0.5" y="0.5" width="{card_w-1}" height="{card_h-1}" rx="{BORDER_RADIUS}" ry="{BORDER_RADIUS}"
          fill="none" stroke="{BORDER_COLOR}" stroke-width="1"/>
  </g>
</svg>'''
    return svg


def main():
    parser = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument("--gif", default=os.path.join(here, "..", "assets", "ascii.gif"))
    parser.add_argument("--config", default=os.path.join(here, "..", "config.json"))
    parser.add_argument("--out", default=os.path.join(here, "..", "assets", "left_card.svg"))
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)

    svg = build_svg(args.gif, cfg)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
