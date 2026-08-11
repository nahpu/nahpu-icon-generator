"""Build the real icon set and check the glyphs that come out the other end."""

import glob
import os

import pytest
from fontTools.ttLib import TTFont

from icon_generator.core import PUA_START, UNITS_PER_EM, generate_font_and_dart
from icon_generator.lint import FILLED_SUFFIX, OUTLINED_SUFFIX

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG_DIR = os.path.join(REPO, "svg")

#: A glyph smaller than this has collapsed into a hairline or gone missing.
MIN_EXTENT = 300
#: Nothing should exceed the em box by more than the optical overshoot allows.
MAX_EXTENT = 1300
#: The two variants of one family share a skeleton, so their boxes must agree.
PAIR_TOLERANCE = 60


@pytest.fixture(scope="session")
def icon_font(tmp_path_factory):
    output = tmp_path_factory.mktemp("font") / "icons.ttf"
    assert generate_font_and_dart(SVG_DIR, str(output), "NahpuIcons") is True
    return TTFont(str(output))


@pytest.fixture(scope="session")
def glyph_names():
    return sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(f"{SVG_DIR}/*.svg"))


def _bounds(font, name):
    glyph = font["glyf"][name]
    return glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax


def test_every_svg_becomes_a_mapped_glyph(icon_font, glyph_names):
    cmap = icon_font.getBestCmap()
    assert sorted(cmap.values()) == glyph_names
    assert sorted(cmap) == list(range(PUA_START, PUA_START + len(glyph_names)))


def test_notdef_is_present_and_empty(icon_font):
    assert icon_font["glyf"][".notdef"].numberOfContours == 0


def test_glyphs_have_contours_and_plausible_bounds(icon_font, glyph_names):
    for name in glyph_names:
        glyph = icon_font["glyf"][name]
        assert glyph.numberOfContours > 0, f"{name} has no contours"

        x_min, y_min, x_max, y_max = _bounds(icon_font, name)
        width, height = x_max - x_min, y_max - y_min
        assert MIN_EXTENT <= width <= MAX_EXTENT, f"{name} is {width} units wide"
        assert MIN_EXTENT <= height <= MAX_EXTENT, f"{name} is {height} units tall"


def test_glyphs_cover_enough_of_the_em_box(icon_font, glyph_names):
    """Catches an icon that technically drew but shrank to a sliver."""
    for name in glyph_names:
        x_min, y_min, x_max, y_max = _bounds(icon_font, name)
        area = (x_max - x_min) * (y_max - y_min)
        assert area >= 0.15 * UNITS_PER_EM**2, f"{name} covers too little of the em box"


def test_variant_pairs_share_a_bounding_box(icon_font, glyph_names):
    families = {n[: -len(OUTLINED_SUFFIX)] for n in glyph_names if n.endswith(OUTLINED_SUFFIX)}
    for family in sorted(families):
        outlined = _bounds(icon_font, family + OUTLINED_SUFFIX)
        filled = _bounds(icon_font, family + FILLED_SUFFIX)
        for axis, (a, b) in enumerate(zip(outlined, filled, strict=True)):
            assert abs(a - b) <= PAIR_TOLERANCE, (
                f"{family}: variant bounds differ on axis {axis} ({a} vs {b})"
            )


def test_all_glyphs_share_one_advance_width(icon_font, glyph_names):
    hmtx = icon_font["hmtx"]
    for name in glyph_names:
        assert hmtx[name][0] == UNITS_PER_EM
