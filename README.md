# nahpu-icon-generator

[![Tests](https://github.com/nahpu/nahpu-icon-generator/actions/workflows/test.yml/badge.svg)](https://github.com/nahpu/nahpu-icon-generator/actions/workflows/test.yml)

Generate a TrueType font (`.ttf`) from a directory of SVG files. Used internally for the NAHPU app to create custom Flutter icon fonts.

## Requirements
This project uses `uv` for dependency management.

## Usage

1. Place your `.svg` files inside the `svg/` directory.
2. Run the command-line application:

```bash
uv run python main.py --input svg --output font-output/icon_font.ttf --font-name NahpuIcons
```

The script will:
- Map each SVG to a Unicode Private Use Area (PUA) codepoint starting from `U+E000` sequentially.
- Generate a TrueType Font file (`icon_font.ttf`) in the output directory.
- Automatically generate a Dart class file (`nahpuicons.dart`) containing the `IconData` mappings, ready to be used in your Flutter project.

## Using the Font in Flutter

To use the generated font in your Flutter application, follow these steps:

### 1. Add the font to your `pubspec.yaml`
Copy the generated `icon_font.ttf` to your Flutter project's assets directory (e.g., `assets/fonts/`) and register it in your `pubspec.yaml`:

```yaml
flutter:
  fonts:
    - family: NahpuIcons
      fonts:
        - asset: assets/fonts/icon_font.ttf
```

### 2. Include the Dart Class
Copy the generated `nahpuicons.dart` file into your Flutter project's `lib/` directory. This file already contains all the correct static constants mapping to the generated Unicode codepoints.

### 3. Display the Icon
Use it inside your Flutter widgets just like any standard `Icon` using the static constants provided by the generated class:

```dart
import 'path/to/nahpuicons.dart';

Icon(
  NahpuIcons.my_custom_icon,
  size: 24.0,
  color: Colors.black,
)
```

## Testing

This project includes automated unit tests using `pytest`.
To run the test suite:

```bash
uv run pytest
```
