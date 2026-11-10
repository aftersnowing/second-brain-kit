"""Contract tests for the kit. Run these once in any new project.

They are not testing arithmetic. Each one pins a rule that was learned by
shipping the mistake, and the kit is only worth importing while they pass:

    python3 test_analysis_kit.py        # no pytest needed
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from analysis_kit import (  # noqa: E402
    Outcome,
    Reason,
    Rejected,
    Thresholds,
    audit_figure,
    check_range,
    check_support,
    configure,
    font_floor,
    graduated_verdict,
    status_color,
    style_axis,
    tiers,
)


# --- the floor is a function of placement, not a constant -------------------

def test_font_floor_tracks_embed_scale():
    assert font_floor(1.0) == 9.0
    assert abs(font_floor(0.72) - 12.5) < 1e-9
    for bad in (0.0, -0.5, 1.5):
        try:
            font_floor(bad)
        except ValueError:
            continue
        raise AssertionError(f"font_floor({bad}) should have refused")


def test_no_tier_can_be_specified_below_the_floor():
    for scale in (1.0, 0.85, 0.72):
        t = tiers(scale)
        assert t.smallest() >= t.floor - 1e-9, (scale, t)


# --- thresholds must carry their provenance --------------------------------

def test_thresholds_require_a_named_population():
    for empty in ("", "   "):
        try:
            Thresholds(warn=(5, 15), fail=(8, 30), source=empty)
        except ValueError:
            continue
        raise AssertionError("Thresholds accepted an unsourced band")


def test_thresholds_reject_an_inverted_band():
    try:
        Thresholds(warn=(9, 40), fail=(8, 30), source="test")
    except ValueError:
        return
    raise AssertionError("warn looser than fail should have been refused")


# --- absent measurement is never a pass ------------------------------------

TH = Thresholds(warn=(5, 15), fail=(8, 30), source="unit test only")


def test_nan_residual_is_no_data_not_pass():
    assert graduated_verdict(float("nan"), float("nan"), thresholds=TH) == "NO_DATA"
    assert graduated_verdict(1.0, float("nan"), thresholds=TH) == "NO_DATA"
    assert graduated_verdict(float("inf"), 1.0, thresholds=TH) == "NO_DATA"


def test_graduated_boundaries():
    assert graduated_verdict(4.9, 14.9, thresholds=TH) == "PASS"
    assert graduated_verdict(5.0, 1.0, thresholds=TH) == "WARN"
    assert graduated_verdict(1.0, 15.0, thresholds=TH) == "WARN"
    assert graduated_verdict(8.0, 1.0, thresholds=TH) == "FAIL"
    assert graduated_verdict(1.0, 30.0, thresholds=TH) == "FAIL"


def test_thresholds_cannot_be_omitted():
    try:
        graduated_verdict(1.0, 1.0)  # type: ignore[call-arg]
    except TypeError:
        return
    raise AssertionError("graduated_verdict ran without stated thresholds")


# --- a refusal cannot be laundered into a number ---------------------------

def test_ok_refuses_a_non_finite_value():
    for bad in (float("nan"), float("inf")):
        try:
            Outcome.ok(bad)
        except ValueError:
            continue
        raise AssertionError(f"Outcome.ok({bad}) should have refused")


def test_rejected_outcome_raises_on_value_access():
    o = Outcome.rejected(Reason.INSUFFICIENT_SUPPORT, "3 bins, need 8")
    assert not o.is_ok
    try:
        o.value
    except Rejected as exc:
        assert exc.reason is Reason.INSUFFICIENT_SUPPORT
    else:
        raise AssertionError("reading .value on a refusal must raise")
    try:
        float(o)
    except Rejected:
        pass
    else:
        raise AssertionError("float() on a refusal must raise")
    assert o.value_or(None) is None
    assert o.value_or(0.0) == 0.0


def test_refusal_reaches_a_table_cell_as_its_reason():
    o = Outcome.rejected(Reason.OUT_OF_SUPPORT_RANGE)
    assert f"{o:.2f}" == "OUT_OF_SUPPORT_RANGE"
    assert str(o) == "OUT_OF_SUPPORT_RANGE"
    good = Outcome.ok(12.3456)
    assert f"{good:.2f}" == "12.35"


def test_verdict_contract_does_not_drag_in_matplotlib():
    """Pinned after the kit failed outright inside a matplotlib-free venv.

    A project that only validates tables must still get Outcome/Reason. Run in a
    subprocess because this test module imports matplotlib itself.
    """
    import subprocess

    probe = (
        "import sys; sys.path.insert(0, %r);"
        "from analysis_kit import Outcome, Reason, graduated_verdict, Thresholds;"
        "assert 'matplotlib' not in sys.modules, 'package imported matplotlib eagerly';"
        "print('lazy-ok')" % str(Path(__file__).parent)
    )
    out = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "lazy-ok" in out.stdout


def test_support_checks():
    assert check_support(0, n_min=8) is Reason.NO_DATA
    assert check_support(3, n_min=8) is Reason.INSUFFICIENT_SUPPORT
    assert check_support(8, n_min=8) is None
    assert check_range(16.5, 12.0, 18.0) is None
    assert check_range(19.0, 12.0, 18.0) is Reason.OUT_OF_SUPPORT_RANGE
    assert check_range(float("nan"), 12.0, 18.0) is Reason.NO_DATA


def test_unknown_status_does_not_read_as_pass():
    assert status_color("PASS") != status_color("something else")
    assert status_color("something else") == status_color("NO_DATA")


# --- the linter catches what nobody opens ----------------------------------

def test_audit_requires_an_explicit_floor():
    fig = plt.figure()
    try:
        audit_figure(fig)  # type: ignore[call-arg]
    except TypeError:
        return
    finally:
        plt.close(fig)
    raise AssertionError("audit_figure ran without a stated font floor")


def test_audit_finds_an_empty_chart_and_a_small_label():
    t = tiers(0.72)
    configure(t)
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)          # drawn nothing on purpose
    ax.set_title("silent panel")
    style_axis(ax, t)
    fig.text(0.5, 0.5, "tiny caption", fontsize=5.0)

    kinds = {f.kind for f in audit_figure(fig, min_font_pt=t.floor)}
    plt.close(fig)
    assert "empty_axes" in kinds, kinds
    assert "font_below_floor" in kinds, kinds


def test_audit_finds_two_labels_written_on_each_other():
    """Found by rendering the kit's own demo, which the linter had passed clean.

    Both labels were placed with ax.text(), and the linter only scanned
    fig.texts and only compared text against charts — never text against text.
    """
    t = tiers(1.0)
    configure(t)
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    ax.plot([0, 1], [0, 1])
    ax.text(0.45, 0.5, "INSUFFICIENT_SUPPORT", fontsize=t.note, transform=ax.transAxes)
    ax.text(0.55, 0.5, "NO_DATA", fontsize=t.note, transform=ax.transAxes)

    kinds = {f.kind for f in audit_figure(fig, min_font_pt=t.floor)}
    plt.close(fig)
    assert "text_collision" in kinds, kinds


def test_axes_level_label_is_checked_against_the_floor():
    t = tiers(0.72)
    configure(t)
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    ax.plot([0, 1], [0, 1])
    ax.text(0.1, 0.9, "footnote", fontsize=5.0, transform=ax.transAxes)

    kinds = {f.kind for f in audit_figure(fig, min_font_pt=t.floor)}
    plt.close(fig)
    assert "font_below_floor" in kinds, kinds


def test_a_label_inside_its_own_axes_is_not_a_collision():
    t = tiers(1.0)
    configure(t)
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    ax.plot([0, 1], [0, 1])
    ax.text(0.5, 0.5, "chip", fontsize=t.note, transform=ax.transAxes)

    findings = audit_figure(fig, min_font_pt=t.floor)
    plt.close(fig)
    assert not findings, findings


def test_audit_is_quiet_on_a_clean_figure():
    t = tiers(1.0)
    configure(t)
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    ax.plot([0, 1, 2], [1, 2, 3])
    ax.set_title("populated")
    style_axis(ax, t)

    findings = audit_figure(fig, min_font_pt=t.floor)
    plt.close(fig)
    assert not findings, findings


def _main() -> int:
    tests = [(n, o) for n, o in sorted(globals().items())
             if n.startswith("test_") and callable(o)]
    failed = []
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - this is the reporter
            failed.append((name, exc))
            print(f"FAIL {name}: {exc}")
        else:
            print(f"ok   {name}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
