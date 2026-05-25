import argparse
import sys
from icon_generator.core import generate_font_and_dart

def main():
    parser = argparse.ArgumentParser(description="Convert SVGs to a TTF font and Dart class for Flutter")
    parser.add_argument("--input", "-i", type=str, default="svg", help="Directory containing SVG files")
    parser.add_argument("--output", "-o", type=str, default="font-output/nahpu_font.ttf", help="Output TTF file path")
    parser.add_argument("--font-name", "-f", type=str, default="NahpuIcons", help="Font family name")
    parser.add_argument("--weight", "-w", type=float, default=1.5, help="Stroke weight for outlined icons")
    
    args = parser.parse_args()

    success = generate_font_and_dart(args.input, args.output, args.font_name, args.weight)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
