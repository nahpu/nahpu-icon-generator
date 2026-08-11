"""Validate SVG sources against the icon design contract.

The rules encoded here are the mechanically checkable half of ``docs/DESIGN.md``:
canvas size, the fixed root attribute set per variant, the constructs the font
pipeline cannot represent, and the live-area bounds.
"""

import glob
import os
import xml.etree.ElementTree as ET

import svgelements

SVG_NS = "http://www.w3.org/2000/svg"

CANVAS = 24.0
#: Nothing may be painted outside the canvas.
HARD_MIN, HARD_MAX = 0.0, CANVAS
#: Ink outside the 2-unit padding is legal but warned about.
LIVE_MIN, LIVE_MAX = 2.0, CANVAS - 2.0

OUTLINED_SUFFIX = "_outlined"
FILLED_SUFFIX = "_filled"

#: Both variants share every root attribute except `fill`, so an outlined and a
#: filled icon can never drift out of alignment with each other.
COMMON_ROOT_ATTRS = {
    "width": "24",
    "height": "24",
    "viewBox": "0 0 24 24",
    "stroke": "currentColor",
    "stroke-width": "2",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
    "fill-rule": "evenodd",
}

ROOT_FILL = {"outlined": "none", "filled": "currentColor"}

ALLOWED_TAGS = {
    "path",
    "circle",
    "ellipse",
    "line",
    "polyline",
    "polygon",
    "rect",
}

FORBIDDEN_TAGS = {"g", "use", "clipPath", "mask", "text", "image", "defs", "style"}
FORBIDDEN_ATTRS = {"transform", "style", "class", "clip-path", "mask", "filter"}

SHAPE_TYPES = (
    svgelements.Path,
    svgelements.Rect,
    svgelements.Circle,
    svgelements.Ellipse,
    svgelements.SimpleLine,
    svgelements.Polyline,
    svgelements.Polygon,
)


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _variant(stem):
    if stem.endswith(OUTLINED_SUFFIX):
        return "outlined"
    if stem.endswith(FILLED_SUFFIX):
        return "filled"
    return None


def _family(stem):
    for suffix in (OUTLINED_SUFFIX, FILLED_SUFFIX):
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem


def check_root_attributes(root, variant, errors):
    expected = dict(COMMON_ROOT_ATTRS, fill=ROOT_FILL[variant])
    actual = {k: v for k, v in root.attrib.items() if _local(k) != "xmlns"}

    for key, value in expected.items():
        if key not in actual:
            errors.append(f"root is missing {key}=\"{value}\"")
        elif actual[key].split() != value.split():
            errors.append(f'root has {key}="{actual[key]}", expected "{value}"')

    for key in sorted(set(actual) - set(expected)):
        errors.append(f'root has unexpected attribute {key}="{actual[key]}"')


def check_elements(root, errors):
    for element in root.iter():
        tag = _local(element.tag)
        if element is root:
            continue
        if tag in FORBIDDEN_TAGS:
            errors.append(f"<{tag}> is not allowed")
            continue
        if tag not in ALLOWED_TAGS:
            errors.append(f"<{tag}> is not an allowed element")
        for attr in element.attrib:
            if _local(attr) in FORBIDDEN_ATTRS:
                errors.append(f"<{tag}> uses the forbidden attribute {_local(attr)}")


def check_bounds(filepath, errors, warnings):
    """Check that painted ink, stroke included, stays on the canvas."""
    try:
        svg = svgelements.SVG.parse(filepath)
    except Exception as e:
        errors.append(f"could not be parsed by svgelements: {e}")
        return

    painted = None
    for element in svg.elements():
        if not isinstance(element, SHAPE_TYPES):
            continue
        try:
            bbox = element.bbox()
        except Exception:
            bbox = None
        if bbox is None:
            continue

        stroke = getattr(element, "stroke", None)
        pad = 0.0
        if stroke is not None and getattr(stroke, "value", None) is not None:
            pad = (getattr(element, "stroke_width", 0.0) or 0.0) / 2.0

        box = (bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad)
        if painted is None:
            painted = box
        else:
            painted = (
                min(painted[0], box[0]),
                min(painted[1], box[1]),
                max(painted[2], box[2]),
                max(painted[3], box[3]),
            )

    if painted is None:
        errors.append("contains no paintable geometry")
        return

    tol = 0.01
    if (
        painted[0] < HARD_MIN - tol
        or painted[1] < HARD_MIN - tol
        or painted[2] > HARD_MAX + tol
        or painted[3] > HARD_MAX + tol
    ):
        errors.append(
            "ink escapes the 24x24 canvas: "
            f"({painted[0]:.2f}, {painted[1]:.2f}) - ({painted[2]:.2f}, {painted[3]:.2f})"
        )
    elif (
        painted[0] < LIVE_MIN - tol
        or painted[1] < LIVE_MIN - tol
        or painted[2] > LIVE_MAX + tol
        or painted[3] > LIVE_MAX + tol
    ):
        warnings.append(
            "ink enters the 2-unit padding: "
            f"({painted[0]:.2f}, {painted[1]:.2f}) - ({painted[2]:.2f}, {painted[3]:.2f})"
        )


