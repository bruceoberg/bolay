import arabic_reshaper
import bidi.algorithm
import colorsys
import copy
import fpdf
import unicategories
import unicodedata

from enum import Enum, auto
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Iterable

@dataclass
class SFontKey:
	strFont: str
	strStyle: str

	def Str(self) -> str:
		return self.strFont.lower() + self.strStyle

class CPdf(fpdf.FPDF):
	s_mpStrFormatWH: dict[str, tuple[float, float]] = {
		# most sizes pulled from https://en.wikipedia.org/wiki/Paper_size
		# and converted to points (1/72nd of an inch). inches are 25.4 mm by definition.
		'letter': (612.00, 792.00),		# 8.5in x 11in
		'legal': (612.00, 1008.00),		# 8.5in x 14in
		'ledger': (792.00, 1224.00),	# 11in x 17in
		'tabloid': (792.00, 1224.00),	# 11in x 17in
		'executive': (522.00, 756.00),	# 7.25in x 10.5in
		# ANSI
		'ansi-a': (612.00, 792.00),		# 8.5in x 11in
		'ansi-b': (792.00, 1224.00),	# 11in x 17in
		'ansi-c': (1224.00, 1584.00),	# 17in x 22in
		'ansi-d': (1584.00, 2448.00),	# 22in x 34in
		'ansi-e': (2448.00, 3168.00),	# 34in x 44in
		# Architectural
		'arch-a': (648.00, 864.00),		# 9in x 12in
		'arch-b': (864.00, 1296.00),	# 12in x 18in
		'arch-c': (1296.00, 1728.00),	# 18in x 24in
		'arch-d': (1728.00, 2592.00),	# 24in x 36in
		'arch-e': (2592.00, 3456.00),	# 36in x 48in
		'arch-e1': (2160.00, 3024.00),	# 30in x 42in
		'arch-e2': (1872.00, 2736.00),	# 26in × 38in
		'arch-e3': (1944.00, 2808.00),	# 27in × 39in
		# ISO 216 https://en.wikipedia.org/wiki/ISO_216
		# fpdf.PAGE_FORMATS is wrong about a5. see https://github.com/py-pdf/fpdf2/issues/1699
		'a0': (2383.94, 3370.39),		# 841mm x 1189mm
		'a1': (1683.78, 2383.94),		# 594mm x 841mm
		'a2': (1190.55, 1683.78),		# 420mm x 594mm
		'a3': (841.89, 1190.55),		# 297mm x 420mm
		'a4': (595.28, 841.89),			# 210mm x 297mm
		'a5': (419.53, 595.28),			# 148mm x 210mm
		'a6': (297.64, 419.53),			# 105mm x 148mm
		'a7': (209.76, 297.64),			# 74mm x 105mm
		'a8': (147.40, 209.76),			# 52mm x 74mm
		'a9': (104.88, 147.40),			# 37mm x 52mm
		'a10': (73.70, 104.88),			# 26mm x 37mm
		'b0': (2834.65, 4008.19),		# 1000mm x 1414mm
		'b1': (2004.09, 2834.65),		# 707mm x 1000mm
		'b2': (1417.32, 2004.09),		# 500mm x 707mm
		'b3': (1000.63, 1417.32),		# 353mm x 500mm
		'b4': (708.66, 1000.63),		# 250mm x 353mm
		'b5': (498.90, 708.66),			# 176mm x 250mm
		'b6': (354.33, 498.90),			# 125mm x 176mm
		'b7': (249.45, 354.33),			# 88mm x 125mm
		'b8': (175.75, 249.45),			# 62mm x 88mm
		'b9': (124.72, 175.75),			# 44mm x 62mm
		'b10': (87.87, 124.72),			# 31mm x 44mm
		'c0': (2599.37, 3676.54),		# 917mm x 1297mm
		'c1': (1836.85, 2599.37),		# 648mm x 917mm
		'c2': (1298.27, 1836.85),		# 458mm x 648mm
		'c3': (918.43, 1298.27),		# 324mm x 458mm
		'c4': (649.13, 918.43),			# 229mm x 324mm
		'c5': (459.21, 649.13),			# 162mm x 229mm
		'c6': (323.15, 459.21),			# 114mm x 162mm
		'c7': (229.61, 323.15),			# 81mm x 114mm
		'c8': (161.57, 229.61),			# 57mm x 81mm
		'c9': (113.39, 161.57),			# 40mm x 57mm
		'c10': (79.37, 113.39),			# 28mm x 40mm
		# ISO 217 Raw & Special Raw https://en.wikipedia.org/wiki/ISO_217
		'ra0': (2437.80, 3458.27),		# 860mm x 1220mm
		'ra1': (1729.13, 2437.80),		# 610mm x 860mm
		'ra2': (1218.90, 1729.13),		# 430mm x 610mm
		'ra3': (864.57, 1218.90),		# 305mm x 430mm
		'ra4': (609.45, 864.57),		# 215mm x 305mm
		'sra0': (2551.18, 3628.35),		# 900mm x 1280mm
		'sra1': (1814.17, 2551.18),		# 640mm x 900mm
		'sra2': (1275.59, 1814.17),		# 450mm x 640mm
		'sra3': (907.09, 1275.59),		# 320mm x 450mm
		'sra4': (637.80, 907.09),		# 225mm x 320mm
		# photo sizes see https://en.wikipedia.org/wiki/Photo_print_sizes
		'8R': (576.00, 720.00),			# 8in x 10in
		'11R': (792.00, 1224.00),		# 11in x 14in
		'16R': (1152.00, 1440.00),		# 16in x 20in
		# convenient aliases - often offered by american print shops
		'8x10': (576.00, 720.00),		# 8in x 10in aka 8R
		'11x14': (792.00, 1224.00),		# 11in x 14in aka 11R
		'12x18': (864.00, 1296.00),		# 12in x 18in aka arch-b
		'16x20': (1152.00, 1440.00),	# 16in x 20in aka 16R
		'18x24': (1296.00, 1728.00),	# 18in x 24in aka arch-c
		'22x28': (1584.00, 2016.00),	# 22in x 28in (22R is NOT this!)
		'24x36': (1728.00, 2592.00),	# 24in x 36in aka arch-d
		'36x48': (2592.00, 3456.00),	# 36in x 48in aka arch-e
		'40x60': (2880.00, 4320.00),	# 40in x 60in office depot exclusive?
	}

	def __init__(self):
		fpdf.fpdf.PAGE_FORMATS.update(self.s_mpStrFormatWH)

		super().__init__(unit='in')

	def AddFont(self, strFontkey: str, strStyle: str, path: Path):
		self.add_font(family=strFontkey, style=strStyle, fname=str(path))

	def TuDxDyFromOrientationFmt(self, strOrientation: str, fmt: Optional[str | tuple[float, float]]) -> tuple[float, float] | None:
		if fmt is None:
			return None

		tuDxDyPt: tuple[float, float] = fpdf.fpdf.get_page_format(fmt, self.k)
		dXPt, dYPt = tuDxDyPt

		# replicating FPDF._set_orientation()

		strOrientation = strOrientation.lower()
		if strOrientation in ("p", "portrait"):
			return (dXPt / self.k, dYPt / self.k)

		assert strOrientation in ("l", "landscape")
		return (dYPt / self.k, dXPt / self.k)

