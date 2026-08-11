import pytest

from icon_generator.core import (
    DEFAULT_EM_SCALE,
    EM_CENTER,
    UNITS_PER_EM,
    IconBuildError,
    compute_placement,
)


def test_matches_the_original_hardcoded_transform():
    """The 24x24 placement must not move when it is derived from the viewBox.

    Before this was computed, the vertical offset was the literal
    ``300 + 500 * 1.15``. Every shipped icon depends on that number.
    """
    scale = (UNITS_PER_EM / 24) * DEFAULT_EM_SCALE
    expected = (scale, 0.0, 0.0, -scale, (1000 - 24 * scale) / 2, 300 + 500 * DEFAULT_EM_SCALE)
    assert tuple(compute_placement(24, 24)) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("width", "height"),
    [(24, 24), (48, 48), (24, 36), (36, 24), (16, 16)],
)
def test_icon_is_centred_in_the_em_box(width, height):
    transform = compute_placement(width, height)
    corners = [transform.transformPoint(p) for p in ((0, 0), (width, height))]
    xs = sorted(p[0] for p in corners)
    ys = sorted(p[1] for p in corners)

    assert (xs[0] + xs[1]) / 2 == pytest.approx(UNITS_PER_EM / 2)
    assert (ys[0] + ys[1]) / 2 == pytest.approx(EM_CENTER)


def test_y_axis_is_flipped():
    """SVG y grows downwards; font y grows upwards."""
    transform = compute_placement(24, 24)
    top = transform.transformPoint((12, 0))
    bottom = transform.transformPoint((12, 24))
    assert top[1] > bottom[1]


def test_em_scale_controls_the_overshoot():
    unscaled = compute_placement(24, 24, em_scale=1.0)
    corners = [unscaled.transformPoint(p) for p in ((0, 0), (24, 24))]
    ys = sorted(p[1] for p in corners)
    assert ys[1] - ys[0] == pytest.approx(UNITS_PER_EM)


@pytest.mark.parametrize(("width", "height"), [(0, 24), (24, 0), (-24, 24)])
def test_rejects_degenerate_viewboxes(width, height):
    with pytest.raises(IconBuildError):
        compute_placement(width, height)
