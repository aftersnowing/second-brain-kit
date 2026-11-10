"""Portable analysis assets: one implementation, every project.

    import os, sys
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/analysis-asset-kit/assets"))
    from analysis_kit import tiers, configure, audit_figure, Outcome, Reason

``verdict`` is pure logic and always importable. ``style`` and ``layout`` need
matplotlib and are therefore loaded on first use, not at import time: a project
that only validates tables should not be locked out of the verdict contract
because its virtualenv has no plotting stack. (Found by running the kit inside a
matplotlib-free venv, where importing anything at all used to fail.)

See SKILL.md for the four contracts and the two rituals.
"""

from .verdict import (
    Outcome,
    Reason,
    Rejected,
    Thresholds,
    check_range,
    check_support,
    graduated_verdict,
)

_LAZY = {
    "layout": ("Finding", "audit_figure", "format_findings"),
    "style": (
        "ACCENT", "EMBED_MIN_PT", "GRID", "INK", "LIGHT", "MUTED", "SERIES", "STATUS",
        "WHITE", "Tiers", "configure", "font_floor", "resolve_font", "status_color",
        "style_axis", "tiers",
    ),
}
_OWNER = {name: module for module, names in _LAZY.items() for name in names}


def __getattr__(name: str):
    """PEP 562 lazy export for the matplotlib-backed halves."""
    module_name = _OWNER.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    try:
        module = import_module(f".{module_name}", __name__)
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise ImportError(
            f"analysis_kit.{name} needs matplotlib, which is not installed in this "
            f"environment. The verdict contract (Outcome / Reason / Thresholds / "
            f"graduated_verdict) works without it."
        ) from exc
    value = getattr(module, name)
    globals()[name] = value  # subsequent lookups skip this path
    return value


def __dir__() -> list[str]:
    return sorted(__all__)


__all__ = [
    # verdict — always available
    "Outcome", "Reason", "Rejected", "Thresholds",
    "check_range", "check_support", "graduated_verdict",
    # style — needs matplotlib
    "ACCENT", "EMBED_MIN_PT", "GRID", "INK", "LIGHT", "MUTED", "SERIES", "STATUS", "WHITE",
    "Tiers", "configure", "font_floor", "resolve_font", "status_color", "style_axis", "tiers",
    # layout — needs matplotlib
    "Finding", "audit_figure", "format_findings",
]
