"""Deterministic visual system for delivery figures.

One repository held four style modules that disagreed on both the palette and
the font floor, and two of them were each right for their own use: one produced
figures that *were* the page, the other produced figures a report inserted at
0.72x. Nine-point text survives the first and dies in the second. The floor is
therefore not a constant — it is a function of how the figure will be placed,
and every module that hard-codes it will eventually be wrong somewhere.

Two ideas are encoded here:

- ``font_floor(embed_scale)`` derives the native lower bound from the smallest
  scale the figure will be embedded at. Tiers are built up from that floor, so
  a figure can never be specified below print legibility.
- The palette carries data in greyscale and reserves one saturated colour for
  the point being made. Emphasis you cannot name is emphasis you should not draw.

Nothing here knows about any particular project, product name, or page size.
"""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib
from matplotlib import font_manager

# ---------------------------------------------------------------------------
# Colour
# ---------------------------------------------------------------------------

INK = "#1F2933"
"""Body text, axis labels, spines that must be read."""

MUTED = "#6B7785"
"""Secondary text: footers, notes, units, annotations that support the reading."""

GRID = "#D9E0E7"
"""Gridlines and rules. Must never compete with data."""

LIGHT = "#EEF2F5"
"""Fill for banding, header cells, shaded regions."""

WHITE = "#FFFFFF"

ACCENT = "#B4232A"
"""The only saturated colour on a delivery figure.

It marks the one thing the reader must take away: the contract/reference line,
the subject entity among its peers, the exceedance. Using it for a second
purpose on the same figure destroys its meaning — split the panel instead.
"""

SERIES = ("#1F2933", "#5A6672", "#96A0AB", "#C3CBD4")
"""Up to four unemphasised series, dark to light.

Beyond four, greyscale separation fails. That is a signal to switch to a
colourbar (for a continuous variable) or to split panels — not to add colours.
"""

STATUS = {
    "PASS": "#2E7D5B",
    "WARN": "#D99000",
    "FAIL": "#B4232A",
    "NO_DATA": "#6B7785",
}
"""Verdict colours for chips and table cells only — never for curves.

These are the one place saturated colour is allowed alongside ACCENT, because
they are categorical labels rather than data. They are also the one place that
needs a non-colour fallback: always print the verdict word next to the colour,
since roughly one reader in twelve cannot separate the green from the red.
"""


def status_color(value: str) -> str:
    """Colour for a verdict string. Unknown values read as NO_DATA, not as PASS."""
    return STATUS.get(str(value).strip().upper(), STATUS["NO_DATA"])


# ---------------------------------------------------------------------------
# Type size
# ---------------------------------------------------------------------------

EMBED_MIN_PT = 9.0
"""Point size that must survive into the printed deliverable.

Provenance: exec-report review practice — below this, axis ticks stop being
read at arm's length on A4. Raise it for wall-projected decks; lower it only
against a rendered proof.
"""

_RATIOS = {
    "title": 2.30,
    "section": 1.40,
    "axis": 1.15,
    "tick": 1.05,
    "legend": 1.05,
    "note": 1.00,
}


@dataclass(frozen=True)
class Tiers:
    """Font sizes for one figure, all guaranteed at or above ``floor``."""

    floor: float
    title: float
    section: float
    axis: float
    tick: float
    legend: float
    note: float

    def smallest(self) -> float:
        return min(self.title, self.section, self.axis, self.tick, self.legend, self.note)


def font_floor(embed_scale: float = 1.0) -> float:
    """Native point floor for a figure that will be placed at ``embed_scale``.

    ``embed_scale`` is the *smallest* scale the figure will be inserted at:
    1.0 when the figure is the page itself, ~0.72 for a figure dropped into a
    report body. Pass the smallest, not the typical — a figure is only as
    legible as its worst placement.
    """
    if not 0.0 < embed_scale <= 1.0:
        raise ValueError(f"embed_scale must be in (0, 1], got {embed_scale!r}")
    return EMBED_MIN_PT / embed_scale


def tiers(embed_scale: float = 1.0) -> Tiers:
    """Build a tier set from the embed scale. This is the only way to get sizes."""
    floor = font_floor(embed_scale)
    return Tiers(floor=floor, **{k: round(floor * r, 1) for k, r in _RATIOS.items()})


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

FONT_CANDIDATES = (
    "Pretendard",
    "Noto Sans CJK KR",
    "NanumGothic",
    "Malgun Gothic",
    "AppleGothic",
    "DejaVu Sans",
)
"""Preference order. The CJK-capable faces come first because a missing Korean
glyph renders as a tofu box that no linter catches and every reader sees."""


def resolve_font(candidates: tuple[str, ...] = FONT_CANDIDATES) -> str:
    available = {f.name for f in font_manager.fontManager.ttflist}
    return next((name for name in candidates if name in available), "DejaVu Sans")


def configure(t: Tiers, *, font: str | None = None, headless: bool = True) -> str:
    """Apply deterministic matplotlib defaults. Returns the resolved font name.

    ``pdf.fonttype = 42`` embeds TrueType rather than converting to outlines,
    which keeps text selectable and searchable in the delivered PDF — reviewers
    grep deliverables, and an outlined figure silently defeats that.
    """
    if headless:
        matplotlib.use("Agg")
    resolved = font or resolve_font()
    matplotlib.rcParams.update(
        {
            "font.family": resolved,
            "axes.unicode_minus": False,
            "font.size": t.note,
            "axes.titlesize": t.section,
            "axes.labelsize": t.axis,
            "xtick.labelsize": t.tick,
            "ytick.labelsize": t.tick,
            "legend.fontsize": t.legend,
            "figure.facecolor": WHITE,
            "axes.facecolor": WHITE,
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "axes.titlecolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "grid.color": GRID,
            "grid.alpha": 0.70,
            "grid.linewidth": 0.70,
            "legend.frameon": True,
            "legend.framealpha": 0.92,
            "savefig.facecolor": WHITE,
            "savefig.bbox": None,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    return resolved


def style_axis(ax, t: Tiers, *, grid: str | None = "both") -> None:
    """Apply tiers and neutral furniture to one axis."""
    ax.tick_params(labelsize=t.tick, colors=INK)
    ax.xaxis.label.set_size(t.axis)
    ax.yaxis.label.set_size(t.axis)
    ax.title.set_size(t.section)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    if grid:
        ax.grid(True, axis=grid, color=GRID, linewidth=0.70, alpha=0.70)
    ax.set_axisbelow(True)