class JH(Enum):
	Left = auto()
	Center = auto()
	Right = auto()

class JV(Enum):
	Bottom = auto()
	Middle = auto()
	Top = auto()

class CFontInstance:
	"""a sized font"""
	def __init__(self, pdf: CPdf, fontkey: SFontKey, dYFont: float) -> None:
		self.pdf = pdf
		self.fontkey = fontkey
		self.dYFont = dYFont
		self.dPtFont = self.dYFont * 72.0 # inches to points

		font = pdf.fonts[self.fontkey.Str()]

		try:
			desc = font['desc']
		except TypeError:
			desc = font.desc
		
		try:
			dYCapRaw = desc['CapHeight']
		except TypeError:
			dYCapRaw = desc.cap_height
		self.dYCap = dYCapRaw * self.dYFont / 1000.0

@dataclass
class SColor: # tag = color
	r: int = 0
	g: int = 0
	b: int = 0
	a: int = 255

def ColorFromStr(strColor: str, alpha: int = 255) -> SColor:
	r, g, b = fpdf.html.color_as_decimal(strColor).colors255
	return SColor(r, g, b, alpha)

colorWhite = ColorFromStr('white')
colorGrey = ColorFromStr('grey')
colorLightGrey = ColorFromStr('lightgrey')
colorDarkgrey = ColorFromStr('darkgrey')	# NOTE (bruceo) lighter than grey!
colorDarkSlateGrey = ColorFromStr('darkslategrey')
colorBlack = ColorFromStr('black')

def ColorResaturate(color: SColor, rS: float = 1.0, dS: float = 0.0, rV: float = 1.0, dV: float = 0.0) -> SColor:
	h, s, v = colorsys.rgb_to_hsv(color.r / 255.0, color.g / 255.0, color.b / 255.0)
	s = min(1.0, max(0.0, s * rS + dS))
	v = min(1.0, max(0.0, v * rV + dV))
	r, g, b = colorsys.hsv_to_rgb(h, s, v)
	return SColor(round(r * 255), round(g * 255), round(b * 255), color.a)

