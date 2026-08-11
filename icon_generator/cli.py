"""Command line interface for the NAHPU icon font pipeline."""

import argparse
import sys

from icon_generator.core import DEFAULT_EM_SCALE, IconBuildError, generate_font_and_dart
from icon_generator.lint import run_lint
from icon_generator.specimen import SpecimenError, build_specimen

#: Flags the pre-subcommand CLI accepted. Seeing one first means an old-style call.
LEGACY_FLAGS = {"-i", "--input", "-o", "--output", "-f", "--font-name", "-w", "--weight"}
PASSTHROUGH = {"-h", "--help", "--version"}

DEFAULT_INPUT = "svg"
DEFAULT_OUTPUT = "font-output/nahpu_font.ttf"
DEFAULT_FONT_NAME = "NahpuIcons"


def build_parser():
    parser = argparse.ArgumentParser(
        prog="nahpu-icons",
        description="Build the NAHPU icon font from SVG sources and review the result.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Build the TTF font and Dart class from SVGs")
    build.add_argument("--input", "-i", default=DEFAULT_INPUT, help="Directory of SVG files")
    build.add_argument("--output", "-o", default=DEFAULT_OUTPUT, help="Output TTF path")
    build.add_argument("--font-name", "-f", default=DEFAULT_FONT_NAME, help="Font family name")
    build.add_argument(
        "--weight",
        "-w",
        type=float,
        default=None,
        help="Override every stroke width (default: honour each SVG's own stroke-width)",
    )
    build.add_argument(
        "--em-scale",
        type=float,
        default=DEFAULT_EM_SCALE,
        help="Optical size multiplier applied inside the em box",
    )
    build.add_argument(
        "--keep-going",
        action="store_true",
        help="Warn instead of failing when an icon produces no geometry",
    )
    build.add_argument(
        "--specimen",
        action="store_true",
        help="Also render the PDF specimen sheet for the font just built",
    )
    build.set_defaults(func=cmd_build)

    specimen = subparsers.add_parser(
        "specimen",
        aliases=["pdf"],
        help="Render a PDF specimen sheet of every glyph in a font",
    )
    specimen.add_argument("font", help="Path to the generated .ttf file")
    specimen.add_argument(
        "--output", "-o", default=None, help="Output PDF path (default: <font>_specimen.pdf)"
    )
    specimen.add_argument(
        "--font-name", "-f", default=None, help="Display name (default: read from the font)"
    )
    specimen.add_argument("--columns", type=int, default=4, help="Icons per grid row")
    specimen.add_argument("--glyph-size", type=float, default=48.0, help="Grid glyph size in pt")
    specimen.add_argument("--page-size", choices=["letter", "a4"], default="letter")
    specimen.add_argument(
        "--size-ramp",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Append pages showing each icon at 12-48 pt",
    )
    specimen.set_defaults(func=cmd_specimen)

    lint = subparsers.add_parser("lint", help="Check SVG sources against the design contract")
    lint.add_argument("--input", "-i", default=DEFAULT_INPUT, help="Directory of SVG files")
    lint.set_defaults(func=cmd_lint)

    return parser


def normalize_argv(argv):
    """Accept the pre-subcommand invocation by defaulting to ``build``."""
    if not argv:
        return ["build"]
    first = argv[0]
    if first in PASSTHROUGH:
        return list(argv)
    if first.split("=", 1)[0] in LEGACY_FLAGS:
        return ["build", *argv]
    return list(argv)


def cmd_build(args):
    try:
        success = generate_font_and_dart(
            args.input,
            args.output,
            args.font_name,
            args.weight,
            em_scale=args.em_scale,
            keep_going=args.keep_going,
        )
    except IconBuildError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not success:
        return 1

    if args.specimen:
        return _render_specimen(args.output)
    return 0


def cmd_specimen(args):
    return _render_specimen(
        args.font,
        output_path=args.output,
        family=args.font_name,
        columns=args.columns,
        glyph_size=args.glyph_size,
        page_size=args.page_size,
        size_ramp=args.size_ramp,
    )


def _render_specimen(font_path, **kwargs):
    try:
        output = build_specimen(font_path, **kwargs)
    except SpecimenError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(f"Specimen sheet saved to {output}")
    return 0


def cmd_lint(args):
    return 0 if run_lint(args.input) else 1


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    parser = build_parser()
    args = parser.parse_args(normalize_argv(argv))
    return args.func(args)
