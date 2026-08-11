"""Render a PDF specimen sheet for a generated icon font.

The sheet is the review artifact for the icon set: every glyph is drawn from the
font itself at display size with its name, Dart constant and codepoint, followed
by a size ramp that shows how each icon holds up as it shrinks.
"""

import os
from dataclasses import dataclass
from datetime import date

from fontTools.ttLib import TTFont

from icon_generator.naming import to_dart_name

#: Point sizes shown on the size-ramp pages, smallest first.
RAMP_SIZES = (12, 16, 20, 24, 32, 48)
#: Internal reportlab alias for the icon font; the display name comes from the font.
FONT_ALIAS = "IconFont"
MARGIN = 36.0
LABEL_FONT = "Helvetica"
MONO_FONT = "Courier"
#: How far a glyph reaches above and below its baseline, as a fraction of the
#: point size. Icons overshoot the em box (see core.DEFAULT_EM_SCALE), so these
#: are the real ink extents rather than the nominal ascender and descender.
GLYPH_TOP_RATIO = 0.88
GLYPH_BOTTOM_RATIO = 0.28
LABEL_LEADING = 10.0


class SpecimenError(Exception):
    """Raised when a specimen sheet cannot be produced."""


@dataclass(frozen=True)
class GlyphEntry:
    """One glyph as it appears on the sheet."""

    name: str
    codepoint: int
    dart_name: str

    @property
    def char(self):
        return chr(self.codepoint)

    @property
    def codepoint_label(self):
        return f"U+{self.codepoint:04X}"


def _require_reportlab():
    try:
        import reportlab.pdfgen.canvas  # noqa: F401
    except ImportError as e:  # pragma: no cover - exercised only without the extra
        raise SpecimenError(
            "The specimen sheet needs reportlab. Install it with: uv sync --extra specimen"
        ) from e


def discover_glyphs(font_path):
    """Read the icon glyphs out of a font's cmap, sorted by codepoint.

    Glyph names are the SVG file stems, so the cmap alone carries everything the
    sheet needs.
    """
    if not os.path.exists(font_path):
        raise SpecimenError(f"Font file '{font_path}' does not exist.")

    font = TTFont(font_path)
    cmap = font.getBestCmap()
    if not cmap:
        raise SpecimenError(f"Font file '{font_path}' has no usable cmap.")

    return [
        GlyphEntry(name=name, codepoint=codepoint, dart_name=to_dart_name(name))
        for codepoint, name in sorted(cmap.items())
    ]


def font_family_name(font_path):
    """Return the font's typographic family name, falling back to the file stem."""
    font = TTFont(font_path)
    name_table = font["name"] if "name" in font else None
    if name_table is not None:
        for name_id in (16, 1):
            record = name_table.getDebugName(name_id)
            if record:
                return record
    return os.path.splitext(os.path.basename(font_path))[0]


def default_output_path(font_path):
    stem = os.path.splitext(os.path.abspath(font_path))[0]
    return f"{stem}_specimen.pdf"


def build_specimen(
    font_path,
    output_path=None,
    *,
    family=None,
    columns=4,
    glyph_size=48.0,
    page_size="letter",
    size_ramp=True,
):
    """Render the specimen sheet and return the path it was written to."""
    _require_reportlab()

    glyphs = discover_glyphs(font_path)
    family = family or font_family_name(font_path)
    output_path = output_path or default_output_path(font_path)

    output_dir = os.path.dirname(os.path.abspath(output_path))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    render_specimen(
        font_path,
        output_path,
        glyphs=glyphs,
        family=family,
        columns=columns,
        glyph_size=glyph_size,
        page_size=page_size,
        size_ramp=size_ramp,
    )
    return output_path


