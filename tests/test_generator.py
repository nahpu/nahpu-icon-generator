import os
import pytest
from icon_generator.core import get_svg_dimensions, generate_font_and_dart

@pytest.fixture
def dummy_svg(tmp_path):
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <path d="M12 2L2 22h20L12 2z"/>
</svg>"""
    file_path = tmp_path / "dummy.svg"
    file_path.write_text(svg_content)
    return file_path

@pytest.fixture
def dummy_svg_dir(tmp_path):
    svg_dir = tmp_path / "svgs"
    svg_dir.mkdir()
    
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M12 2L2 22h20L12 2z"/>
</svg>"""
    
    (svg_dir / "icon_one.svg").write_text(svg_content)
    (svg_dir / "icon_two.svg").write_text(svg_content)
    return svg_dir

def test_get_svg_dimensions(dummy_svg):
    width, height = get_svg_dimensions(str(dummy_svg))
    assert width == 24.0
    assert height == 24.0

def test_get_svg_dimensions_no_viewbox(tmp_path):
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="48px" height="48px">
  <path d="M12 2L2 22h20L12 2z"/>
</svg>"""
    file_path = tmp_path / "no_viewbox.svg"
    file_path.write_text(svg_content)
    
    width, height = get_svg_dimensions(str(file_path))
    assert width == 48.0
    assert height == 48.0

def test_generate_font_and_dart(dummy_svg_dir, tmp_path):
    output_font = tmp_path / "output" / "my_font.ttf"
    
    success = generate_font_and_dart(str(dummy_svg_dir), str(output_font), "TestIcons")
    
    assert success is True
    assert output_font.exists()
    
    # Check that Dart file was generated
    dart_file = tmp_path / "output" / "testicons.dart"
    assert dart_file.exists()
    
    dart_content = dart_file.read_text()
    assert "class TestIcons" in dart_content
    assert "static const IconData iconOne = IconData(" in dart_content
    assert "static const IconData iconTwo = IconData(" in dart_content

def test_generate_empty_dir(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    
    output_font = tmp_path / "output" / "my_font.ttf"
    success = generate_font_and_dart(str(empty_dir), str(output_font), "TestIcons")
    
    assert success is False
    assert not output_font.exists()
