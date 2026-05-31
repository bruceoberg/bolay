# CLAUDE.md — bolay

A small library for laying out PDF documents from data. Wraps `fpdf2` with high-quality
typography (glyph-accurate vertical metrics, RTL/Arabic shaping), ICC-based RGB↔CMYK
color management, geometry primitives, and composable drawable elements.

This is a **git submodule** consumed by several other projects. It ships no CLI — it is
purely a library.

## Conventions

Follow the user's global rules in `~/.claude/` — tabs not spaces, Hungarian notation,
`from __future__ import annotations`. The whole library lives in one module; match its
existing style. Each class carries a `# tag = …` comment.

## Where things live

The whole library is a single module, `src/bolay/__init__.py`. Bundled ICC profiles
(sRGB2014, GRACoL, SWOP/PSO, FOGRA52, plus `adobe/`) sit in `src/bolay/icc/` and are
loaded by path relative to the package. `py.typed` marks it as typed. Build is `uv_build`,
Python ≥3.12 (`pyproject.toml`).

## What's inside

- **PDF** — `CPdf` (extends `fpdf.FPDF`): 50+ named paper formats (`s_mpStrFormatWH`),
  em-unit font metrics, glyph-bound text measurement with caching, ICC-aware color
  setters, output intents for PDF/X.
- **Color** — `SColor` (RGBA), `ICC` enum, `CColorTransformer` (RGB↔CMYK via profiles,
  cached), resaturate/darken helpers, CIELAB `L*`, named greys. `s_mpIccIccd` maps the
  `ICC` enum to the bundled profile files.
- **Geometry** — `SPoint`, `SRect` (min/max corners; Inset/Outset/Shift/Stretch),
  `RectBoundingBox`, `JH`/`JV` justification enums.
- **Typography** — `SFontKey`, `CFontInstance` (sized font + scaled metrics),
  `SVertExtents`/`VEK`/`SLimit` (choose cap-height vs descender baselines),
  `StrTextShaped`/`FHasAnyRtl` (bidi + Arabic reshaping).
- **Drawing** — `SBox` (stroke/fill/radius), `SHaloArgs` (outline-for-contrast text),
  `COneLineTextBox` (single-line shrink-to-fit + justify + halo), and `CBlot` — the
  abstract drawable base.
- **Utilities** — `IntEnum0` (auto() from 0), `EnumTuple` (fixed tuple indexed by enum).

(Symbol names above are entry points for orientation, not an inventory — grep the module
for the current set.)

## Dependencies

`fpdf2` (PDF), `pillow` (image/color), `python-bidi` + `arabic-reshaper` (RTL shaping),
`unicategories` (Unicode classification). No tests here — coverage lives in client projects.

## Editing notes

- ICC profiles are loaded by path relative to this package; keep `icc/` in the wheel.
