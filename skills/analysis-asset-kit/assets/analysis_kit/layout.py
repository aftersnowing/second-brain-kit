"""Layout audit for rendered figures.

Every defect this module looks for was first found by rendering a page and
looking at it, which only ever covers the pages someone happens to open. The
first full sweep of a package that had been reviewed by eye for weeks found a
live defect on every single vessel: an appendix paragraph sitting on top of the
table it was describing. Nobody had opened that page.

- ``empty_axes``       a chart that drew nothing. The failure mode with no
                       exception behind it: a selector matching no rows leaves a
                       blank frame and the page still builds, still ships.
- ``text_overlap``     a caption or heading sitting on top of a chart or table.
- ``text_off_page``    text running past the page edge.
- ``text_on_furniture``text straddling a page rule (running head, footer line).
- ``cell_clipped``     table text wider than its own cell, so the reader sees a
                       truncated value with no indication anything was cut.
- ``font_below_floor`` a label under the print floor.

Findings are returned, never raised: the caller decides which page is allowed to
carry which defect. A linter that aborts the build gets switched off.
"""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib.pyplot as plt
from matplotlib.table import Table
from matplotlib.text import Text

PAGE_MARGIN = 0.02
"""Page-edge keep-out in figure coordinates."""

OVERLAP_TOLERANCE = 0.08
"""Overlap below this fraction of the text box counts as touching rather than
colliding. Rendered glyph boxes carry slack, and a zero-tolerance check reports
every axis label that grazes its own spine."""

FURNITURE_CLEARANCE = 0.008


@dataclass(frozen=True)
class Finding:
    kind: str
    detail: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.kind}: {self.detail}"


def _renderer(fig: plt.Figure):
    fig.canvas.draw()
    return fig.canvas.get_renderer()


def _fig_bbox(artist, renderer, fig):
    try:
        bbox = artist.get_window_extent(renderer)
    except Exception:  # noqa: BLE001 - an unmeasurable artist is simply skipped
        return None
    if bbox is None or bbox.width <= 0 or bbox.height <= 0:
        return None
    return bbox.transformed(fig.transFigure.inverted())


def _overlap_fraction(a, b) -> float:
    dx = min(a.x1, b.x1) - max(a.x0, b.x0)
    dy = min(a.y1, b.y1) - max(a.y0, b.y0)
    if dx <= 0 or dy <= 0:
        return 0.0
    area = a.width * a.height
    return (dx * dy) / area if area > 0 else 0.0


def _axes_is_empty(ax) -> bool:
    if ax.lines or ax.collections or ax.images or ax.patches:
        return False
    if ax.texts or ax.tables:
        return False
    # Bar charts land in containers on some matplotlib versions.
    if getattr(ax, "containers", None):
        return False
    return True


def _short(text: str, limit: int = 48) -> str:
    flat = " ".join(str(text).split())
    return flat if len(flat) <= limit else flat[: limit - 1] + "…"


def _collect_texts(fig: plt.Figure) -> list[tuple[Text, object]]:
    """Every explicitly placed label, with the axes that owns it (None = figure).

    ``fig.texts`` alone is not enough: a caption written with ``ax.text(...)``
    lives on the axes, and the first version of this module scanned only the
    figure level. A demo figure whose two axes-level labels sat squarely on top
    of each other audited clean. Tick labels and legend entries are deliberately
    excluded — they are laid out by matplotlib, and flagging them is noise.
    """
    items: list[tuple[Text, object]] = [(t, None) for t in fig.texts]
    for ax in fig.axes:
        items.extend((t, ax) for t in ax.texts)
    return items


def _audit_text_pairs(measured: list[tuple[Text, object]]) -> list[Finding]:
    """Labels written on top of each other.

    Text-vs-chart overlap was checked from the start; text-vs-text was not, and
    that is the one that survives review, because a collision between two short
    strings still looks like a line of text from across the room.
    """
    findings: list[Finding] = []
    for index, (text_a, box_a) in enumerate(measured):
        for text_b, box_b in measured[index + 1 :]:
            fraction = max(_overlap_fraction(box_a, box_b), _overlap_fraction(box_b, box_a))
            if fraction > OVERLAP_TOLERANCE:
                findings.append(
                    Finding(
                        "text_collision",
                        f"{fraction:.0%} overlap: “{_short(text_a.get_text(), 28)}” "
                        f"and “{_short(text_b.get_text(), 28)}”",
                    )
                )
    return findings


