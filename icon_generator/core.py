import glob
import os
import xml.etree.ElementTree as ET
import re

import ufoLib2
import ufo2ft
from fontTools.svgLib.path import SVGPath
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform
import svgelements
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

def segment_to_points(segment, steps=15):
    points = []
    for i in range(steps + 1):
        t = i / steps
        p = segment.point(t)
        points.append((p.x, p.y))
    return points

def svg_element_to_shapely(element):
    try:
        path = svgelements.Path(element)
    except Exception:
        return None
        
    all_geoms = []
    current_subpath = []
    
    for segment in path:
        if isinstance(segment, svgelements.Move):
            if current_subpath:
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
                
    if current_subpath and len(current_subpath) >= 2:
        all_geoms.append(LineString(current_subpath))
        
    return all_geoms

def polygon_to_svg_path(polygon):
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
        
    if polygon.geom_type == 'Polygon':
        path_segments.append(ring_to_svg(polygon.exterior))
        for interior in polygon.interiors:
            path_segments.append(ring_to_svg(interior))
    elif polygon.geom_type == 'MultiPolygon':
        for poly in polygon.geoms:
            path_segments.append(ring_to_svg(poly.exterior))
            for interior in poly.interiors:
                path_segments.append(ring_to_svg(interior))
                
    return " ".join(filter(None, path_segments))

def load_and_outline_svg(filepath, weight):
    if not filepath.endswith('_outlined.svg'):
        return SVGPath(filepath)
        
    svg = svgelements.SVG.parse(filepath)
    geometries_to_union = []
    
    for element in svg.elements():
        if isinstance(element, (svgelements.Path, svgelements.Rect, svgelements.Circle, svgelements.Ellipse, svgelements.Line, svgelements.Polyline, svgelements.Polygon)):
            lines = svg_element_to_shapely(element)
            if lines:
                for line in lines:
                    buffered = line.buffer(weight / 2.0, join_style=1, cap_style=1)
                    geometries_to_union.append(buffered)
                    
    if geometries_to_union:
        merged = unary_union(geometries_to_union)
        path_d = polygon_to_svg_path(merged)
        new_svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="{path_d}" /></svg>'
        return SVGPath.fromstring(new_svg.encode('utf-8'))
    else:
        return SVGPath(filepath)

def get_svg_dimensions(filepath):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        if 'viewBox' in root.attrib:
            vb = root.attrib['viewBox'].split()
            if len(vb) == 4:
                return float(vb[2]), float(vb[3])
        if 'width' in root.attrib and 'height' in root.attrib:
            return float(root.attrib['width'].replace('px', '')), float(root.attrib['height'].replace('px', ''))
    except Exception as e:
        print(f"Warning: Could not parse dimensions for {filepath}, defaulting to 24x24. Error: {e}")
    return 24.0, 24.0

def generate_dart_class(mappings, font_name, output_path):
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
        ""
    ]

    for icon_name, codepoint in mappings.items():
        # Clean up icon name to be a valid Dart variable name (lowerCamelCase)
        clean_name = "".join(c if c.isalnum() else '_' for c in icon_name)
        parts = [p for p in clean_name.split('_') if p]
        if not parts:
            safe_name = "icon"
        else:
            safe_name = parts[0].lower() + "".join(p.title() for p in parts[1:])
            
        if safe_name[0].isdigit():
            safe_name = "icon" + safe_name.title()
        
        hex_code = hex(codepoint)
        dart_code.append(f"  static const IconData {safe_name} = IconData({hex_code}, fontFamily: _fontFamily);")

    dart_code.append("}")
    dart_code.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(dart_code))

def generate_font_and_dart(input_dir, output_font_path, font_name, weight=1.5):
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return False

    svg_files = sorted(glob.glob(os.path.join(input_dir, "*.svg")))
    if not svg_files:
        print(f"No SVG files found in '{input_dir}'.")
        return False

    os.makedirs(os.path.dirname(os.path.abspath(output_font_path)), exist_ok=True)

    font = ufoLib2.Font()
    font.info.unitsPerEm = 1000
    font.info.ascender = 800
    font.info.descender = -200
    font.info.familyName = font_name

    current_codepoint = 0xE000
    
    print(f"Found {len(svg_files)} SVGs. Generating font '{font_name}'...")

    notdef_glyph = font.newGlyph(".notdef")
    notdef_glyph.width = 1000

    mappings = {}

    for filepath in svg_files:
        filename = os.path.basename(filepath)
        icon_name = os.path.splitext(filename)[0]

        width, height = get_svg_dimensions(filepath)
        
        glyph = font.newGlyph(icon_name)
        glyph.unicode = current_codepoint
        
        scale_factor_y = 1000 / height
        scale_factor_x = 1000 / width
        scale_factor = min(scale_factor_x, scale_factor_y)
        
        # Scale up by 1.15 to match the optical size of Material Design Icons (reduces excess padding)
        scale_multiplier = 1.15
        scaled_factor = scale_factor * scale_multiplier
        
        x_offset = (1000 - (width * scaled_factor)) / 2
        y_translation = 300 + 500 * scale_multiplier
        t = Transform().translate(x_offset, y_translation).scale(scaled_factor, -scaled_factor)
        
        try:
            svg_path = load_and_outline_svg(filepath, weight)
            pen = glyph.getPen()
            tpen = TransformPen(pen, t)
            svg_path.draw(tpen)
        except Exception as e:
            print(f"Warning: Failed to draw path for {filepath}. Error: {e}")
            
        glyph.width = 1000
        mappings[icon_name] = current_codepoint
        print(f"Mapped '{icon_name}' to {hex(current_codepoint)}")
        current_codepoint += 1

    print("Compiling TTF...")
    ttf = ufo2ft.compileTTF(font)
    ttf.save(output_font_path)
    print(f"Success! Font saved to {output_font_path}")

    # Convert font_name to snake_case for the filename
    dart_output_name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', font_name)
    dart_output_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', dart_output_name).lower()
    dart_output_path = os.path.join(os.path.dirname(os.path.abspath(output_font_path)), f"{dart_output_name}.dart")
    generate_dart_class(mappings, font_name, dart_output_path)
    print(f"Generated Dart class at {dart_output_path}")

    return True
