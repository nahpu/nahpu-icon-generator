# NAHPU icon design contract

Every SVG in `svg/` follows the rules below. The mechanical ones are enforced by
`uv run python main.py lint`; the rest are judgement calls that the specimen
sheet is there to check.

## Canvas and grid

| Rule | Value |
| --- | --- |
| Canvas | `viewBox="0 0 24 24"`, `width="24" height="24"` |
| Padding / live area | 2 units on all sides, leaving a 20x20 live area (enforced) |
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

**Both bounds are errors.** Material puts a 20x20 live area inside the 24x24
grid, and every icon stays inside it. Strokes are centred on their path, so the
skeleton has to sit inside `[3, 21]` for the painted ink to land inside
`[2, 22]`.

You do not have to hit this by hand. The authoring step measures each family
**as the font builder will actually paint it** — fills unioned with expanded
strokes — then centres it on (12, 12) and scales it onto the Material keyline.
The lint check is the backstop.

Material sets different keylines by shape, because a solid square reads larger
than a circle inside the same box: **18 units for a shape that fills its
bounding box, 20 for a circular one.** The authoring step interpolates between
them using the ink's actual coverage of its bounding box, so the set stays
optically even instead of drifting between sizes. Before this existed the icons
ranged from 15.9 to 20 units and looked like a jumble.

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

Eyes are **filled, not stroked**:

```xml
<circle data-role="eye" fill="currentColor" stroke="none" cx="16" cy="13.8" r="0.75" />
```

A stroked circle is centred on its path, so it renders as a tiny donut with a
pinhole rather than a dot. Material draws the eye as a solid disc about 1.5
units across, which is what `r="0.75"` filled gives. An eye socket that is meant
to read as a *hole* — `skull`, `fossil` — is the opposite: a stroked ring with a
radius large enough that the counter survives.

Never use the zero-length `v.01` round-cap trick; it is fragile under stroke
expansion.

### Roles

Every element **after** the silhouette carries a `data-role`, drawn from:

`leg` · `wing` · `antenna` · `eye` · `ear` · `tail` · `head` · `detail`

`data-*` attributes are valid XML and ignored by every renderer, `svgelements`
and the font pipeline included — these files never reach Flutter. They exist so
`anatomy.toml` can be checked mechanically. `detail` is the catch-all for
everything that is not a countable body part: an elytra split, a mouth line, a
gill, a rib, a shell rim, a wing strut.

## Anatomy

NAHPU is a natural-history app, so the icons are read by people who know what
the animals look like. `anatomy.toml` records how many legs, antennae and wings
each family draws, and `main.py lint` verifies it against the sources.

The counts are of **drawn elements**, not of the animal's real anatomy, because
the two diverge for three legitimate reasons:

- **View.** A flea in lateral profile shows three legs, not six.
- **Silhouette.** A feature drawn into the silhouette path cannot be counted — a
  butterfly's wings are part of its outline, so `wings = 0` there. **Any limb
  that has to be counted must be a stroked element.** A limb drawn as a
  silhouette lobe is invisible to the check.
- **Legibility.** The winged insects (`fly`, `wasp`, `butterfly`, `moth`,
  `dragonfly`) omit legs deliberately; six legs under those wings is mud at
  16 px. Those entries carry a `note` saying so, which is the point of the file:
  an omission becomes a recorded decision instead of something indistinguishable
  from an oversight.

Getting a count wrong is a lint **error**, so a future edit that drops a spider
leg fails the build rather than shipping.

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
  dilation, so a gap you want to survive needs to start at about 3.8 units.
- **`fill-rule="evenodd"` applies within a single element.** Overlapping
  subpaths of one path knock holes in each other; that is why `ant` and
  `spider` keep their body segments apart and let the strokes bridge the gap.

## View convention

Vertebrates are drawn in **lateral profile wherever a side view is
recognisable** — `bird`, `mouse`, `rat`, `shrew`, `lizard`, `salamander`,
`fish`, `fossil`, `skull`.

**Dorsal or head-on only where that is the diagnostic view**: `turtle` from
above, `snake` as a coil, and `frog` and `bat` head-on. A bat in profile is a
lump; with its wings spread it is unmistakable. The same is true of a frog's
face.

Some marks are **shape-led**: `mouse`, `rat` and `shrew` draw no limbs at all,
because at 24 px four leg strokes fight with the body outline instead of
supporting it. Body proportion, ear size and tail carry the identification, and
`anatomy.toml` records `legs = 0` with a note so the omission is on the record.

The view drives the limb count, which is why `anatomy.toml` counts what is drawn
rather than what the animal has.

## Telling similar taxa apart

The single biggest failure of the original icon set was that mite and tick, and
mouse and rat, were indistinguishable. Each mark carries a deliberate field
mark:

- **mite** round idiosoma, eight legs swept forward and back, no capitulum ·
  **tick** teardrop idiosoma with a forward capitulum and its eight legs
  clustered on the front third · **spider** two-part body with eight long,
  sharply bent legs, all on the cephalothorax ·
  **flea** laterally compressed teardrop with one oversized Z-shaped jumping
  leg · **louse** flat broad body, short stout hooked legs.
- **mouse** large round ear, short tail · **rat** small ear, long curling tail ·
  **shrew** no visible ear, long pointed snout.
- **snake** limbless S-coil · **lizard** S-curve, four bent legs, tail longer
  than the trunk · **salamander** blunt head, smooth body, four sprawling legs ·
  **frog** head-on with bulging eyes and folded hind limbs (this is the
  herpetofauna mark NAHPU uses).
- **bird** is a parrot in lateral profile: crest, hooked bill and a tail longer
  than the body.
- **bat** head-on, wings spread on elongated finger struts — the struts are what
  separate a bat wing from a moth wing at this size.
- **beetle** dorsal oval with a single centre elytra split · **butterfly** broad
  rounded wings, upper pair larger · **moth** narrower swept triangular wings ·
  **fly** two wings only · **wasp** pinched waist · **ant** three separated body
  segments · **dragonfly** long thin abdomen, four narrow wings.

## Adding an icon

1. Draw `{family}_outlined.svg`, giving every element after the silhouette a
   `data-role`.
2. Copy it to `{family}_filled.svg` and change only the root `fill` to
   `currentColor`.
3. Add a `[{family}]` entry to `anatomy.toml` with the legs, antennae and wings
   the mark draws, plus a `note` if any of those counts is not what the animal
   actually has.
4. `uv run python main.py lint`
5. `uv run python main.py build --specimen`
6. Open the specimen sheet and check the icon on the size-ramp pages. If it is a
   smudge at 16 pt, it is not finished.
7. Commit both SVGs and `anatomy.toml` together.

Remember that codepoints are assigned in alphabetical filename order, so adding
a family renumbers every icon after it. See the README.
