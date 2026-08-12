import pytest

from icon_generator.cli import main, normalize_argv

SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"\n'
    '     fill="none" stroke="currentColor" stroke-width="2"\n'
    '     stroke-linecap="round" stroke-linejoin="round" fill-rule="evenodd">\n'
    '  <path d="M 5 5 H 19 V 19 H 5 Z" />\n'
    "</svg>\n"
)


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        ([], ["build"]),
        (["--input", "svg"], ["build", "--input", "svg"]),
        (["-i", "svg", "-o", "a.ttf"], ["build", "-i", "svg", "-o", "a.ttf"]),
        (["--output=a.ttf"], ["build", "--output=a.ttf"]),
        (["build", "-i", "svg"], ["build", "-i", "svg"]),
        (["specimen", "a.ttf"], ["specimen", "a.ttf"]),
        (["lint"], ["lint"]),
        (["--help"], ["--help"]),
    ],
)
def test_legacy_invocations_still_reach_build(argv, expected):
    assert normalize_argv(argv) == expected


def _fixture_anatomy(tmp_path, family="alpha"):
    """A one-family manifest, so lint checks the fixture rather than the real set."""
    path = tmp_path / "anatomy.toml"
    path.write_text(f"[{family}]\nlegs = 0\nantennae = 0\nwings = 0\n")
    return str(path)


def test_build_and_lint_round_trip(tmp_path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "alpha_outlined.svg").write_text(SVG)
    (svg_dir / "alpha_filled.svg").write_text(SVG.replace('fill="none"', 'fill="currentColor"', 1))

    output = tmp_path / "out" / "icons.ttf"
    assert main(["build", "-i", str(svg_dir), "-o", str(output)]) == 0
    assert output.exists()
    assert (tmp_path / "out" / "nahpu_icons.dart").exists()
    assert main(["lint", "-i", str(svg_dir), "-a", _fixture_anatomy(tmp_path)]) == 0


def test_lint_fails_when_the_manifest_does_not_cover_the_set(tmp_path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "alpha_outlined.svg").write_text(SVG)
    (svg_dir / "alpha_filled.svg").write_text(SVG.replace('fill="none"', 'fill="currentColor"', 1))

    anatomy = _fixture_anatomy(tmp_path, family="beta")
    assert main(["lint", "-i", str(svg_dir), "-a", anatomy]) == 1


def test_build_fails_on_a_missing_input_directory(tmp_path):
    assert main(["build", "-i", str(tmp_path / "nope"), "-o", str(tmp_path / "a.ttf")]) == 1


def test_lint_fails_on_an_unpaired_icon(tmp_path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "alpha_outlined.svg").write_text(SVG)
    assert main(["lint", "-i", str(svg_dir), "-a", _fixture_anatomy(tmp_path)]) == 1


def test_specimen_reports_a_missing_font(tmp_path):
    assert main(["specimen", str(tmp_path / "nope.ttf")]) == 1
