"""Build a TrueType icon font and a Flutter Dart class from a directory of SVGs.

Every source SVG is rendered to a single filled outline: stroked elements are
expanded to their outline geometry and filled elements are used as-is, then the
whole lot is unioned. That happens before the glyph is drawn, because TrueType
glyphs have no notion of a stroke.
"""

import glob
import math
import os
import xml.etree.ElementTree as ET

import svgelements
import ufo2ft
import ufoLib2
from fontTools.misc.transform import Transform
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import SVGPath
from shapely.geometry import LineString, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

from icon_generator.naming import to_dart_name, to_snake_case

UNITS_PER_EM = 1000
ASCENDER = 800
DESCENDER = -200
#: Vertical centre of the em box; glyphs are centred on it.
EM_CENTER = (ASCENDER + DESCENDER) / 2
#: Icons are scaled past the em box to match the optical size of Material Symbols.
DEFAULT_EM_SCALE = 1.15
#: First Unicode Private Use Area codepoint.
PUA_START = 0xE000

#: Vertices per viewBox unit when flattening curves. Roughly 14 font units apart.
FLATTEN_DENSITY = 3
MIN_FLATTEN_STEPS = 6
MAX_FLATTEN_STEPS = 64
#: Segments per quarter circle when buffering strokes. The shapely default of 8
#: leaves visibly faceted round caps at large display sizes.
BUFFER_QUAD_SEGS = 16

SHAPE_TYPES = (
    svgelements.Path,
    svgelements.Rect,
    svgelements.Circle,
    svgelements.Ellipse,
    svgelements.SimpleLine,
    svgelements.Polyline,
    svgelements.Polygon,
)


class IconBuildError(Exception):
    """Raised when an icon cannot be converted into glyph geometry."""


def compute_placement(width, height, em_scale=DEFAULT_EM_SCALE, units_per_em=UNITS_PER_EM):
    """Return the transform placing a ``width`` x ``height`` viewBox in the em box.

    The icon is scaled to fit the em square, multiplied by ``em_scale``, flipped
    vertically (SVG y grows downwards, font y grows upwards) and centred both
    horizontally on the em width and vertically on :data:`EM_CENTER`.
    """
    if width <= 0 or height <= 0:
        raise IconBuildError(f"Invalid viewBox dimensions: {width} x {height}")

    scale = min(units_per_em / width, units_per_em / height) * em_scale
    x_offset = (units_per_em - width * scale) / 2
    y_offset = EM_CENTER + (height * scale) / 2
    return Transform().translate(x_offset, y_offset).scale(scale, -scale)


def segment_to_points(segment, steps=None):
    """Flatten a single path segment into points, adapting to the segment length."""
    if steps is None:
        steps = _flatten_steps(segment)
    return [(p.x, p.y) for p in (segment.point(i / steps) for i in range(steps + 1))]


def _flatten_steps(segment):
    try:
        length = float(segment.length())
    except (TypeError, ValueError, ZeroDivisionError):
        length = 0.0
    if not math.isfinite(length):
        length = 0.0
    steps = math.ceil(length * FLATTEN_DENSITY)
    return max(MIN_FLATTEN_STEPS, min(MAX_FLATTEN_STEPS, steps))


def svg_element_to_shapely(element):
    """Flatten an SVG shape into one LineString per subpath.

    Subpaths closed with ``Z`` come back with their first point repeated, so the
    caller can tell a closed ring from an open stroke by comparing endpoints.
    """
    try:
        path = svgelements.Path(element)
    except Exception:
        return None

    all_geoms = []
    current_subpath = []

    for segment in path:
        if isinstance(segment, svgelements.Move):
            if len(current_subpath) >= 2:
                all_geoms.append(LineString(current_subpath))
            current_subpath = []
            p = segment.end
            current_subpath.append((p.x, p.y))
        elif isinstance(segment, svgelements.Close):
            if current_subpath:
                current_subpath.append(current_subpath[0])
                if len(current_subpath) >= 2:
                    all_geoms.append(LineString(current_subpath))
                current_subpath = []
        else:
            pts = segment_to_points(segment)
            if current_subpath:
                current_subpath.extend(pts[1:])
            else:
                current_subpath.extend(pts)

    if len(current_subpath) >= 2:
        all_geoms.append(LineString(current_subpath))

    return all_geoms