def FIsSaturated(color: SColor) -> bool:
	return colorsys.rgb_to_hsv(color.r / 255.0, color.g / 255.0, color.b / 255.0)[1] > 0.0

@dataclass
class SPoint: # tag = pos
	x: float = 0
	y: float = 0

	def Shift(self, dX: float = 0, dY: float = 0) -> None:
		self.x += dX
		self.y += dY

class SRect: # tag = rect
	def __init__(self, x: float = 0, y: float = 0, dX: float = 0, dY: float = 0):
		self.posMin: SPoint = SPoint(x, y)
		self.posMax: SPoint = SPoint(x + dX, y + dY)

	def Set(self, x: Optional[float] = None, y: Optional[float] = None, dX: Optional[float] = None, dY: Optional[float] = None) -> 'SRect':
		if x is not None:
			self.x = x
		if y is not None:
			self.y = y
		if dX is not None:
			self.dX = dX
		if dY is not None:
			self.dY = dY
		return self

	def Copy(self, x: Optional[float] = None, y: Optional[float] = None, dX: Optional[float] = None, dY: Optional[float] = None) -> 'SRect':
		rectNew = copy.deepcopy(self)
		rectNew.Set(x, y, dX, dY)
		return rectNew

	def __repr__(self):
		# NOTE (bruceo) avoiding property wrappers for faster debugger perf
		strVals = ', '.join([
			# NOTE (bruceo) avoiding property wrappers for faster debugger perf
			f'_x={self.posMin.x!r}',
			f'_y={self.posMin.y!r}',
			f'dX={self.posMax.x - self.posMin.x!r}',
			f'dY={self.posMax.y - self.posMin.y!r}',
			f'x_={self.posMax.x!r}',
			f'y_={self.posMax.y!r}',
		])
		return f'{type(self).__name__}({strVals})'

	@property
	def xMin(self) -> float:
		return self.posMin.x
	@xMin.setter
	def xMin(self, xNew: float) -> None:
		self.posMin.x = xNew

	@property
	def yMin(self) -> float:
		return self.posMin.y
	@yMin.setter
	def yMin(self, yNew: float) -> None:
		self.posMin.y = yNew

	@property
	def xMax(self) -> float:
		return self.posMax.x
	@xMax.setter
	def xMax(self, xNew: float) -> None:
		self.posMax.x = xNew

	@property
	def yMax(self) -> float:
		return self.posMax.y
	@yMax.setter
	def yMax(self, yNew: float) -> None:
		self.posMax.y = yNew

	@property
	def x(self) -> float:
		return self.posMin.x
	@x.setter
	def x(self, xNew: float) -> None:
		dX = xNew - self.posMin.x
		self.Shift(dX, 0)

	@property
	def y(self) -> float:
		return self.posMin.y
	@y.setter
	def y(self, yNew: float) -> None:
		dY = yNew - self.posMin.y
		self.Shift(0, dY)

	@property
	def dX(self) -> float:
		return self.posMax.x - self.posMin.x
	@dX.setter
	def dX(self, dXNew: float) -> None:
		self.posMax.x = self.posMin.x + dXNew

	@property
	def dY(self) -> float:
		return self.posMax.y - self.posMin.y
	@dY.setter
	def dY(self, dYNew: float) -> None:
		self.posMax.y = self.posMin.y + dYNew

	def Shift(self, dX: float = 0, dY: float = 0) -> 'SRect':
		self.posMin.Shift(dX, dY)
		self.posMax.Shift(dX, dY)
		return self

	def Inset(self, dS: float) -> 'SRect':
		self.posMin.Shift(dS, dS)
		self.posMax.Shift(-dS, -dS)
		return self

	def Outset(self, dS: float) -> 'SRect':
		self.Inset(-dS)
		return self

	def Stretch(self, dXLeft: float = 0, dYTop: float = 0, dXRight: float = 0, dYBottom: float = 0) -> 'SRect':
		self.posMin.Shift(dXLeft, dYTop)
		self.posMax.Shift(dXRight, dYBottom)
		return self

def RectBoundingBox(iRect: Iterable[SRect]) -> SRect:
	if not iRect:
		return SRect()
	
	iterRect = iter(iRect)
	rectReturn = next(iterRect).Copy()

	for rectNext in iterRect:
		rectReturn.xMin = min(rectReturn.xMin, rectNext.xMin)
		rectReturn.yMin = min(rectReturn.yMin, rectNext.yMin)
		rectReturn.xMax = max(rectReturn.xMax, rectNext.xMax)
		rectReturn.yMax = max(rectReturn.yMax, rectNext.yMax)

	return rectReturn

def FHasAnyRtl(strText: str) -> bool:
	for ch in strText:
		strBidi = unicodedata.bidirectional(ch)
		if strBidi in ('AL', 'R'):
			return True

	return False

