"""Check the shipped SVG sources against the design contract in docs/DESIGN.md."""

import glob
import os

import pytest

from icon_generator.lint import lint_directory, lint_file

SVG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "svg")
SVG_FILES = sorted(glob.glob(os.path.join(SVG_DIR, "*.svg")))


def test_the_icon_set_is_not_empty():
    assert SVG_FILES, "no SVG sources found"


@pytest.mark.parametrize("path", SVG_FILES, ids=lambda p: os.path.basename(p))
def test_source_satisfies_the_design_contract(path):
    errors, _ = lint_file(path)
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