def _is_painted(color):
    """True when an svgelements paint value is an actual colour rather than ``none``."""
    return color is not None and getattr(color, "value", None) is not None


def _fill_rule(element):
    values = getattr(element, "values", None) or {}
    rule = values.get("fill-rule") or values.get("fill_rule")
    return str(rule).strip().lower() if rule else "nonzero"


def _rings_to_filled_geometry(lines, fill_rule):
    """Combine closed subpaths into a filled area honouring the SVG fill rule."""
    polygons = []
    for line in lines:
        coords = list(line.coords)
        if len(coords) < 4:
            continue
        polygon = Polygon(coords)
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
        if not polygon.is_empty:
            polygons.append(polygon)

    if not polygons:
        return None

    if fill_rule == "evenodd":
        # Even-odd: a point inside an odd number of rings is painted, so nested
        # rings knock holes out of their parent.
        area = polygons[0]
        for polygon in polygons[1:]:
            area = area.symmetric_difference(polygon)
        return area

    return unary_union(polygons)


def _element_geometry(element, weight):
    """Return the filled area an SVG element contributes, or None if it paints nothing."""
    lines = svg_element_to_shapely(element)
    if not lines:
        return None

    geometries = []

    if _is_painted(getattr(element, "fill", None)):
        filled = _rings_to_filled_geometry(lines, _fill_rule(element))
        if filled is not None and not filled.is_empty:
            geometries.append(filled)

    if _is_painted(getattr(element, "stroke", None)):
        stroke_width = weight if weight is not None else getattr(element, "stroke_width", None)
        if stroke_width is None:
            stroke_width = 1.0
        if stroke_width > 0:
            for line in lines:
                geometries.append(
                    line.buffer(
                        stroke_width / 2.0,
                        join_style=1,
                        cap_style=1,
                        quad_segs=BUFFER_QUAD_SEGS,
                    )
                )

    if not geometries:
        return None
    return unary_union(geometries)


def polygon_to_svg_path(polygon):
    """Serialise a shapely polygonal geometry back into an SVG path string."""
    path_segments = []

    def ring_to_svg(ring):
        coords = list(ring.coords)
        if not coords:
            return ""
        seg = [f"M {coords[0][0]:.3f} {coords[0][1]:.3f}"]
        for pt in coords[1:]:
            seg.append(f"L {pt[0]:.3f} {pt[1]:.3f}")
        seg.append("Z")
        return " ".join(seg)

    def polygon_to_svg(poly):
        # Consistent winding: exteriors counter-clockwise and holes clockwise in
        # SVG space, which the y-flip turns into the TrueType convention.
        poly = orient(poly, sign=1.0)
        parts = [ring_to_svg(poly.exterior)]
        parts.extend(ring_to_svg(interior) for interior in poly.interiors)
        return parts

    if polygon.geom_type == "Polygon":
        path_segments.extend(polygon_to_svg(polygon))
    elif polygon.geom_type in ("MultiPolygon", "GeometryCollection"):
        for geom in polygon.geoms:
            if geom.geom_type == "Polygon":
                path_segments.extend(polygon_to_svg(geom))

    return " ".join(filter(None, path_segments))


def outline_geometry(filepath, weight=None):
    """Return the painted area of an SVG as a single shapely geometry.

    Strokes are expanded to outlines and unioned with any filled areas, so this
    is what the icon actually covers -- the basis for both the glyph outline and
    for measuring an icon against Material's keylines.
    """
    svg = svgelements.SVG.parse(filepath)
    geometries = []

    for element in svg.elements():
        if not isinstance(element, SHAPE_TYPES):
            continue
        geometry = _element_geometry(element, weight)
        if geometry is not None and not geometry.is_empty:
            geometries.append(geometry)

    if not geometries:
        raise IconBuildError(f"'{filepath}' contains no paintable geometry")

    return unary_union(geometries)


def svg_to_outline_path(filepath, weight=None, width=24.0, height=24.0):
    """Convert an SVG file into a single filled :class:`SVGPath` ready to draw."""
    path_d = polygon_to_svg_path(outline_geometry(filepath, weight))
    if not path_d:
        raise IconBuildError(f"'{filepath}' produced empty outline geometry")

    new_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" fill="currentColor" stroke="none">'
        f'<path d="{path_d}" /></svg>'
    )
    return SVGPath.fromstring(new_svg.encode("utf-8"))