@dataclass
class SHaloArgs: # tag = haloa
	color: SColor
	uPtLine: float # factor of point size for halo line

class COneLineTextBox: # tag = oltb
	"""a box with a single line of text in a particular font, sized to fit the box"""
	
	s_strControl: str = ''.join([chr(ucp) for tuMinMax in unicategories.categories['Cf'] for ucp in range(tuMinMax[0], tuMinMax[1])])
	s_transRemoveControl = str.maketrans('', '', s_strControl)

	def __init__(self, pdf: CPdf, rect: SRect, fontkey: SFontKey, dYFont: float, dSMargin: Optional[float] = None) -> None:
		self.pdf = pdf
		self.fonti = CFontInstance(pdf, fontkey, dYFont)
		self.rect = rect

		self.dYCap = self.fonti.dYCap
		self.dSMargin = dSMargin or max(0.0, (self.rect.dY - self.dYCap) / 2.0)
		self.rectMargin = self.rect.Copy().Inset(self.dSMargin)

	def RectDrawText(self, strText: str, color: SColor, jh : JH = JH.Left, jv: JV = JV.Middle, fShrinkToFit: bool = False, haloa: Optional[SHaloArgs] = None) -> SRect:
		if FHasAnyRtl(strText):
			strText = arabic_reshaper.reshape(strText)
			strText = bidi.algorithm.get_display(strText, base_dir='R')
			strText = strText.translate(self.s_transRemoveControl)

		self.pdf.set_font(self.fonti.fontkey.strFont, style=self.fonti.fontkey.strStyle, size=self.fonti.dPtFont)
		dXText = self.pdf.get_string_width(strText)

		if fShrinkToFit and dXText > self.rectMargin.dX:
			rReduce = self.rectMargin.dX / dXText
			dYFontReduced = rReduce * self.fonti.dYFont

			self.fonti = CFontInstance(self.pdf, self.fonti.fontkey, dYFontReduced)
			self.dYCap = self.fonti.dYCap

			self.pdf.set_font(self.fonti.fontkey.strFont, style=self.fonti.fontkey.strStyle, size=self.fonti.dPtFont)
			dXText = self.pdf.get_string_width(strText)

			# BB (bruceo) assert new width fits?

		rectText = SRect(0, 0, dXText, self.dYCap)

		if jh == JH.Left:
			rectText.x = self.rectMargin.x
		elif jh == JH.Center:
			rectText.x = self.rectMargin.x + (self.rectMargin.dX - rectText.dX) / 2.0
		else:
			assert jh == JH.Right
			rectText.x = self.rectMargin.x + self.rectMargin.dX - rectText.dX

		if jv == JV.Bottom:
			rectText.y = self.rectMargin.y + self.rectMargin.dY
		elif jv == JV.Middle:
			rectText.y = self.rectMargin.y + (self.rectMargin.dY + rectText.dY) / 2.0
		else:
			assert jv == JV.Top
			rectText.y = self.rectMargin.y + rectText.dY

		if haloa:
			dSLine = self.fonti.dPtFont * haloa.uPtLine
			with self.pdf.local_context(text_mode="STROKE", line_width=dSLine):
				self.pdf.set_draw_color(haloa.color.r, haloa.color.g, haloa.color.b)
				self.pdf.text(rectText.x, rectText.y, strText)

		self.pdf.set_text_color(color.r, color.g, color.b)
		self.pdf.text(rectText.x, rectText.y, strText)

		return rectText.Copy().Shift(dY = -rectText.dY)

	DrawText = RectDrawText

class CBlot: # tag = blot
	"""something drawable at a location. some blots may contain other blots."""

	def __init__(self, pdf: CPdf) -> None:
		self.pdf = pdf

	def DrawBox(self, rect: SRect, dSLine: float, color: SColor, colorFill: Optional[SColor] = None) -> None:
		if colorFill is None:
			strFillDraw = 'D'
		else:
			strFillDraw = 'FD'
			self.pdf.set_fill_color(colorFill.r, colorFill.g, colorFill.b)

		self.pdf.set_line_width(dSLine)
		self.pdf.set_draw_color(color.r, color.g, color.b)

		self.pdf.rect(rect.x, rect.y, rect.dX, rect.dY, style=strFillDraw)

	def FillBox(self, rect: SRect, color: SColor) -> None:
		self.pdf.set_fill_color(color.r, color.g, color.b)
		self.pdf.rect(rect.x, rect.y, rect.dX, rect.dY, style='F')

	def Oltb(self, rect: SRect, fontkey: SFontKey, dYFont: float, dSMargin: Optional[float] = None) ->COneLineTextBox:
		return COneLineTextBox(self.pdf, rect, fontkey, dYFont, dSMargin)

	def Draw(self, pos: SPoint) -> None:
		pass