def audit_figure(
    fig: plt.Figure,
    *,
    min_font_pt: float,
    furniture_rules: tuple[float, ...] = (),
) -> list[Finding]:
    """Layout findings for one rendered figure.

    ``min_font_pt`` has no default on purpose. The right floor depends on the
    scale the figure will be embedded at, and a module-level constant here would
    silently pass figures destined for a report body. Get it from
    ``style.font_floor(embed_scale)``.

    ``furniture_rules`` are figure-coordinate y positions of page rules (running
    head, footer). Text straddling one reads as broken even though it sits
    inside the page. Empty means the figure has no page furniture.
    """
    findings: list[Finding] = []
    renderer = _renderer(fig)

    axes_boxes: list[tuple[object, object]] = []
    for ax in fig.axes:
        if _axes_is_empty(ax):
            title = ax.get_title() or ax.get_ylabel() or "untitled"
            findings.append(Finding("empty_axes", f"chart drew nothing ({_short(title)})"))
        box = _fig_bbox(ax, renderer, fig)
        if box is not None:
            axes_boxes.append((ax, box))

    measured: list[tuple[Text, object]] = []
    for text, owner in _collect_texts(fig):
        if not str(text.get_text()).strip():
            continue
        size = float(text.get_fontsize() or 0)
        if size and size < min_font_pt - 1e-6:
            findings.append(
                Finding(
                    "font_below_floor",
                    f"{size:.2f}pt < {min_font_pt:.2f}pt: {_short(text.get_text())}",
                )
            )
        box = _fig_bbox(text, renderer, fig)
        if box is None:
            continue
        measured.append((text, box))
        if (
            box.x0 < PAGE_MARGIN
            or box.y0 < PAGE_MARGIN
            or box.x1 > 1.0 - PAGE_MARGIN
            or box.y1 > 1.0 - PAGE_MARGIN
        ):
            findings.append(Finding("text_off_page", _short(text.get_text())))
        for rule in furniture_rules:
            if box.y0 < rule + FURNITURE_CLEARANCE and box.y1 > rule - FURNITURE_CLEARANCE:
                # Head and footer legitimately sit outside the rules; only text
                # that straddles one is a collision.
                if not (box.y1 < rule or box.y0 > rule):
                    findings.append(
                        Finding(
                            "text_on_furniture",
                            f"crosses the rule at y={rule:g}: {_short(text.get_text())}",
                        )
                    )
                    break
        for ax, ax_box in axes_boxes:
            if ax is owner:
                # A label placed inside its own axes is not a collision with it.
                continue
            fraction = _overlap_fraction(box, ax_box)
            if fraction > OVERLAP_TOLERANCE:
                where = ax.get_title() or "chart"
                findings.append(
                    Finding(
                        "text_overlap",
                        f"{fraction:.0%} of “{_short(text.get_text(), 36)}” sits on {_short(where, 32)}",
                    )
                )
                break

    findings.extend(_audit_text_pairs(measured))
    findings.extend(_audit_tables(fig, renderer, min_font_pt))
    return findings


def _audit_tables(fig: plt.Figure, renderer, min_font_pt: float) -> list[Finding]:
    findings: list[Finding] = []
    for ax in fig.axes:
        for table in [a for a in ax.get_children() if isinstance(a, Table)]:
            for (row, col), cell in table.get_celld().items():
                label: Text = cell.get_text()
                content = str(label.get_text()).strip()
                if not content:
                    continue
                size = float(label.get_fontsize() or 0)
                if size and size < min_font_pt - 1e-6:
                    findings.append(
                        Finding(
                            "font_below_floor",
                            f"{size:.2f}pt in table cell r{row}c{col}: {_short(content)}",
                        )
                    )
                text_box = _fig_bbox(label, renderer, fig)
                cell_box = _fig_bbox(cell, renderer, fig)
                if text_box is None or cell_box is None or cell_box.width <= 0:
                    continue
                # Matplotlib clips drawn glyphs to the cell, so compare the
                # text's own measured width against the space it was given.
                if text_box.width > cell_box.width * 0.99:
                    findings.append(
                        Finding(
                            "cell_clipped",
                            f"r{row}c{col} needs {text_box.width / cell_box.width:.0%} "
                            f"of its cell: {_short(content, 36)}",
                        )
                    )
    return findings


def format_findings(page: str, findings: list[Finding]) -> list[str]:
    return [f"{page}: {finding}" for finding in findings]
