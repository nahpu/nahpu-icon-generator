# nahpu-icon-generator

[![Tests](https://github.com/nahpu/nahpu-icon-generator/actions/workflows/test.yml/badge.svg)](https://github.com/nahpu/nahpu-icon-generator/actions/workflows/test.yml)

Builds the `NahpuIcons` TrueType font and its Flutter `IconData` bindings from a
directory of SVG sources, and renders a PDF specimen sheet so the icon set can
actually be reviewed. Used internally by the [NAHPU](https://github.com/nahpu/nahpu) app.

The set covers the taxa NAHPU catalogues — mammals, birds, herpetofauna,
arthropods — plus fish, vertebrate fossils, and a few specimen-handling marks.
33 families, each with an outlined and a filled variant.

## Requirements

This project uses `uv` for dependency management. The specimen sheet needs the
optional `reportlab` dependency:

```bash
uv sync --all-extras --dev
```

## Usage

### Build the font

```bash
uv run python main.py build --input svg --output font-output/nahpu_font.ttf --font-name NahpuIcons
```

This maps each SVG to a Private Use Area codepoint from `U+E000`, compiles the
TTF, and writes the matching Dart class next to it. Pass `--specimen` to render
the PDF in the same run.

Useful flags:

- `--weight N` — override every stroke width. By default each SVG's own
  `stroke-width` is honoured.
- `--em-scale N` — optical size multiplier inside the em box (default `1.15`).
- `--keep-going` — warn instead of failing when an icon produces no geometry.

The old flag-only invocation (`main.py --input svg --output ...`) still works
and is treated as `build`.

### Render the specimen sheet

```bash
uv run python main.py specimen font-output/nahpu_font.ttf --size-ramp
```

Takes any icon font as input and produces a PDF containing:

- a grid of every glyph at 48 pt with its icon name, Dart constant, and codepoint;
- a header giving the family name, glyph count, codepoint span, and build date;
- size-ramp pages showing each icon at 12 / 16 / 20 / 24 / 32 / 48 pt.

The size ramp is the page that matters. An icon whose counters close up or whose
strokes merge at 16 pt is not finished. Use `--no-size-ramp` to skip it,
`--columns` and `--glyph-size` to change the grid, and `--page-size a4` for A4.

### Lint the sources

```bash
uv run python main.py lint
```

Checks every SVG against the design contract: canvas size, the exact root
attribute set, constructs the font pipeline cannot represent, ink staying on the
canvas, and that each outlined icon has a filled twin differing only in the root
`fill`. See [docs/DESIGN.md](docs/DESIGN.md) for the full contract.

## Codepoints renumber when the set changes

Codepoints are assigned in **alphabetical filename order** starting at `U+E000`.
Adding or removing a family shifts every icon after it.

This means the generated `nahpu_icons.dart` must be copied into NAHPU
**wholesale**, never merged, and the font and the Dart file must always ship
together. A font that is one build behind its Dart class renders the wrong
animals rather than failing loudly.

## Icon roster

| Group | Families |
| --- | --- |
| Mammals | `bat`, `mouse`, `rat`, `shrew`, `mammal` |
| Birds | `bird`, `egg`, `nest` |
| Herps | `amphibian`, `frog`, `salamander`, `snake`, `lizard`, `turtle` |
| Fish | `fish` |
| Fossils | `fossil` |
| Arachnids and parasites | `mite`, `tick`, `spider`, `flea`, `louse` |
| Insects | `beetle`, `butterfly`, `moth`, `ant`, `fly`, `wasp`, `dragonfly` |
| Myriapods | `millipede` |
| Specimen handling | `skull`, `bone`, `vial`, `tag` |

NAHPU's `matchCatFmtToIcon` currently uses `bird`, `rat`, `amphibian`, and
`mite` for its four `CatalogFmt` values.

<details>
<summary>Full codepoint table</summary>

| Icon | Dart constant | Codepoint |
| --- | --- | --- |
| `amphibian_filled` | `NahpuIcons.amphibianFilled` | U+E000 |
| `amphibian_outlined` | `NahpuIcons.amphibianOutlined` | U+E001 |
| `ant_filled` | `NahpuIcons.antFilled` | U+E002 |
| `ant_outlined` | `NahpuIcons.antOutlined` | U+E003 |
| `bat_filled` | `NahpuIcons.batFilled` | U+E004 |
| `bat_outlined` | `NahpuIcons.batOutlined` | U+E005 |
| `beetle_filled` | `NahpuIcons.beetleFilled` | U+E006 |
| `beetle_outlined` | `NahpuIcons.beetleOutlined` | U+E007 |
| `bird_filled` | `NahpuIcons.birdFilled` | U+E008 |
| `bird_outlined` | `NahpuIcons.birdOutlined` | U+E009 |
| `bone_filled` | `NahpuIcons.boneFilled` | U+E00A |
| `bone_outlined` | `NahpuIcons.boneOutlined` | U+E00B |
| `butterfly_filled` | `NahpuIcons.butterflyFilled` | U+E00C |
| `butterfly_outlined` | `NahpuIcons.butterflyOutlined` | U+E00D |
| `dragonfly_filled` | `NahpuIcons.dragonflyFilled` | U+E00E |
| `dragonfly_outlined` | `NahpuIcons.dragonflyOutlined` | U+E00F |
| `egg_filled` | `NahpuIcons.eggFilled` | U+E010 |
| `egg_outlined` | `NahpuIcons.eggOutlined` | U+E011 |
| `fish_filled` | `NahpuIcons.fishFilled` | U+E012 |
| `fish_outlined` | `NahpuIcons.fishOutlined` | U+E013 |
| `flea_filled` | `NahpuIcons.fleaFilled` | U+E014 |
| `flea_outlined` | `NahpuIcons.fleaOutlined` | U+E015 |
| `fly_filled` | `NahpuIcons.flyFilled` | U+E016 |
| `fly_outlined` | `NahpuIcons.flyOutlined` | U+E017 |
| `fossil_filled` | `NahpuIcons.fossilFilled` | U+E018 |
| `fossil_outlined` | `NahpuIcons.fossilOutlined` | U+E019 |
| `frog_filled` | `NahpuIcons.frogFilled` | U+E01A |
| `frog_outlined` | `NahpuIcons.frogOutlined` | U+E01B |
| `lizard_filled` | `NahpuIcons.lizardFilled` | U+E01C |
| `lizard_outlined` | `NahpuIcons.lizardOutlined` | U+E01D |
| `louse_filled` | `NahpuIcons.louseFilled` | U+E01E |
| `louse_outlined` | `NahpuIcons.louseOutlined` | U+E01F |
| `mammal_filled` | `NahpuIcons.mammalFilled` | U+E020 |
| `mammal_outlined` | `NahpuIcons.mammalOutlined` | U+E021 |
| `millipede_filled` | `NahpuIcons.millipedeFilled` | U+E022 |
| `millipede_outlined` | `NahpuIcons.millipedeOutlined` | U+E023 |
| `mite_filled` | `NahpuIcons.miteFilled` | U+E024 |
| `mite_outlined` | `NahpuIcons.miteOutlined` | U+E025 |
| `moth_filled` | `NahpuIcons.mothFilled` | U+E026 |
| `moth_outlined` | `NahpuIcons.mothOutlined` | U+E027 |
| `mouse_filled` | `NahpuIcons.mouseFilled` | U+E028 |
| `mouse_outlined` | `NahpuIcons.mouseOutlined` | U+E029 |
| `nest_filled` | `NahpuIcons.nestFilled` | U+E02A |
| `nest_outlined` | `NahpuIcons.nestOutlined` | U+E02B |
| `rat_filled` | `NahpuIcons.ratFilled` | U+E02C |
| `rat_outlined` | `NahpuIcons.ratOutlined` | U+E02D |
| `salamander_filled` | `NahpuIcons.salamanderFilled` | U+E02E |
| `salamander_outlined` | `NahpuIcons.salamanderOutlined` | U+E02F |
| `shrew_filled` | `NahpuIcons.shrewFilled` | U+E030 |
| `shrew_outlined` | `NahpuIcons.shrewOutlined` | U+E031 |
| `skull_filled` | `NahpuIcons.skullFilled` | U+E032 |
| `skull_outlined` | `NahpuIcons.skullOutlined` | U+E033 |
| `snake_filled` | `NahpuIcons.snakeFilled` | U+E034 |
| `snake_outlined` | `NahpuIcons.snakeOutlined` | U+E035 |
| `spider_filled` | `NahpuIcons.spiderFilled` | U+E036 |
| `spider_outlined` | `NahpuIcons.spiderOutlined` | U+E037 |
| `tag_filled` | `NahpuIcons.tagFilled` | U+E038 |
| `tag_outlined` | `NahpuIcons.tagOutlined` | U+E039 |
| `tick_filled` | `NahpuIcons.tickFilled` | U+E03A |
| `tick_outlined` | `NahpuIcons.tickOutlined` | U+E03B |
| `turtle_filled` | `NahpuIcons.turtleFilled` | U+E03C |
| `turtle_outlined` | `NahpuIcons.turtleOutlined` | U+E03D |
| `vial_filled` | `NahpuIcons.vialFilled` | U+E03E |
| `vial_outlined` | `NahpuIcons.vialOutlined` | U+E03F |
| `wasp_filled` | `NahpuIcons.waspFilled` | U+E040 |
| `wasp_outlined` | `NahpuIcons.waspOutlined` | U+E041 |

</details>

## Adding an icon

1. Draw `{family}_outlined.svg` following [docs/DESIGN.md](docs/DESIGN.md).
2. Copy it to `{family}_filled.svg`, changing only the root `fill` to `currentColor`.
3. `uv run python main.py lint`
4. `uv run python main.py build --specimen`
5. Review the icon on the size-ramp pages of the specimen sheet.
6. Commit both SVGs together, and regenerate the font and Dart class for NAHPU.

## Using the font in Flutter

### 1. Register the font

Copy the generated `nahpu_font.ttf` into your Flutter project's assets and
register it:

```yaml
flutter:
  fonts:
    - family: NahpuIcons
      fonts:
        - asset: assets/fonts/nahpu_font.ttf
```

### 2. Copy the Dart class

Copy the generated `nahpu_icons.dart` into your project. NAHPU keeps it at
`lib/services/types/nahpu_icons.dart`. Replace the file wholesale — see the
codepoint note above.

### 3. Use it

```dart
import 'package:nahpu/services/types/nahpu_icons.dart';

Icon(
  NahpuIcons.fishOutlined,
  size: 24.0,
  color: Colors.black,
)
```

## How the build works

Source SVGs are parsed with `svgelements`. For each element, filled areas become
shapely polygons and stroked paths are buffered out to their outline; everything
is unioned into a single filled region, which is what gets drawn into the glyph.
That is why an icon can mix fills and strokes freely, and why the outlined and
filled variants of a family land on exactly the same bounding box.

Glyphs are placed at 1000 units per em, scaled to fit and multiplied by
`--em-scale` to match the optical size of Material Symbols, then centred on the
em box. Overlaps are removed by `ufo2ft` via `skia-pathops`.

## Testing

```bash
uv run pytest
```

The suite covers glyph placement, the SVG design contract, the compiled glyphs
(every glyph has contours, plausible bounds, and matches its variant twin), the
specimen sheet, and the CLI.
