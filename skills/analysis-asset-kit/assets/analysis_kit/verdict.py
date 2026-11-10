"""Verdicts that cannot be laundered into numbers.

The failure this module prevents is specific. Two modules in one repository
implemented the same graduated verdict; one returned ``NO_DATA`` for a NaN
residual and one had no guard at all, so a NaN fell through every comparison
(``nan >= 8`` is False, and so is ``nan >= 5``) and came out ``PASS``. The
second module was safe only because three unrelated files upstream happened to
guarantee finite inputs. Safety held at a distance is safety that will break
when the code moves.

The other failure is quieter. Analysis code routinely reaches a point where it
cannot answer — a channel is dead, the sample does not support a fit, the query
sits outside the observed range, the two sides are not on the same basis. If
that state is expressed as a bare NaN or a raised exception, it is gone by the
time anyone reads the table: NaN prints as a blank cell, and an exception gets
swallowed by whatever ``try`` block surrounds the loop. Either way the
deliverable claims coverage it does not have.

So refusal is a *return value* that travels all the way to the page, and the
number inside it cannot be extracted without confronting the reason.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class Reason(str, Enum):
    """Why an analysis declined to produce a number."""

    NO_DATA = "NO_DATA"
    """No valid sample at all."""

    INSUFFICIENT_SUPPORT = "INSUFFICIENT_SUPPORT"
    """Sample exists but is too thin or too narrow to carry a fit."""

    OUT_OF_SUPPORT_RANGE = "OUT_OF_SUPPORT_RANGE"
    """The query point lies outside the observed range — extrapolation."""

    BASIS_MISMATCH = "BASIS_MISMATCH"
    """The two sides are not comparable as stated (different reference,
    normalisation, scope, or operating state). Reconcile the basis, do not
    report the difference."""

    def __str__(self) -> str:
        return self.value


class Rejected(Exception):
    """Raised when a caller tries to read a number that was never produced."""

    def __init__(self, reason: Reason, note: str = "") -> None:
        self.reason = reason
        self.note = note
        super().__init__(f"{reason}{f': {note}' if note else ''}")


@dataclass(frozen=True)
class Outcome:
    """A number, or a stated reason there is none. Never both, never neither."""

    _value: float | None
    reason: Reason | None
    note: str = ""

    @classmethod
    def ok(cls, value: float) -> "Outcome":
        numeric = float(value)
        if math.isnan(numeric) or math.isinf(numeric):
            raise ValueError(
                "Outcome.ok() received a non-finite value. A NaN is not a result — "
                "use Outcome.rejected(Reason.NO_DATA) and say so."
            )
        return cls(numeric, None)

    @classmethod
    def rejected(cls, reason: Reason, note: str = "") -> "Outcome":
        return cls(None, reason, note)

    @property
    def is_ok(self) -> bool:
        return self.reason is None

    @property
    def value(self) -> float:
        """The number. Raises ``Rejected`` when there is none.

        This is deliberately loud. A caller that wants to keep going must say so
        with ``value_or``, and that call site is then greppable.
        """
        if self.reason is not None:
            raise Rejected(self.reason, self.note)
        assert self._value is not None  # narrowed by the guard above
        return self._value

    def value_or(self, default: float | None) -> float | None:
        return self._value if self.reason is None else default

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        """Renders for a table cell: the number, or the reason it is absent."""
        if self.reason is not None:
            return str(self.reason)
        return f"{self._value:g}"

    def __format__(self, spec: str) -> str:
        """A numeric spec on a rejected outcome yields the reason, not an error.

        ``f"{outcome:.2f}"`` is how these reach a table cell, and that call site
        must not have to branch. A rejected outcome ignores the numeric spec and
        prints its reason, so the cell reads ``INSUFFICIENT_SUPPORT`` instead of
        a blank or a fabricated zero.
        """
        if self.reason is not None:
            return str(self.reason)
        return format(self._value, spec)


# ---------------------------------------------------------------------------
# Support checks
# ---------------------------------------------------------------------------


def check_support(n_points: int, *, n_min: int) -> Reason | None:
    """``None`` when the sample carries a fit, otherwise the reason it does not."""
    if n_points <= 0:
        return Reason.NO_DATA
    if n_points < n_min:
        return Reason.INSUFFICIENT_SUPPORT
    return None


def check_range(x: float, lo: float, hi: float) -> Reason | None:
    """``None`` when ``x`` sits inside the observed support."""
    if math.isnan(x) or math.isnan(lo) or math.isnan(hi):
        return Reason.NO_DATA
    return None if lo <= x <= hi else Reason.OUT_OF_SUPPORT_RANGE


# ---------------------------------------------------------------------------
# Graduated verdict
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Thresholds:
    """Verdict boundaries bound to the population they were derived from.

    ``source`` is required and has no default. Thresholds are the one thing in a
    shared toolkit that is guaranteed *not* to generalise: a band calibrated on
    one engine class, instrument, or contract says nothing about the next. A
    hidden default here produces a confident PASS on a population nobody
    checked — which is worse than a crash, because it ships.
    """

    warn: tuple[float, float]
    fail: tuple[float, float]
    source: str

    def __post_init__(self) -> None:
        if not str(self.source).strip():
            raise ValueError(
                "Thresholds.source must name the population these values were "
                "derived from, e.g. '<fleet> <ship type> M/E SFC, 15 hulls, 2026-07'."
            )
        if self.warn[0] >= self.fail[0] or self.warn[1] >= self.fail[1]:
            raise ValueError(f"warn must be tighter than fail: {self.warn} vs {self.fail}")


def graduated_verdict(
    mean_abs: float,
    max_abs: float,
    *,
    thresholds: Thresholds,
) -> str:
    """``PASS`` / ``WARN`` / ``FAIL`` / ``NO_DATA`` from a residual pair.

    Non-finite input returns ``NO_DATA``. It does not return ``PASS``, and it
    does not raise — an absent measurement is a reportable state, not an error
    and not a pass.
    """
    if not (math.isfinite(mean_abs) and math.isfinite(max_abs)):
        return "NO_DATA"
    if mean_abs >= thresholds.fail[0] or max_abs >= thresholds.fail[1]:
        return "FAIL"
    if mean_abs >= thresholds.warn[0] or max_abs >= thresholds.warn[1]:
        return "WARN"
    return "PASS"