def lint_file(filepath):
    """Return ``(errors, warnings)`` for a single SVG source file."""
    errors, warnings = [], []
    stem = os.path.splitext(os.path.basename(filepath))[0]

    variant = _variant(stem)
    if variant is None:
        errors.append(f"name must end in {OUTLINED_SUFFIX} or {FILLED_SUFFIX}")
        return errors, warnings

    try:
        root = ET.parse(filepath).getroot()
    except ET.ParseError as e:
        errors.append(f"is not well-formed XML: {e}")
        return errors, warnings

    if _local(root.tag) != "svg":
        errors.append(f"root element is <{_local(root.tag)}>, expected <svg>")
        return errors, warnings

    check_root_attributes(root, variant, errors)
    check_elements(root, errors)
    check_bounds(filepath, errors, warnings)
    return errors, warnings


def lint_directory(input_dir):
    """Lint every SVG in ``input_dir``.

    Returns ``(results, pairing_errors)`` where ``results`` maps each file path to
    its ``(errors, warnings)`` tuple.
    """
    svg_files = sorted(glob.glob(os.path.join(input_dir, "*.svg")))
    results = {path: lint_file(path) for path in svg_files}

    stems = {os.path.splitext(os.path.basename(p))[0] for p in svg_files}
    pairing_errors = []
    for stem in sorted(stems):
        variant = _variant(stem)
        if variant is None:
            continue
        family = _family(stem)
        counterpart = family + (FILLED_SUFFIX if variant == "outlined" else OUTLINED_SUFFIX)
        if counterpart not in stems:
            pairing_errors.append(f"'{stem}' has no matching '{counterpart}.svg'")
        elif variant == "outlined":
            pairing_errors.extend(check_pair_identity(input_dir, family))

    return results, pairing_errors


def check_pair_identity(input_dir, family):
    """The two variants must differ only in the root ``fill`` attribute.

    Enforcing this structurally is what keeps a filled icon on exactly the same
    skeleton, and therefore the same bounding box, as its outlined twin.
    """
    outlined = os.path.join(input_dir, f"{family}{OUTLINED_SUFFIX}.svg")
    filled = os.path.join(input_dir, f"{family}{FILLED_SUFFIX}.svg")
    try:
        with open(outlined) as f:
            outlined_text = f.read()
        with open(filled) as f:
            filled_text = f.read()
    except OSError as e:
        return [f"could not compare the '{family}' pair: {e}"]

    normalized = filled_text.replace('fill="currentColor"', 'fill="none"', 1)
    if normalized != outlined_text:
        return [
            f"'{family}_filled.svg' differs from '{family}_outlined.svg' by more than "
            "the root fill attribute"
        ]
    return []


def run_lint(input_dir):
    """Print a lint report for ``input_dir``. Returns True when there are no errors."""
    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return False

    results, pairing_errors = lint_directory(input_dir)
    if not results:
        print(f"No SVG files found in '{input_dir}'.")
        return False

    error_count = 0
    warning_count = 0

    for path, (errors, warnings) in results.items():
        name = os.path.basename(path)
        for message in errors:
            print(f"error: {name}: {message}")
        for message in warnings:
            print(f"warning: {name}: {message}")
        error_count += len(errors)
        warning_count += len(warnings)

    for message in pairing_errors:
        print(f"error: {message}")
    error_count += len(pairing_errors)

    print(
        f"\nLinted {len(results)} files: {error_count} error(s), {warning_count} warning(s)."
    )
    return error_count == 0
