# nahpu-icon-generator

[![Tests](https://github.com/nahpu/nahpu-icon-generator/actions/workflows/test.yml/badge.svg)](https://github.com/nahpu/nahpu-icon-generator/actions/workflows/test.yml)

Builds the `NahpuIcons` TrueType font and its Flutter `IconData` bindings from a
directory of SVG sources, and renders a PDF specimen sheet so the icon set can
actually be reviewed. Used internally by the [NAHPU](https://github.com/nahpu/nahpu) app.

The set covers the taxa NAHPU catalogues — mammals, birds, herpetofauna,
arthropods — plus fish, vertebrate fossils, and a few specimen-handling marks.
31 families, each with an outlined and a filled variant.

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

It also checks **anatomy**. `anatomy.toml` records how many legs, antennae and
wings each family draws, and lint fails if the art disagrees — so an edit that
drops one of the spider's eight legs breaks the build instead of shipping. The
counts are of drawn elements rather than of the animal, because view and
legibility legitimately change them (a flea in profile shows three legs, not
six); entries where those differ carry a `note` explaining why. Pass
`--anatomy PATH` to check against a different manifest.

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
| Mammals | `bat`, `mouse`, `rat`, `shrew` |
| Birds | `bird` (parrot), `egg`, `nest` |
| Herps | `frog`, `salamander`, `snake`, `lizard`, `turtle` |
| Fish | `fish` |
| Fossils | `fossil` |
| Arachnids and parasites | `mite`, `tick`, `spider`, `flea`, `louse` |
| Insects | `beetle`, `butterfly`, `moth`, `ant`, `fly`, `wasp`, `dragonfly` |
| Myriapods | `millipede` |
| Specimen handling | `skull`, `bone`, `vial`, `tag` |

NAHPU's `matchCatFmtToIcon` uses `bird`, `rat`, `frog`, and `beetle` for its
four `CatalogFmt` values.

<details>
<summary>Full codepoint table</summary>

| Icon | Dart constant | Codepoint |
| --- | --- | --- |
| `ant_filled` | `NahpuIcons.antFilled` | U+E000 |
| `ant_outlined` | `NahpuIcons.antOutlined` | U+E001 |
| `bat_filled` | `NahpuIcons.batFilled` | U+E002 |
| `bat_outlined` | `NahpuIcons.batOutlined` | U+E003 |
| `beetle_filled` | `NahpuIcons.beetleFilled` | U+E004 |
| `beetle_outlined` | `NahpuIcons.beetleOutlined` | U+E005 |
| `bird_filled` | `NahpuIcons.birdFilled` | U+E006 |
| `bird_outlined` | `NahpuIcons.birdOutlined` | U+E007 |
| `bone_filled` | `NahpuIcons.boneFilled` | U+E008 |
| `bone_outlined` | `NahpuIcons.boneOutlined` | U+E009 |
| `butterfly_filled` | `NahpuIcons.butterflyFilled` | U+E00A |
| `butterfly_outlined` | `NahpuIcons.butterflyOutlined` | U+E00B |
| `dragonfly_filled` | `NahpuIcons.dragonflyFilled` | U+E00C |
| `dragonfly_outlined` | `NahpuIcons.dragonflyOutlined` | U+E00D |
| `egg_filled` | `NahpuIcons.eggFilled` | U+E00E |
| `egg_outlined` | `NahpuIcons.eggOutlined` | U+E00F |
| `fish_filled` | `NahpuIcons.fishFilled` | U+E010 |
| `fish_outlined` | `NahpuIcons.fishOutlined` | U+E011 |
| `flea_filled` | `NahpuIcons.fleaFilled` | U+E012 |
| `flea_outlined` | `NahpuIcons.fleaOutlined` | U+E013 |
| `fly_filled` | `NahpuIcons.flyFilled` | U+E014 |
| `fly_outlined` | `NahpuIcons.flyOutlined` | U+E015 |
| `fossil_filled` | `NahpuIcons.fossilFilled` | U+E016 |
| `fossil_outlined` | `NahpuIcons.fossilOutlined` | U+E017 |
| `frog_filled` | `NahpuIcons.frogFilled` | U+E018 |
| `frog_outlined` | `NahpuIcons.frogOutlined` | U+E019 |
| `lizard_filled` | `NahpuIcons.lizardFilled` | U+E01A |
| `lizard_outlined` | `NahpuIcons.lizardOutlined` | U+E01B |
| `louse_filled` | `NahpuIcons.louseFilled` | U+E01C |
| `louse_outlined` | `NahpuIcons.louseOutlined` | U+E01D |
| `millipede_filled` | `NahpuIcons.millipedeFilled` | U+E01E |
| `millipede_outlined` | `NahpuIcons.millipedeOutlined` | U+E01F |
| `mite_filled` | `NahpuIcons.miteFilled` | U+E020 |
| `mite_outlined` | `NahpuIcons.miteOutlined` | U+E021 |
| `moth_filled` | `NahpuIcons.mothFilled` | U+E022 |
| `moth_outlined` | `NahpuIcons.mothOutlined` | U+E023 |
| `mouse_filled` | `NahpuIcons.mouseFilled` | U+E024 |
| `mouse_outlined` | `NahpuIcons.mouseOutlined` | U+E025 |
| `nest_filled` | `NahpuIcons.nestFilled` | U+E026 |
| `nest_outlined` | `NahpuIcons.nestOutlined` | U+E027 |
| `rat_filled` | `NahpuIcons.ratFilled` | U+E028 |
| `rat_outlined` | `NahpuIcons.ratOutlined` | U+E029 |
| `salamander_filled` | `NahpuIcons.salamanderFilled` | U+E02A |
| `salamander_outlined` | `NahpuIcons.salamanderOutlined` | U+E02B |
| `shrew_filled` | `NahpuIcons.shrewFilled` | U+E02C |
| `shrew_outlined` | `NahpuIcons.shrewOutlined` | U+E02D |
| `skull_filled` | `NahpuIcons.skullFilled` | U+E02E |
| `skull_outlined` | `NahpuIcons.skullOutlined` | U+E02F |
| `snake_filled` | `NahpuIcons.snakeFilled` | U+E030 |
| `snake_outlined` | `NahpuIcons.snakeOutlined` | U+E031 |
| `spider_filled` | `NahpuIcons.spiderFilled` | U+E032 |
| `spider_outlined` | `NahpuIcons.spiderOutlined` | U+E033 |
| `tag_filled` | `NahpuIcons.tagFilled` | U+E034 |
| `tag_outlined` | `NahpuIcons.tagOutlined` | U+E035 |
| `tick_filled` | `NahpuIcons.tickFilled` | U+E036 |
| `tick_outlined` | `NahpuIcons.tickOutlined` | U+E037 |
| `turtle_filled` | `NahpuIcons.turtleFilled` | U+E038 |
| `turtle_outlined` | `NahpuIcons.turtleOutlined` | U+E039 |
| `vial_filled` | `NahpuIcons.vialFilled` | U+E03A |
| `vial_outlined` | `NahpuIcons.vialOutlined` | U+E03B |
| `wasp_filled` | `NahpuIcons.waspFilled` | U+E03C |
| `wasp_outlined` | `NahpuIcons.waspOutlined` | U+E03D |

</details>

## Adding an icon

1. Draw `{family}_outlined.svg` following [docs/DESIGN.md](docs/DESIGN.md), giving
   every element after the silhouette a `data-role`.
2. Copy it to `{family}_filled.svg`, changing only the root `fill` to `currentColor`.
3. Add a `[{family}]` entry to `anatomy.toml`.
4. `uv run python main.py lint`
5. `uv run python main.py build --specimen`
6. Review the icon on the size-ramp pages of the specimen sheet.
7. Commit the SVGs and `anatomy.toml` together, and regenerate the font and Dart
   class for NAHPU.

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