def render_specimen(
    font_path,
    output_path,
    *,
    glyphs,
    family,
    columns=4,
    glyph_size=48.0,
    page_size="letter",
    size_ramp=True,
):
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont as PdfTTFont
    from reportlab.pdfgen import canvas as pdfcanvas

    if not glyphs:
        raise SpecimenError("The font contains no glyphs to render.")
    if columns < 1:
        raise SpecimenError("--columns must be at least 1.")

    pdfmetrics.registerFont(PdfTTFont(FONT_ALIAS, font_path))

    page = A4 if page_size == "a4" else letter
    pdf = pdfcanvas.Canvas(output_path, pagesize=page)
    pdf.setTitle(f"{family} specimen")

    layout = _GridLayout(page, columns, glyph_size)
    grid_pages = _paginate(glyphs, layout)
    ramp_chunks = _ramp_chunks(page, glyphs) if size_ramp else []
    total_pages = len(grid_pages) + len(ramp_chunks)

    page_number = _draw_grid_pages(
        pdf, layout, grid_pages, glyphs, family, font_path, glyph_size, total_pages
    )
    _draw_ramp_pages(pdf, page, ramp_chunks, family, page_number, total_pages)

    pdf.save()


class _GridLayout:
    """Cell geometry for the glyph grid."""

    def __init__(self, page, columns, glyph_size):
        self.page_width, self.page_height = page
        self.columns = columns
        self.glyph_size = glyph_size
        self.cell_width = (self.page_width - 2 * MARGIN) / columns
        self.glyph_gap = 10.0
        self.cell_height = (
            self.glyph_gap
            + (GLYPH_TOP_RATIO + GLYPH_BOTTOM_RATIO) * glyph_size
            + 4 * LABEL_LEADING
        )
        self.header_height = 54.0
        self.footer_height = 24.0

    def glyph_baseline(self, cell_top):
        return cell_top - self.glyph_gap - GLYPH_TOP_RATIO * self.glyph_size

    def first_label_y(self, cell_top):
        return self.glyph_baseline(cell_top) - GLYPH_BOTTOM_RATIO * self.glyph_size - LABEL_LEADING

    def rows(self, with_header):
        usable = self.page_height - 2 * MARGIN - self.footer_height
        if with_header:
            usable -= self.header_height
        return max(1, int(usable // self.cell_height))

    def cell_top(self, row, with_header):
        top = self.page_height - MARGIN
        if with_header:
            top -= self.header_height
        return top - row * self.cell_height

    def cell_center_x(self, column):
        return MARGIN + (column + 0.5) * self.cell_width


def _draw_header(pdf, layout, family, glyphs, font_path):
    from reportlab.lib import colors

    x = MARGIN
    y = layout.page_height - MARGIN - 18
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(x, y, family)

    span = f"U+{glyphs[0].codepoint:04X}–U+{glyphs[-1].codepoint:04X}"
    subtitle = (
        f"{len(glyphs)} glyphs  ·  {span}  ·  "
        f"{os.path.basename(font_path)}  ·  {date.today().isoformat()}"
    )
    pdf.setFont(LABEL_FONT, 9)
    pdf.setFillColor(colors.HexColor("#666666"))
    pdf.drawString(x, y - 16, subtitle)

    pdf.setStrokeColor(colors.HexColor("#cccccc"))
    pdf.setLineWidth(0.5)
    pdf.line(MARGIN, y - 28, layout.page_width - MARGIN, y - 28)


def _draw_footer(pdf, page_width, page_number, total_pages):
    from reportlab.lib import colors

    pdf.setFont(LABEL_FONT, 8)
    pdf.setFillColor(colors.HexColor("#999999"))
    pdf.drawCentredString(page_width / 2, MARGIN - 12, f"page {page_number} of {total_pages}")


def _paginate(glyphs, layout):
    """Split glyphs into per-page chunks; the first page is shorter for the header."""
    pages = []
    index = 0
    first = True
    while index < len(glyphs):
        per_page = layout.rows(with_header=first) * layout.columns
        pages.append((glyphs[index : index + per_page], first))
        index += per_page
        first = False
    return pages


def _draw_grid_pages(pdf, layout, pages, glyphs, family, font_path, glyph_size, total_pages):
    """Draw the glyph grid. Returns the number of the next page."""
    page_number = 1
    for chunk, with_header in pages:
        if with_header:
            _draw_header(pdf, layout, family, glyphs, font_path)

        for position, entry in enumerate(chunk):
            row, column = divmod(position, layout.columns)
            _draw_cell(pdf, layout, entry, row, column, with_header, glyph_size)

        _draw_footer(pdf, layout.page_width, page_number, total_pages)
        pdf.showPage()
        page_number += 1
    return page_number


def _draw_cell(pdf, layout, entry, row, column, with_header, glyph_size):
    from reportlab.lib import colors

    top = layout.cell_top(row, with_header)
    center_x = layout.cell_center_x(column)

    pdf.setStrokeColor(colors.HexColor("#eeeeee"))
    pdf.setLineWidth(0.25)
    pdf.rect(
        MARGIN + column * layout.cell_width,
        top - layout.cell_height,
        layout.cell_width,
        layout.cell_height,
        stroke=1,
        fill=0,
    )

    pdf.setFillColor(colors.black)
    pdf.setFont(FONT_ALIAS, glyph_size)
    pdf.drawCentredString(center_x, layout.glyph_baseline(top), entry.char)

    label_y = layout.first_label_y(top)
    pdf.setFont(LABEL_FONT, 8)
    pdf.drawCentredString(center_x, label_y, entry.name)

    pdf.setFillColor(colors.HexColor("#777777"))
    pdf.setFont(MONO_FONT, 7)
    pdf.drawCentredString(center_x, label_y - LABEL_LEADING, entry.dart_name)
    pdf.drawCentredString(center_x, label_y - 2 * LABEL_LEADING, entry.codepoint_label)


def _ramp_geometry(page):
    page_width, page_height = page
    row_height = max(RAMP_SIZES) + 14.0
    ramp_left = MARGIN + 108.0
    column_width = (page_width - MARGIN - ramp_left) / len(RAMP_SIZES)
    header_height = 46.0
    usable = page_height - 2 * MARGIN - header_height
    rows_per_page = max(1, int(usable // row_height))
    return row_height, ramp_left, column_width, header_height, rows_per_page


def _ramp_chunks(page, glyphs):
    _, _, _, _, rows_per_page = _ramp_geometry(page)
    return [glyphs[i : i + rows_per_page] for i in range(0, len(glyphs), rows_per_page)]


def _draw_ramp_pages(pdf, page, chunks, family, page_number, total_pages):
    """Draw each icon at every size in RAMP_SIZES, one icon per row."""
    from reportlab.lib import colors

    page_width, page_height = page
    row_height, ramp_left, column_width, header_height, _ = _ramp_geometry(page)

    for ramp_index, chunk in enumerate(chunks, start=1):
        top = page_height - MARGIN
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(MARGIN, top - 12, f"{family} — size ramp ({ramp_index}/{len(chunks)})")

        pdf.setFont(LABEL_FONT, 7)
        pdf.setFillColor(colors.HexColor("#666666"))
        for index, size in enumerate(RAMP_SIZES):
            pdf.drawCentredString(
                ramp_left + (index + 0.5) * column_width, top - 30, f"{size} pt"
            )

        pdf.setStrokeColor(colors.HexColor("#cccccc"))
        pdf.setLineWidth(0.5)
        pdf.line(MARGIN, top - 38, page_width - MARGIN, top - 38)

        for row, entry in enumerate(chunk):
            baseline = top - header_height - (row + 1) * row_height + 12
            pdf.setFillColor(colors.HexColor("#333333"))
            pdf.setFont(LABEL_FONT, 7)
            pdf.drawString(MARGIN, baseline, entry.name)

            pdf.setFillColor(colors.black)
            for index, size in enumerate(RAMP_SIZES):
                pdf.setFont(FONT_ALIAS, size)
                pdf.drawCentredString(
                    ramp_left + (index + 0.5) * column_width, baseline, entry.char
                )

        _draw_footer(pdf, page_width, page_number, total_pages)
        pdf.showPage()
        page_number += 1
