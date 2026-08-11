import pytest

from icon_generator.core import PUA_START, generate_font_and_dart
from icon_generator.specimen import (
    SpecimenError,
    default_output_path,
    discover_glyphs,
    font_family_name,
)

SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"\n'
    '     fill="none" stroke="currentColor" stroke-width="2"\n'
    '     stroke-linecap="round" stroke-linejoin="round" fill-rule="evenodd">\n'
    '  <path d="M 5 5 H 19 V 19 H 5 Z" />\n'
    "</svg>\n"
)


@pytest.fixture
def tiny_font(tmp_path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "alpha_outlined.svg").write_text(SVG)
    (svg_dir / "beta_outlined.svg").write_text(SVG)

    font_path = tmp_path / "out" / "tiny.ttf"
    assert generate_font_and_dart(str(svg_dir), str(font_path), "TinyIcons") is True
    return font_path


def test_discover_glyphs_reads_names_and_codepoints(tiny_font):
    glyphs = discover_glyphs(str(tiny_font))
    assert [g.name for g in glyphs] == ["alpha_outlined", "beta_outlined"]
    assert [g.codepoint for g in glyphs] == [PUA_START, PUA_START + 1]
    assert [g.dart_name for g in glyphs] == ["alphaOutlined", "betaOutlined"]
    assert glyphs[0].codepoint_label == "U+E000"
    assert glyphs[0].char == chr(PUA_START)


def test_font_family_name_comes_from_the_font(tiny_font):
    assert font_family_name(str(tiny_font)) == "TinyIcons"


def test_discover_glyphs_rejects_a_missing_font(tmp_path):
    with pytest.raises(SpecimenError):
        discover_glyphs(str(tmp_path / "nope.ttf"))


def test_default_output_path_sits_next_to_the_font(tiny_font):
    assert default_output_path(str(tiny_font)).endswith("tiny_specimen.pdf")


def test_build_specimen_writes_a_pdf(tiny_font, tmp_path):
    pytest.importorskip("reportlab")
    from icon_generator.specimen import build_specimen

    output = tmp_path / "sheet.pdf"
    assert build_specimen(str(tiny_font), str(output)) == str(output)

    data = output.read_bytes()
    assert data.startswith(b"%PDF-")
    assert len(data) > 3000


def test_build_specimen_without_the_size_ramp_is_shorter(tiny_font, tmp_path):
    pytest.importorskip("reportlab")
    from icon_generator.specimen import build_specimen

    with_ramp = tmp_path / "with.pdf"
    without_ramp = tmp_path / "without.pdf"
    build_specimen(str(tiny_font), str(with_ramp), size_ramp=True)
    build_specimen(str(tiny_font), str(without_ramp), size_ramp=False)

    assert with_ramp.read_bytes().count(b"/Type /Page\n") > (
        without_ramp.read_bytes().count(b"/Type /Page\n")
    )
