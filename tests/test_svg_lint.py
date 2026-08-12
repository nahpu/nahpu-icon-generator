"""Check the shipped SVG sources against the design contract in docs/DESIGN.md."""

import glob
import os

import pytest

from icon_generator.lint import COUNTED_ROLES, lint_directory, lint_file, load_anatomy

SVG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "svg")
SVG_FILES = sorted(glob.glob(os.path.join(SVG_DIR, "*.svg")))
ANATOMY = load_anatomy()


def test_the_icon_set_is_not_empty():
    assert SVG_FILES, "no SVG sources found"


@pytest.mark.parametrize("path", SVG_FILES, ids=lambda p: os.path.basename(p))
def test_source_satisfies_the_design_contract(path):
    errors, _ = lint_file(path, ANATOMY)
    assert not errors, "; ".join(errors)


def test_every_icon_has_both_variants_and_the_pair_matches():
    _, pairing_errors = lint_directory(SVG_DIR)
    assert not pairing_errors, "; ".join(pairing_errors)


def test_rejects_a_forbidden_construct(tmp_path):
    path = tmp_path / "thing_outlined.svg"
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" fill-rule="evenodd">'
        '<g><path transform="scale(2)" d="M 4 4 H 20" /></g></svg>'
    )
    errors, _ = lint_file(str(path))
    assert any("<g>" in e for e in errors)
    assert any("transform" in e for e in errors)


def test_rejects_ink_outside_the_canvas(tmp_path):
    path = tmp_path / "thing_outlined.svg"
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" fill-rule="evenodd">'
        '<path d="M 4 4 H 30" /></svg>'
    )
    errors, _ = lint_file(str(path))
    assert any("escapes the 24x24 canvas" in e for e in errors)


def test_rejects_a_wrong_root_attribute(tmp_path):
    path = tmp_path / "thing_outlined.svg"
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round" fill-rule="evenodd">'
        '<path d="M 4 4 H 20" /></svg>'
    )
    errors, _ = lint_file(str(path))
    assert any("stroke-width" in e for e in errors)


ROLE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round" fill-rule="evenodd">'
    '<path d="M 8 8 H 16 V 16 H 8 Z" />'
    "{elements}</svg>"
)


def _write(tmp_path, name, elements):
    path = tmp_path / name
    path.write_text(ROLE_SVG.format(elements=elements))
    return str(path)


def test_anatomy_covers_every_family():
    """Every family in svg/ has an entry, and no entry is left behind."""
    families = {
        os.path.basename(p).rsplit("_", 1)[0] for p in SVG_FILES
    }
    assert set(ANATOMY) == families

    for family, spec in ANATOMY.items():
        for field in COUNTED_ROLES:
            assert field in spec, f"anatomy.toml [{family}] is missing '{field}'"
            assert isinstance(spec[field], int), f"[{family}].{field} must be an int"


def test_wrong_leg_count_is_an_error(tmp_path):
    """The check that stops a dropped spider leg from shipping."""
    path = _write(
        tmp_path,
        "thing_outlined.svg",
        '<path data-role="leg" fill="none" d="M 8 12 L 4 12" />',
    )
    errors, _ = lint_file(path, {"thing": {"legs": 4, "antennae": 0, "wings": 0}})
    assert any("draws 1 legs but anatomy.toml [thing] declares 4" in e for e in errors)


def test_matching_counts_pass(tmp_path):
    path = _write(
        tmp_path,
        "thing_outlined.svg",
        '<path data-role="leg" fill="none" d="M 8 12 L 4 12" />'
        '<path data-role="antenna" fill="none" d="M 12 8 L 12 4" />',
    )
    errors, _ = lint_file(path, {"thing": {"legs": 1, "antennae": 1, "wings": 0}})
    assert not errors, "; ".join(errors)


def test_missing_role_is_an_error(tmp_path):
    path = _write(tmp_path, "thing_outlined.svg", '<path fill="none" d="M 8 12 L 4 12" />')
    errors, _ = lint_file(path, {"thing": {"legs": 0, "antennae": 0, "wings": 0}})
    assert any("has no data-role" in e for e in errors)


def test_unknown_role_is_an_error(tmp_path):
    path = _write(
        tmp_path,
        "thing_outlined.svg",
        '<path data-role="flipper" fill="none" d="M 8 12 L 4 12" />',
    )
    errors, _ = lint_file(path, {"thing": {"legs": 0, "antennae": 0, "wings": 0}})
    assert any("unknown data-role" in e for e in errors)


def test_family_missing_from_the_manifest_is_an_error(tmp_path):
    path = _write(tmp_path, "thing_outlined.svg", "")
    errors, _ = lint_file(path, {})
    assert any("has no entry in anatomy.toml" in e for e in errors)
