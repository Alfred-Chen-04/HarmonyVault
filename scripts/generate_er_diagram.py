"""
generate_er_diagram.py — Generates HarmonyVault ER diagram as a PNG.

Usage (from repo root, with venv active):
    python scripts/generate_er_diagram.py

Output: docs/ER_diagram.png
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
FIG_W, FIG_H = 34, 25

# ---------------------------------------------------------------------------
# Entity definitions: (label, cx, cy, w, h)
# ---------------------------------------------------------------------------
STRONG_ENTITIES: list[tuple[str, float, float, float, float]] = [
    ("Users",    15.5, 20.0, 3.0, 1.0),
    ("Clips",    9.5,  12.5, 3.0, 1.0),
    ("Projects", 23.0, 12.5, 3.0, 1.0),
    ("Tags",     3.0,  12.5, 3.0, 1.0),
]

# Weak entities — drawn with double border
WEAK_ENTITIES: list[tuple[str, float, float, float, float]] = [
    ("MusicalAttributes", 7.5,  5.5, 3.8, 1.0),
    ("ClipVersions",      23.0, 5.5, 3.4, 1.0),
]

# Relationships: (label, cx, cy, half_w, half_h, is_identifying)
RELATIONSHIPS: list[tuple[str, float, float, float, float, bool]] = [
    ("Owns",          9.5,  17.0, 1.2, 0.65, False),
    ("Creates",       21.0, 17.0, 1.2, 0.65, False),
    ("Defines",       5.5,  16.5, 1.2, 0.65, False),
    ("Tagged",        6.0,  12.5, 1.2, 0.65, False),
    ("Includes",      16.0, 12.5, 1.2, 0.65, False),
    ("Collaborates",  23.0, 20.0, 1.4, 0.70, False),
    ("HasAttributes", 8.0,   9.0, 1.5, 0.70, True),
    ("HasVersion",    15.5,  9.0, 1.4, 0.70, True),
]

# ---------------------------------------------------------------------------
# Attributes: (label, cx, cy, entity_label, key_type)
# key_type: "pk" = primary key (solid underline), "partial" = partial key
#           (dashed ellipse + underline), None = regular
# ---------------------------------------------------------------------------
ATTRIBUTES: list[tuple[str, float, float, str, str | None]] = [
    # Users
    ("userID",       12.5, 21.3, "Users",    "pk"),
    ("username",     12.5, 20.3, "Users",    None),
    ("email",        12.5, 19.2, "Users",    None),
    ("dateCreated",  18.5, 21.3, "Users",    None),

    # Clips
    ("clipID",        6.7,  13.8, "Clips",   "pk"),
    ("title",         6.7,  12.8, "Clips",   None),
    ("duration",      6.7,  11.8, "Clips",   None),
    ("filepath",      12.5, 13.5, "Clips",   None),
    ("dateCreated",   12.5, 12.3, "Clips",   None),

    # Projects  — attributes on the LEFT of Projects to avoid right-edge crowding
    ("projectID",    19.5, 13.8, "Projects", "pk"),
    ("name",         19.5, 12.8, "Projects", None),
    ("description",  19.5, 11.8, "Projects", None),
    ("dateCreated",  19.5, 10.7, "Projects", None),

    # Tags
    ("tagID",         0.5,  13.5, "Tags",    "pk"),
    ("tagName",       0.5,  12.5, "Tags",    None),

    # MusicalAttributes
    ("musicalKey",    4.8,   6.7, "MusicalAttributes", None),
    ("mode",          4.8,   5.7, "MusicalAttributes", None),
    ("tempo",        10.2,   6.7, "MusicalAttributes", None),
    ("timeSignature",10.2,   5.7, "MusicalAttributes", None),

    # ClipVersions — attributes on the RIGHT, clear of Projects
    # versionNumber is the partial key; versionID omitted (relational surrogate)
    ("versionNumber", 27.0,  7.2, "ClipVersions", "partial"),
    ("notes",         27.0,  6.2, "ClipVersions", None),
    ("filepath",      27.0,  5.2, "ClipVersions", None),
    ("dateCreated",   27.0,  4.2, "ClipVersions", None),
]

# Relationship attributes (drawn in orange)
REL_ATTRIBUTES: list[tuple[str, float, float, str]] = [
    ("role",    26.5, 21.0, "Collaborates"),
    ("addedAt", 26.5, 19.2, "Collaborates"),
]

# Edges: (from, to)  — cardinalities are looked up in CARDINALITIES
# "from" cardinality is placed near "from", "to" cardinality near "to"
EDGES: list[tuple[str, str]] = [
    ("Users",    "Owns"),
    ("Owns",     "Clips"),
    ("Users",    "Creates"),
    ("Creates",  "Projects"),
    ("Users",    "Defines"),
    ("Defines",  "Tags"),
    ("Clips",    "Tagged"),
    ("Tagged",   "Tags"),
    ("Clips",    "Includes"),
    ("Includes", "Projects"),
    ("Users",    "Collaborates"),
    ("Collaborates", "Projects"),
    ("Clips",    "HasAttributes"),
    ("HasAttributes", "MusicalAttributes"),
    ("Clips",    "HasVersion"),
    ("HasVersion", "ClipVersions"),
]

# (src, dst) → (label_near_src, label_near_dst)
CARDINALITIES: dict[tuple[str, str], tuple[str, str]] = {
    ("Users",    "Owns"):             ("1", ""),
    ("Owns",     "Clips"):            ("",  "N"),
    ("Users",    "Creates"):          ("1", ""),
    ("Creates",  "Projects"):         ("",  "N"),
    ("Users",    "Defines"):          ("1", ""),
    ("Defines",  "Tags"):             ("",  "N"),
    ("Clips",    "Tagged"):           ("M", ""),
    ("Tagged",   "Tags"):             ("",  "N"),
    ("Clips",    "Includes"):         ("M", ""),
    ("Includes", "Projects"):         ("",  "N"),
    ("Users",    "Collaborates"):     ("M", ""),
    ("Collaborates", "Projects"):     ("",  "N"),
    ("Clips",    "HasAttributes"):    ("1", ""),
    ("HasAttributes", "MusicalAttributes"): ("", "1"),
    ("Clips",    "HasVersion"):       ("1", ""),
    ("HasVersion", "ClipVersions"):   ("",  "N"),
}

# Pairs whose edges use double lines (identifying relationships)
IDENTIFYING_PAIRS: set[tuple[str, str]] = {
    ("Clips", "HasAttributes"),
    ("HasAttributes", "MusicalAttributes"),
    ("Clips", "HasVersion"),
    ("HasVersion", "ClipVersions"),
}

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
C_ENTITY   = "#BBD6F5"   # light blue
C_WEAK     = "#FFF0A0"   # light yellow
C_REL      = "#C8E6C9"   # light green
C_ID_REL   = "#FFF0A0"   # same as weak — identifying rel color
C_ATTR     = "#FFFFFF"
C_REL_ATTR = "#FFD9A0"   # light orange
C_BORDER   = "#555555"


# ---------------------------------------------------------------------------
# Node-center resolution
# ---------------------------------------------------------------------------
def _center(label: str) -> tuple[float, float]:
    for (lbl, cx, cy, *_) in STRONG_ENTITIES + WEAK_ENTITIES:
        if lbl == label:
            return cx, cy
    for (lbl, cx, cy, *_) in RELATIONSHIPS:
        if lbl == label:
            return cx, cy
    for (lbl, cx, cy, *_) in ATTRIBUTES + REL_ATTRIBUTES:
        if lbl == label:
            return cx, cy
    raise KeyError(label)


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _draw_entity(ax, cx, cy, w, h, color, label, double=False, fs=12):
    x, y = cx - w / 2, cy - h / 2
    rect = plt.Rectangle((x, y), w, h, facecolor=color, edgecolor=C_BORDER,
                          linewidth=1.8, zorder=4)
    ax.add_patch(rect)
    if double:
        pad = 0.09
        inner = plt.Rectangle((x + pad, y + pad), w - 2 * pad, h - 2 * pad,
                               fill=False, edgecolor=C_BORDER,
                               linewidth=1.8, zorder=4)
        ax.add_patch(inner)
    ax.text(cx, cy, label, ha="center", va="center",
            fontsize=fs, fontweight="bold", zorder=5)


def _draw_diamond(ax, cx, cy, hw, hh, color, label, double=False, fs=9):
    xs = [cx, cx + hw, cx, cx - hw, cx]
    ys = [cy + hh, cy,  cy - hh, cy, cy + hh]
    ax.fill(xs, ys, color=color, zorder=4)
    ax.plot(xs, ys, color=C_BORDER, linewidth=1.8, zorder=5)
    if double:
        p = 0.10
        xi = [cx, cx + hw - p, cx, cx - hw + p, cx]
        yi = [cy + hh - p, cy, cy - hh + p, cy, cy + hh - p]
        ax.plot(xi, yi, color=C_BORDER, linewidth=1.5, zorder=5)
    ax.text(cx, cy, label, ha="center", va="center",
            fontsize=fs, fontweight="bold", zorder=6)


def _draw_attr(ax, cx, cy, label, color=C_ATTR, key_type: str | None = None,
               edgecolor=C_BORDER, lw=1.0):
    ew, eh = 1.3, 0.42
    dashed = key_type == "partial"
    ls = (0, (3, 2)) if dashed else "-"
    edge_lw = 1.5 if dashed else lw
    el = mpatches.Ellipse((cx, cy), ew, eh, facecolor=color,
                           edgecolor=edgecolor, linewidth=edge_lw,
                           linestyle=ls, zorder=4)
    ax.add_patch(el)

    fs = 8.0
    ax.text(cx, cy, label, ha="center", va="center", fontsize=fs, zorder=5)

    if key_type in ("pk", "partial"):
        # draw a thin underline under the text
        char_w = 0.058 * fs / 8.0
        half_len = max(len(label) * char_w, 0.18)
        baseline = cy - 0.09
        ax.plot([cx - half_len, cx + half_len], [baseline, baseline],
                color="black", linewidth=0.9, zorder=6)


def _draw_line(ax, p1, p2, double=False, lw=1.4):
    x1, y1 = p1
    x2, y2 = p2
    ax.plot([x1, x2], [y1, y2], color=C_BORDER, linewidth=lw, zorder=2)
    if double:
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy)
        if dist > 1e-6:
            nx, ny = -dy / dist * 0.06, dx / dist * 0.06
            ax.plot([x1 + nx, x2 + nx], [y1 + ny, y2 + ny],
                    color=C_BORDER, linewidth=lw, zorder=2)


def _cardinality_label(ax, near: tuple[float, float], far: tuple[float, float],
                        text: str):
    if not text:
        return
    # place label 22% of the way from "near" toward "far"
    t = 0.22
    mx = near[0] * (1 - t) + far[0] * t
    my = near[1] * (1 - t) + far[1] * t
    ax.text(mx, my, text, ha="center", va="center", fontsize=9.5,
            fontweight="bold", color="#1a1a1a",
            bbox=dict(boxstyle="round,pad=0.08", fc="white", ec="none",
                      alpha=0.85),
            zorder=7)


# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------
def _draw_legend(ax, lx, ly):
    ax.text(lx, ly, "Legend", fontsize=10, fontweight="bold")
    dy = 0.9
    _draw_entity(ax, lx + 0.8, ly - dy, 1.5, 0.5, C_ENTITY,
                 "Strong entity", fs=7)
    dy += 0.8
    _draw_entity(ax, lx + 0.8, ly - dy, 1.7, 0.5, C_WEAK,
                 "Weak entity", double=True, fs=7)
    dy += 0.9
    _draw_diamond(ax, lx + 0.8, ly - dy, 0.85, 0.38, C_REL,
                  "Relationship", fs=6.5)
    dy += 0.9
    _draw_diamond(ax, lx + 0.8, ly - dy, 0.95, 0.42, C_ID_REL,
                  "Identifying rel.", double=True, fs=6)
    dy += 0.9
    _draw_attr(ax, lx + 0.8, ly - dy, "Attribute")
    dy += 0.6
    _draw_attr(ax, lx + 0.8, ly - dy, "PK (underlined)", key_type="pk")
    dy += 0.6
    _draw_attr(ax, lx + 0.8, ly - dy, "Partial key", key_type="partial")
    dy += 0.6
    _draw_attr(ax, lx + 0.8, ly - dy, "Rel. attribute", color=C_REL_ATTR)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # Title — placed well above the diagram content (Users top edge ≈ y 20.5)
    ax.text(FIG_W / 2, 24.3,
            "HarmonyVault — Entity-Relationship Diagram",
            ha="center", va="center", fontsize=16, fontweight="bold")
    ax.text(FIG_W / 2, 23.7,
            "Corrected per TA feedback: no FK attributes inside entity boxes  ·  "
            "role & addedAt on Collaborates diamond  ·  "
            "weak entities = double border  ·  "
            "identifying relationships = double diamond  ·  "
            "versionNumber = partial key (dashed ellipse)",
            ha="center", va="center", fontsize=8, color="#444444",
            style="italic")

    # ---- Edges (drawn first, below everything) ----
    for (src, dst) in EDGES:
        p1 = _center(src)
        p2 = _center(dst)
        is_id = (src, dst) in IDENTIFYING_PAIRS
        _draw_line(ax, p1, p2, double=is_id)
        cards = CARDINALITIES.get((src, dst), ("", ""))
        _cardinality_label(ax, p1, p2, cards[0])
        _cardinality_label(ax, p2, p1, cards[1])

    # Attribute edges
    for (lbl, cx, cy, parent, *_) in ATTRIBUTES:
        _draw_line(ax, (cx, cy), _center(parent))

    for (lbl, cx, cy, parent) in REL_ATTRIBUTES:
        _draw_line(ax, (cx, cy), _center(parent))

    # ---- Draw entities ----
    for (lbl, cx, cy, w, h) in STRONG_ENTITIES:
        _draw_entity(ax, cx, cy, w, h, C_ENTITY, lbl, fs=12)

    for (lbl, cx, cy, w, h) in WEAK_ENTITIES:
        _draw_entity(ax, cx, cy, w, h, C_WEAK, lbl, double=True, fs=11)

    # ---- Draw relationships ----
    for (lbl, cx, cy, hw, hh, is_id) in RELATIONSHIPS:
        color = C_ID_REL if is_id else C_REL
        _draw_diamond(ax, cx, cy, hw, hh, color, lbl, double=is_id, fs=9)

    # ---- Draw attributes ----
    for (lbl, cx, cy, parent, key_type) in ATTRIBUTES:
        _draw_attr(ax, cx, cy, lbl, key_type=key_type)

    for (lbl, cx, cy, parent) in REL_ATTRIBUTES:
        _draw_attr(ax, cx, cy, lbl, color=C_REL_ATTR)

    # ---- Legend (bottom-left) ----
    _draw_legend(ax, 0.3, 9.5)

    # ---- Save ----
    out = Path(__file__).resolve().parent.parent / "docs" / "ER_diagram.png"
    fig.savefig(out, dpi=200, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    print(f"Saved: {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()
