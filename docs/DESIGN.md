# NAHPU icon design contract

Every SVG in `svg/` follows the rules below. The mechanical ones are enforced by
`uv run python main.py lint`; the rest are judgement calls that the specimen
sheet is there to check.

## Canvas and grid

| Rule | Value |
| --- | --- |
| Canvas | `viewBox="0 0 24 24"`, `width="24" height="24"` |
| Padding / live area | 2 units on all sides, leaving a 20x20 live area |
| Skeleton box | draw **centrelines** inside `[3, 21]`, so the 2-unit stroke's outer edge lands on the keyline |
| Keylines | square 20x20; circle diameter 20 at (12, 12); vertical 16x20; horizontal 20x16 |
| Stroke width | exactly `2`, declared once on the root, never per element |
| Caps and joins | `round` / `round` |
| Quantisation | anchors on 0.5 units; control points may use 0.25 |
| Minimum counter | at least 2 units across after stroking, or it closes up at 16 px |
| Minimum gap | centrelines at least 3 units apart |
| Symmetry | mirrored pairs are exact reflections about x=12 |
| Forbidden | `transform`, `<g>`, `<use>`, `style=`, `clipPath`, `mask`, `<text>`, `<image>` |
| Allowed elements | `path`, `circle`, `ellipse`, `line`, `polyline`, `polygon`, `rect` |

Ink that crosses the canvas edge is an error. Ink that merely enters the 2-unit
padding is a warning: wide marks such as `butterfly` and `mite` are meant to
fill the grid, so the warning is informational rather than something to chase to
zero.

## The two variants

Each family ships `{family}_outlined.svg` and `{family}_filled.svg`. **They are
identical except for the root `fill` attribute**, and lint fails the build if
anything else differs.

```xml
<!-- {family}_outlined.svg -->
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
     fill="none" stroke="currentColor" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round" fill-rule="evenodd">

<!-- {family}_filled.svg -->
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
     fill="currentColor" stroke="currentColor" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round" fill-rule="evenodd">
```

This works because the builder unions filled areas with expanded strokes rather
than picking one or the other. In the outlined variant a body shape is only
stroked, so you see its outline. In the filled variant the same shape is filled
*and* stroked, so its outer edge lands in exactly the same place — the pair is
guaranteed to share a bounding box and an optical weight, and cannot drift
apart when one is edited.

`tests/test_glyphs.py` asserts the shared bounding box on the compiled font, so
the invariant is checked twice.

## How to compose an icon

An icon is built from three kinds of element:

1. **The silhouette** — one closed `<path>` that inherits the root fill. This is
   the body. Keep it a single path: separate overlapping paths would each be
   stroked in the outlined variant and show internal seams.
2. **Solid parts** — extra closed shapes (usually a `<circle>`) that also inherit
   the root fill and deliberately overlap the silhouette. They union into the
   filled variant and read as a seam — an ear on a head, a rim on a shell — in
   the outlined one. This is how `mouse` and `rat` get their ears.
3. **Details** — open paths carrying `fill="none"`, so they are stroke-only:
   legs, antennae, tails, eyes, wing veins.

Eyes are `<circle r="0.6" fill="none">`, which strokes into a solid dot in the
outlined variant and disappears into the body in the filled one. That is the
Material convention. Never use the zero-length `v.01` round-cap trick — it is
fragile under stroke expansion.

### Things that bite

- **The filled variant dilates by 1 unit in every direction.** An appendage that
  stops less than about 2.5 units beyond the body edge is swallowed whole.
  Legs, tails and beaks need real clearance.
- **Interior detail vanishes in the filled variant.** If a mark depends on an
  internal line to be recognisable, restructure it so the feature breaks the
  outline instead. `frog` puts its eyes as bulges on the silhouette for exactly
  this reason, and `fossil` carries the skeleton on a solid skull rather than
  inside a slab.
- **Shallow concavity fills in.** A notch narrower than 2 units closes under
  dilation. The gap between the frog's hind legs is 3.8 units so that roughly
  1.8 units survive.
- **`fill-rule="evenodd"` applies within a single element.** Overlapping
  subpaths of one path knock holes in each other; that is why `ant` and
  `spider` keep their body segments apart and let the strokes bridge the gap.

## Telling similar taxa apart

The single biggest failure of the previous icon set was that mite and tick, and
mouse and rat, were indistinguishable. Each mark carries a deliberate field
mark:

- **mite** round body, legs radiating evenly, no capitulum ·
  **tick** teardrop body with a forward capitulum, legs clustered on the front
  third · **spider** two-part body with long, sharply bent, high-arching legs ·
  **flea** laterally compressed teardrop with one oversized Z-shaped jumping
  leg · **louse** flat broad body, short stout hooked legs.
- **mouse** large round ear, short tail · **rat** small ear, long curling tail ·
  **shrew** no visible ear, long pointed snout.
- **snake** limbless S-coil · **lizard** S-curve with four bent legs and a long
  tail · **salamander** blunt head, smooth body, short splayed legs ·
  **frog** head-on with bulging eyes · **amphibian** frog from above (this is
  the generic herpetofauna mark NAHPU uses).
- **beetle** dorsal oval with a single centre elytra split · **butterfly** broad
  rounded wings, upper pair larger · **moth** narrower swept triangular wings ·
  **fly** two wings only · **wasp** pinched waist · **ant** three separated body
  segments · **dragonfly** long thin abdomen, four narrow wings.

## Adding an icon

1. Draw `{family}_outlined.svg`.
2. Copy it to `{family}_filled.svg` and change only the root `fill` to
   `currentColor`.
3. `uv run python main.py lint`
4. `uv run python main.py build --specimen`
5. Open the specimen sheet and check the icon on the size-ramp pages. If it is a
   smudge at 16 pt, it is not finished.
6. Commit both SVGs together.

Remember that codepoints are assigned in alphabetical filename order, so adding
a family renumbers every icon after it. See the README.