def get_svg_dimensions(filepath):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        if "viewBox" in root.attrib:
            vb = root.attrib["viewBox"].replace(",", " ").split()
            if len(vb) == 4:
                return float(vb[2]), float(vb[3])
        if "width" in root.attrib and "height" in root.attrib:
            return (
                float(root.attrib["width"].replace("px", "")),
                float(root.attrib["height"].replace("px", "")),
            )
    except Exception as e:
        print(
            f"Warning: Could not parse dimensions for {filepath}, "
            f"defaulting to 24x24. Error: {e}"
        )
    return 24.0, 24.0


def generate_dart_class(mappings, font_name, output_path):
    """Write the Flutter ``IconData`` class for ``mappings`` (name -> codepoint)."""
    dart_code = [
        "// GENERATED CODE - EDIT WITH CAUTION!!!",
        "",
        "// See https://github.com/nahpu/nahpu-icon-generator for more information.",
        "// Use the repo to generate more icons and update here.",
        "",
        "import 'package:flutter/widgets.dart';",
        "",
        f"class {font_name} {{",
        f"  {font_name}._();",
        "",
        f"  static const String _fontFamily = '{font_name}';",
        "",
    ]

    for icon_name, codepoint in sorted(mappings.items(), key=lambda item: item[1]):
        safe_name = to_dart_name(icon_name)
        dart_code.append(
            f"  static const IconData {safe_name} = "
            f"IconData({hex(codepoint)}, fontFamily: _fontFamily);"
        )

    dart_code.append("}")
    dart_code.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(dart_code))


def generate_font_and_dart(
    input_dir,
    output_font_path,
    font_name,
    weight=None,
    *,
    em_scale=DEFAULT_EM_SCALE,
    keep_going=False,
):
    """Build the icon font and its Dart class.

    Codepoints are assigned from :data:`PUA_START` in alphabetical filename
    order, so adding or removing an SVG renumbers everything after it.
    """
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return False

    svg_files = sorted(glob.glob(os.path.join(input_dir, "*.svg")))
    if not svg_files:
        print(f"No SVG files found in '{input_dir}'.")
        return False

    os.makedirs(os.path.dirname(os.path.abspath(output_font_path)), exist_ok=True)

    font = ufoLib2.Font()
    font.info.unitsPerEm = UNITS_PER_EM
    font.info.ascender = ASCENDER
    font.info.descender = DESCENDER
    font.info.familyName = font_name

    print(f"Found {len(svg_files)} SVGs. Generating font '{font_name}'...")

    notdef_glyph = font.newGlyph(".notdef")
    notdef_glyph.width = UNITS_PER_EM

    mappings = {}
    current_codepoint = PUA_START

    for filepath in svg_files:
        icon_name = os.path.splitext(os.path.basename(filepath))[0]

        width, height = get_svg_dimensions(filepath)

        glyph = font.newGlyph(icon_name)
        glyph.unicode = current_codepoint
        glyph.width = UNITS_PER_EM

        try:
            svg_path = svg_to_outline_path(filepath, weight, width, height)
            transform = compute_placement(width, height, em_scale)
            svg_path.draw(TransformPen(glyph.getPen(), transform))
        except Exception as e:
            message = f"Failed to draw path for {filepath}: {e}"
            if not keep_going:
                raise IconBuildError(message) from e
            print(f"Warning: {message}")

        if not keep_going and len(glyph) == 0:
            raise IconBuildError(f"'{filepath}' produced an empty glyph")

        mappings[icon_name] = current_codepoint
        print(f"Mapped '{icon_name}' to {hex(current_codepoint)}")
        current_codepoint += 1

    print("Compiling TTF...")
    ttf = ufo2ft.compileTTF(font, removeOverlaps=True)
    ttf.save(output_font_path)
    print(f"Success! Font saved to {output_font_path}")

    dart_output_path = os.path.join(
        os.path.dirname(os.path.abspath(output_font_path)),
        f"{to_snake_case(font_name)}.dart",
    )
    generate_dart_class(mappings, font_name, dart_output_path)
    print(f"Generated Dart class at {dart_output_path}")

    return True
