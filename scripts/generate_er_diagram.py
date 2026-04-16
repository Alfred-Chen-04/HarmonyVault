"""
generate_er_diagram.py — Generates HarmonyVault ER diagram as a PNG.

Usage:
    pip install matplotlib
    python scripts/generate_er_diagram.py

Output: docs/ER_diagram.png
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


# ---------------------------------------------------------------------------
# Layout constants (all in axes units on a 24×18 canvas)
# ---------------------------------------------------------------------------

FIG_W, FIG_H = 24, 18

# Strong entities: (label, cx, cy, w, h)
STRONG_ENTITIES = [
    ("Users",    12,  15.5, 2.6, 0.9),
    ("Clips",    7,   10.5, 2.6, 0.9),
    ("Projects", 17,  10.5, 2.6, 0.9),
    ("Tags",     2,   10.5, 2.6, 0.9),
]

# Weak entities (double border): (label, cx, cy, w, h)
WEAK_ENTITIES = [
    ("MusicalAttributes", 7,   5.5, 3.4, 0.9),
    ("ClipVersions",      17,  5.5, 3.0, 0.9),
]

# Relationships: (label, cx, cy, hw, hh)  hw=half-width, hh=half-height
# is_identifying=True draws double border
RELATIONSHIPS = [
    ("Owns",         12,  13.0, 1.1, 0.6,  False),
    ("Creates",      14.5,13.0, 1.1, 0.6,  False),
    ("Defines",      7,   13.0, 1.1, 0.6,  False),
    ("Tagged",       4.5, 10.5, 1.1, 0.6,  False),
    ("Includes",     12,  10.5, 1.1, 0.6,  False),
    ("Collaborates", 14.5,15.5, 1.3, 0.65, False),
    ("HasAttributes",7,   7.8,  1.5, 0.65, True),
    ("HasVersion",   12,  7.8,  1.3, 0.65, True),
]

# Attributes: (label, cx, cy, parent_label, is_pk)
# PK attributes will be underlined
ATTRIBUTES = [
    # Users
    ("userID",      10.2, 16.5, "Users",    True),
    ("username",    10.2, 15.5, "Users",    False),
    ("email",       10.2, 14.5, "Users",    False),
    ("dateCreated", 13.8, 16.5, "Users",    False),

    # Clips
    ("clipID",      5.0,  11.5, "Clips",   True),
    ("title",       5.0,  10.5, "Clips",   False),
    ("duration",    5.0,   9.5, "Clips",   False),
    ("filepath",    9.0,  11.2, "Clips",   False),

    # Projects
    ("projectID",   19.2, 11.5, "Projects", True),
    ("name",        19.2, 10.5, "Projects", False),
    ("description", 19.2,  9.5, "Projects", False),

    # Tags
    ("tagID",       0.3,  11.2, "Tags",    True),
    ("tagName",     0.3,  10.2, "Tags",    False),

    # MusicalAttributes
    ("musicalKey",  4.8,  6.2, "MusicalAttributes", False),
    ("mode",        4.8,  5.2, "MusicalAttributes", False),
    ("tempo",       9.2,  6.2, "MusicalAttributes", False),
    ("timeSignature",9.4, 5.2, "MusicalAttributes", False),

    # ClipVersions
    ("versionID",   19.5, 6.5, "ClipVersions", True),
    ("versionNumber",19.5,5.5, "ClipVersions", True),
    ("notes",       19.5, 4.5, "ClipVersions", False),
]

# Relationship attributes (orange): (label, cx, cy, parent_rel)
REL_ATTRIBUTES = [
    ("role",    16.5, 16.2, "Collaborates"),
    ("addedAt", 16.5, 15.0, "Collaborates"),
]

# Edges between nodes: (from_label, to_label, cardinality_at_to)
# cardinality = "1", "N", or "" for attribute edges
EDGES = [
    # Relationships — entity connections
    ("Users",    "Owns",          ""),
    ("Owns",     "Clips",         ""),
    ("Users",    "Creates",       ""),
    ("Creates",  "Projects",      ""),
    ("Users",    "Defines",       ""),
    ("Defines",  "Tags",          ""),
    ("Clips",    "Tagged",        ""),
    ("Tagged",   "Tags",          ""),
    ("Clips",    "Includes",      ""),
    ("Includes", "Projects",      ""),
    ("Users",    "Collaborates",  ""),
    ("Collaborates", "Projects",  ""),
    ("Clips",    "HasAttributes", ""),
    ("HasAttributes", "MusicalAttributes", ""),
    ("Clips",    "HasVersion",    ""),
    ("HasVersion", "ClipVersions",""),
]

CARDINALITIES = {
    ("Owns",          "Clips"):         ("1", "N"),
    ("Users",         "Owns"):          ("1", ""),
    ("Creates",       "Projects"):      ("1", "N"),
    ("Users",         "Creates"):       ("1", ""),
    ("Defines",       "Tags"):          ("1", "N"),
    ("Users",         "Defines"):       ("1", ""),
    ("Clips",         "Tagged"):        ("M", ""),
    ("Tagged",        "Tags"):          ("", "N"),
    ("Clips",         "Includes"):      ("M", ""),
    ("Includes",      "Projects"):      ("", "N"),
    ("Users",         "Collaborates"):  ("M", ""),
    ("Collaborates",  "Projects"):      ("", "N"),
    ("Clips",         "HasAttributes"): ("1", ""),
    ("HasAttributes", "MusicalAttributes"): ("", "1"),
    ("Clips",         "HasVersion"):    ("1", ""),
    ("HasVersion",    "ClipVersions"):  ("", "N"),
}


# ---------------------------------------------------------------------------
# Helper: resolve center of a node by label
# ---------------------------------------------------------------------------

def _node_center(label: str) -> tuple[float, float]:
    for lbl, cx, cy, *_ in STRONG_ENTITIES + WEAK_ENTITIES:
        if lbl == label:
            return cx, cy
    for lbl, cx, cy, *_ in RELATIONSHIPS:
        if lbl == label:
            return cx, cy
    for lbl, cx, cy, *_ in ATTRIBUTES + REL_ATTRIBUTES:
        if lbl == label:
            return cx, cy
    raise KeyError(label)


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

C_ENTITY  = "#ADD8E6"   # light blue
C_WEAK    = "#FFE599"   # light yellow
C_REL     = "#C8E6C9"   # light green
C_RELWEAK = "#FFE599"
C_ATTR    = "#FFFFFF"
C_RELATTR = "#FFE0B2"   # light orange


def draw_rect(ax, cx, cy, w, h, color, edgecolor="#555555", lw=1.5,
              double=False, label="", fontsize=10, bold=True):
    x = cx - w / 2
    y = cy - h / 2
    ax.add_patch(plt.Rectangle((x, y), w, h,
                                facecolor=color, edgecolor=edgecolor,
                                linewidth=lw, zorder=3))
    if double:
        pad = 0.07
        ax.add_patch(plt.Rectangle((x + pad, y + pad),
                                    w - 2 * pad, h - 2 * pad,
                                    fill=False, edgecolor=edgecolor,
                                    linewidth=lw, zorder=3))
    weight = "bold" if bold else "normal"
    ax.text(cx, cy, label, ha="center", va="center",
            fontsize=fontsize, fontweight=weight, zorder=4)


def draw_diamond(ax, cx, cy, hw, hh, color, edgecolor="#555555", lw=1.5,
                 double=False, label="", fontsize=9):
    xs = [cx, cx + hw, cx, cx - hw, cx]
    ys = [cy + hh, cy, cy - hh, cy, cy + hh]
    ax.fill(xs, ys, color=color, zorder=3)
    ax.plot(xs, ys, color=edgecolor, linewidth=lw, zorder=4)
    if double:
        pad = 0.09
        xs2 = [cx, cx + hw - pad, cx, cx - hw + pad, cx]
        ys2 = [cy + hh - pad, cy, cy - hh + pad, cy, cy + hh - pad]
        ax.plot(xs2, ys2, color=edgecolor, linewidth=lw, zorder=4)
    ax.text(cx, cy, label, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", zorder=5)


def draw_ellipse(ax, cx, cy, label, color=C_ATTR, is_pk=False,
                 edgecolor="#888888", fontsize=8.5):
    ew, eh = 1.1, 0.35
    el = mpatches.Ellipse((cx, cy), ew, eh,
                            facecolor=color, edgecolor=edgecolor,
                            linewidth=1.0, zorder=3)
    ax.add_patch(el)
    style = "underline" if is_pk else "normal"
    ax.text(cx, cy, label, ha="center", va="center",
            fontsize=fontsize,
            usetex=False,
            zorder=4,
            **( {"fontweight": "normal"} ))
    if is_pk:
        # manual underline via ax.annotate is awkward; use text decoration workaround
        ax.text(cx, cy, label, ha="center", va="center",
                fontsize=fontsize, zorder=5,
                color="black",
                fontfamily="monospace")
        # draw a thin line under it
        tw = len(label) * 0.062
        ax.plot([cx - tw, cx + tw], [cy - 0.14, cy - 0.14],
                color="black", linewidth=0.8, zorder=5)


def line_between(ax, p1, p2, lw=1.2, color="#555555", double=False):
    x1, y1 = p1
    x2, y2 = p2
    ax.plot([x1, x2], [y1, y2], color=color, linewidth=lw, zorder=2)
    if double:
        # offset the second line slightly perpendicular
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length > 0:
            nx, ny = -dy / length * 0.05, dx / length * 0.05
            ax.plot([x1 + nx, x2 + nx], [y1 + ny, y2 + ny],
                    color=color, linewidth=lw, zorder=2)


def cardinality_label(ax, pa, pb, text):
    if not text:
        return
    mx = pa[0] * 0.25 + pb[0] * 0.75
    my = pa[1] * 0.25 + pb[1] * 0.75
    ax.text(mx, my, text, ha="center", va="center",
            fontsize=9, color="#222222",
            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"),
            zorder=6)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.set_aspect("equal")
    ax.axis("off")

    # Title
    ax.text(FIG_W / 2, 17.7,
            "HarmonyVault — Entity-Relationship Diagram",
            ha="center", va="center", fontsize=15, fontweight="bold")
    ax.text(FIG_W / 2, 17.25,
            "Fixes: no FKs inside entity boxes  ·  role & addedAt on Collaborates  "
            "·  MusicalAttributes & ClipVersions as weak entities (double border)",
            ha="center", va="center", fontsize=8.5, color="#444444", style="italic")

    # ---- Draw edges first (below everything) ----

    # Entity–relationship edges
    identifying_pairs = {
        ("Clips", "HasAttributes"), ("HasAttributes", "MusicalAttributes"),
        ("Clips", "HasVersion"),    ("HasVersion", "ClipVersions"),
    }
    for src, dst, *_ in EDGES:
        p1 = _node_center(src)
        p2 = _node_center(dst)
        is_id = (src, dst) in identifying_pairs
        line_between(ax, p1, p2, double=is_id)
        card = CARDINALITIES.get((src, dst), ("", ""))
        cardinality_label(ax, p1, p2, card[0])
        cardinality_label(ax, p2, p1, card[1])

    # Attribute edges
    for lbl, cx, cy, parent, *_ in ATTRIBUTES:
        pc = _node_center(parent)
        line_between(ax, (cx, cy), pc)

    for lbl, cx, cy, parent in REL_ATTRIBUTES:
        pc = _node_center(parent)
        line_between(ax, (cx, cy), pc)

    # ---- Draw nodes ----

    for lbl, cx, cy, w, h in STRONG_ENTITIES:
        draw_rect(ax, cx, cy, w, h, C_ENTITY, label=lbl, fontsize=11)

    for lbl, cx, cy, w, h in WEAK_ENTITIES:
        draw_rect(ax, cx, cy, w, h, C_WEAK, label=lbl, fontsize=10, double=True)

    for lbl, cx, cy, hw, hh, is_id in RELATIONSHIPS:
        color = C_RELWEAK if is_id else C_REL
        draw_diamond(ax, cx, cy, hw, hh, color, double=is_id, label=lbl)

    for lbl, cx, cy, parent, is_pk in ATTRIBUTES:
        draw_ellipse(ax, cx, cy, lbl, is_pk=is_pk)

    for lbl, cx, cy, parent in REL_ATTRIBUTES:
        draw_ellipse(ax, cx, cy, lbl, color=C_RELATTR)

    # ---- Legend ----
    legend_x, legend_y = 20.5, 3.8
    ax.text(legend_x, legend_y + 0.5, "Legend", fontsize=10, fontweight="bold")
    draw_rect(ax, legend_x + 0.7, legend_y - 0.2, 1.3, 0.4, C_ENTITY,
              label="Strong entity", fontsize=7.5, bold=False)
    draw_rect(ax, legend_x + 0.7, legend_y - 0.8, 1.6, 0.4, C_WEAK,
              label="Weak entity", fontsize=7.5, bold=False, double=True)
    draw_diamond(ax, legend_x + 0.7, legend_y - 1.5, 0.8, 0.35, C_REL,
                 label="Relationship", fontsize=7)
    draw_diamond(ax, legend_x + 0.7, legend_y - 2.2, 0.9, 0.38, C_RELWEAK,
                 label="Identifying rel.", fontsize=6.5, double=True)
    draw_ellipse(ax, legend_x + 0.7, legend_y - 2.9, "Attribute")
    draw_ellipse(ax, legend_x + 0.7, legend_y - 3.4, "PK (underlined)",
                 is_pk=True)
    draw_ellipse(ax, legend_x + 0.7, legend_y - 3.9, "Rel. attribute",
                 color=C_RELATTR)

    # ---- Save ----
    out_path = Path(__file__).resolve().parent.parent / "docs" / "ER_diagram.png"
    fig.savefig(out_path, dpi=180, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    print(f"Saved: {out_path}")
    plt.close(fig)


if __name__ == "__main__":
    main()
