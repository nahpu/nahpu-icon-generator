"""Name conversions shared by the font builder and the specimen renderer."""

import re


def to_dart_name(icon_name: str) -> str:
    """Convert an icon name (SVG file stem) to a lowerCamelCase Dart identifier.

    ``bird_outlined`` becomes ``birdOutlined``. Non-alphanumeric characters are
    treated as word separators, and a leading digit is prefixed so the result is
    always a valid Dart identifier.
    """
    cleaned = "".join(c if c.isalnum() else "_" for c in icon_name)
    parts = [p for p in cleaned.split("_") if p]
    if not parts:
        return "icon"

    name = parts[0].lower() + "".join(p.title() for p in parts[1:])
    if name[0].isdigit():
        name = "icon" + name.title()
    return name


def to_snake_case(name: str) -> str:
    """Convert a CamelCase font name to snake_case, e.g. ``NahpuIcons`` -> ``nahpu_icons``."""
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()
