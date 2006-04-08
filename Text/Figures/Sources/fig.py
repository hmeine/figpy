"""'fig' module - object-oriented interface to XFig files.

You can read fig files into an object 'f' with
  f = fig.File(filename) # or pass a file-like object"""

_cvsVersion = "$Id$" \
              .split(" ")[2:-2]

import sys, string, re, math, types, os

# object codes
figCustomColor   = 0
figEllipse       = 1
figPolygon       = 2
figSpline        = 3
figText          = 4
figArc           = 5
figCompoundBegin = 6
figCompoundEnd   = -6

# polygon types
ptPolyline    = 1
ptBox         = 2
ptPolygon     = 3
ptArcBox      = 4
ptPictureBBox = 5

# ellipse types
etEllipseRadii    = 1
etEllipseDiameter = 2
etCircleRadius    = 3
etCircleDiameter  = 4

# spline types
stClosedApproximated = 1
stOpenInterpolated   = 2
stClosedInterpolated = 3
stOpenXSpline        = 4
stClosedXSpline      = 5

# arc types
atPie  = 0
atOpen = 1

# fill styles
fillStyleNone    = -1
fillStyleBlack   = 0
fillStyleSolid   = 20
fillStyleStripes = 42 # obsolete
def fillStyleShaded(percent): # 0 = black .. 100 = fillColor (5% steps)
	return int(percent) / 5
def fillStyleTinted(percent): # 0 = fillColor .. 100 = white (5% steps)
	return 20 + int(percent) / 5
fillStyleLeft30    = 41 # 30 degree left diagonal pattern
fillStyleRight30   = 42 # 30 degree right diagonal pattern
fillStyleCrossed30 = 44 # 30 degree cross-hatched pattern
fillStyleLeft45    = 44 # 45 degree left diagonal pattern
fillStyleRight45   = 45 # 45 degree right diagonal pattern
fillStyleCrossed45 = 46 # 45 degree cross-hatched pattern

# line styles
lineStyleDefault          = -1
lineStyleSolid            = 0
lineStyleDashed           = 1
lineStyleDotted           = 2
lineStyleDashDotted       = 3
lineStyleDashDoubleDotted = 4
lineStyleDashTripleDotted = 5

standardColors = [
	# pure colors:
	(0, 0, 0),
	(0, 0, 255),
	(0, 255, 0),
	(0, 255, 255),
	(255, 0, 0),
	(255, 0, 255),
	(255, 255, 0),
	(255, 255, 255),
	# four blues:
	(0, 0, 144),
	(0, 0, 176),
	(0, 0, 208),
	(135, 206, 255),
	# three greens:
	(0, 144, 0),
	(0, 176, 0),
	(0, 208, 0),
	# three cyans:
	(0, 144, 144),
	(0, 176, 176),
	(0, 208, 208),
	# three reds:
	(144, 0, 0),
	(176, 0, 0),
	(208, 0, 0),
	# three magentas:
	(144, 0, 144),
	(176, 0, 176),
	(208, 0, 208),
	# three browns:
	(128, 48, 0),
	(160, 64, 0),
	(192, 96, 0),
	# four pinks:
	(255, 128, 128),
	(255, 160, 160),
	(255, 192, 192),
	(255, 224, 224),
	# gold:
	(255, 215, 0),
	]

# colors
colorDefault   = -1
colorBlack     = 0
colorBlue      = 1
colorGreen     = 2
colorCyan      = 3
colorRed       = 4
colorMagenta   = 5
colorYellow    = 6
colorWhite     = 7
colorBlue4     = 8
colorBlue3     = 9
colorBlue2     = 10
colorLightBlue = 11
colorGreen4    = 12
colorGreen3    = 13
colorGreen2    = 14
colorCyan4     = 15
colorCyan3     = 16
colorCyan2     = 17
colorRed4      = 18
colorRed3      = 19
colorRed2      = 20
colorMagenta4  = 21
colorMagenta3  = 22
colorMagenta2  = 23
colorBrown4    = 24
colorBrown3    = 25
colorBrown2    = 26
colorPink4     = 27
colorPink3     = 28
colorPink2     = 29
colorLightPink = 30
colorGold      = 31
colorCustom0   = 32

# join styles
joinStyleMiter = 0
joinStyleBevel = 1
joinStyleRound = 2

# alignments
alignLeft     = 0
alignCentered = 1
alignRight    = 2

# fonts
fontDefault   = 0
fontHelvetica = 16

# font flags
ffRigid      = 1
ffSpecial    = 2
ffPostScript = 4
ffHidden     = 8

paperSizes = ["Letter", "Legal", "Ledger", "Tabloid",
			  "A", "B", "C", "D", "E",
			  "A4", "A3", "A2", "A1", "A0", "B5"]

def _join(*sequence):
	parts = []
	for item in sequence:
		if type(item) == float:
			parts.append(str(int(round(item))))
		elif type(item) == bool:
			parts.append(str(int(item)))
		else:
			parts.append(str(item))
	return string.join(parts, " ")

re_size = re.compile("([0-9]+)x([0-9]+)")
re_geometry = re.compile("([0-9]+)[:,]([0-9]+)([+-:,])([0-9]+)([x:,])([0-9]+)")

def parseSize(sizeStr):
	ma = re_size.match(sizeStr)
	if ma:
		w = int(ma.group(1))
		h = int(ma.group(2))
		return (w, h)

def parseGeometry(geometryString):
	ma = re_geometry.match(geometryString)
	if ma:
		x1 = int(ma.group(1))
		y1 = int(ma.group(2))
		vx2 = int(ma.group(4))
		vy2 = int(ma.group(6))
		if ma.group(3) == "+" or ma.group(5) == "x":
			return ((x1, y1), (x1+vx2, y1+vy2))
		else:
			return ((x1, y1), (vx2, vy2))

class _Rect(object):
	def __init__(self):
		self.empty = 1

	def __call__(self, other):
		if type(other) == _Rect:
			self.__call__((other.x1, other.y1))
			self.__call__((other.x2, other.y2))
		else:
			if self.empty:
				self.x1 = other[0]
				self.x2 = other[0]
				self.y1 = other[1]
				self.y2 = other[1]
				self.empty = False
			else:
				self.x1 = min(self.x1, other[0])
				self.y1 = min(self.y1, other[1])
				self.x2 = max(self.x2, other[0])
				self.y2 = max(self.y2, other[1])

	def width(self):
		return self.x2 - self.x1

	def height(self):
		return self.y2 - self.y1

	def __str__(self):
		return "%d,%d,%d,%d" % (self.x1, self.y1, self.x2, self.y2)

class CustomColor(object):
	def __init__(self, index, hexCode):
		self.index = index
		self.hexCode = hexCode
		#sys.stderr.write("CustomColor(%d, '%s') -> %s" % (index, hexCode, repr(self)))

	def __repr__(self):
		return _join(figCustomColor, self.index, self.hexCode) + "\n"

	def __str__(self):
		return str(self.index)

	def __int__(self):
		return self.index

	def __cmp__(self, other):
		if other == None:
			return 1
		if other.isinstance(other, CustomColor):
			return cmp(self.index, other.index)
		return cmp(self.index, other)

	def __getitem__(self, index):
		return int(self.hexCode[2*index+1:2*index+3], 16)

	def rgb(self):
		return (self[0], self[1], self[2])

	def setRGB(self, r, g, b):
		self.hexCode = "#%02x%02x%02x" % (r, g, b)

class Object(object):
	"""Base class of all fig objects, handles common properties like
	- lineStyle (see lineStyleXXX constants)
	- lineWidth (1/80th inch)
	- styleValue (dash length / dot gap ratio) in 1/80th inches)
	- penColor, fillColor, fillStyle
	- depth (0-999)
	- joinStyle and capStyle
	- forwardArrow/backwardArrow (the latter are Arrow objects)"""
	def __init__(self, type):
		self.type = type
		self.subType = None
		self.lineStyle = lineStyleDefault
		self.lineWidth = 1
		self.penColor = colorDefault
		self.fillColor = colorDefault
		self.depth = 50
		self.penStyle = 0 # not used
		self.fillStyle = fillStyleNone
		self.styleValue = 3.0
		self.joinStyle = 0
		self.capStyle = 0
		self.radius = -1
		self.forwardArrow = None
		self.backwardArrow = None

class Arrow(object):
	def __init__(self, params):
		self.params = params

	def __str__(self):
		return _join(*self.params) + "\n"

class ArcBase(Object):
	def __init__(self):
		Object.__init__(self, figArc)
		self.points = []

	def __str__(self):
		hasForwardArrow = (self.forwardArrow != None and 1 or 0)
		hasBackwardArrow = (self.backwardArrow != None and 1 or 0)
		
		result = _join(self.type, self.subType,
					   self.lineStyle, self.lineWidth,
					   self.penColor, self.fillColor,
					   self.depth, self.penStyle,
					   self.fillStyle, self.lineStyle > 0 and self.styleValue or 0.0,
					   self.capStyle, self.direction,
					   hasForwardArrow, hasBackwardArrow,
					   self.centerX, self.centerY,
					   self.points[0][0], self.points[0][1],
					   self.points[1][0], self.points[1][1],
					   self.points[2][0], self.points[2][1]) + "\n"

		if hasForwardArrow:
			result += "\t" + str(self.forwardArrow)
		if hasBackwardArrow:
			result += "\t" + str(self.backwardArrow)
		return result

	def bounds(self):
		result = _Rect()
		for point in self.points:
			result(point)
		return result

	def _readSub(self, params):
		if self.forwardArrow == True:
			self.forwardArrow = Arrow(params)
			return self.backwardArrow == True

		if self.backwardArrow == True:
			self.backwardArrow = Arrow(params)
			return False

		sys.stderr.write("Unhandled subline while loading arc object!\n")
		return False

def _readArcBase(params):
	result = ArcBase()
	result.subType = int(params[0])
	result.lineStyle = int(params[1])
	result.lineWidth = int(params[2])
	result.penColor = int(params[3])
	result.fillColor = int(params[4])
	result.depth = int(params[5])
	result.penStyle = int(params[6])
	result.fillStyle = int(params[7])
	result.styleValue = float(params[8])
	result.capStyle = int(params[9])
	result.direction = int(params[10])
	subLines = 0
	if int(params[11]):
		result.forwardArrow = True
		subLines += 1
	if int(params[12]):
		result.backwardArrow = True
		subLines += 1
	result.centerX = float(params[13])
	result.centerY = float(params[14])
	result.points = [(int(params[15]), int(params[16])),
					 (int(params[17]), int(params[18])),
					 (int(params[19]), int(params[20]))]
	return result, subLines

class EllipseBase(Object):
	def __init__(self):
		Object.__init__(self, figEllipse)
		self.angle = 0.0
		self.center = (0, 0)
		self.radius = (0, 0)
		self.start = (0, 0)
		self.end = (0, 0)

	def __str__(self):
		return _join(self.type, self.subType,
					 self.lineStyle, self.lineWidth,
					 self.penColor, self.fillColor,
					 self.depth, self.penStyle,
					 self.fillStyle, self.styleValue,
					 1, # "1" is self.direction
					 self.angle,
					 self.center[0], self.center[1],
					 self.radius[0], self.radius[1],
					 self.start[0], self.start[1],
					 self.end[0], self.end[1]) + "\n"

	def bounds(self):
		result = _Rect()
		result(((self.center[0] - self.radius[0]),
				(self.center[1] - self.radius[1])))
		result(((self.center[0] + self.radius[0]),
				(self.center[1] + self.radius[1])))
		return result

	def setCenterRadius(self, center, radius):
		self.center = center
		self.radius = radius
		self.start = self.center
		self.end = (self.center[0] + radius[0],
					self.center[1] + radius[1])


def _readEllipseBase(params):
	result = EllipseBase()
	result.subType = int(params[0])
	result.lineStyle = int(params[1])
	result.lineWidth = int(params[2])
	result.penColor = int(params[3])
	result.fillColor = int(params[4])
	result.depth = int(params[5])
	result.penStyle = int(params[6])
	result.fillStyle = int(params[7])
	result.styleValue = float(params[8])
	result.angle = float(params[10])
	result.center = ((int(params[11]), int(params[12])))
	result.radius = ((int(params[13]), int(params[14])))
	result.start = ((int(params[15]), int(params[16])))
	result.end = ((int(params[17]), int(params[18])))
	return result, 0

class Ellipse(EllipseBase):
	def __init__(self, center = None, radii = None,
				 start = None, end = None):
		EllipseBase.__init__(self)
		if center != None and radii != None:
			self.subType = etEllipseRadii
			self.setCenterRadius(center, radii)
		else:
			raise ValueError("Given Ellipse construction parameter combination not handled!")

class Circle(EllipseBase):
	def __init__(self, center = None, radius = None,
				 start = None, end = None):
		EllipseBase.__init__(self)
		if center != None and radius != None:
			self.subType = etCircleRadius
			self.setCenterRadius(center, (radius, radius))
		else:
			raise ValueError("Given Ellipse construction parameter combination not handled!")

class PolylineBase(Object):
	def __init__(self):
		Object.__init__(self, figPolygon)
		self.points = []
		self.closed = True
		self.pictureFilename = None
		self.flipped = False

	def __str__(self):
		pointCount = len(self.points)
		if self.closed:
			pointCount += 1
		subType = self.subType
		if subType == ptPolygon and not self.closed:
			subType = ptPolyline
		hasForwardArrow = (self.forwardArrow != None and 1 or 0)
		hasBackwardArrow = (self.backwardArrow != None and 1 or 0)
		
		result = _join(self.type, subType,
					   self.lineStyle, self.lineWidth,
					   self.penColor, self.fillColor,
					   self.depth, self.penStyle,
					   self.fillStyle, self.styleValue,
					   self.joinStyle, self.capStyle, self.radius,
					   hasForwardArrow, hasBackwardArrow,
					   pointCount) + "\n"

		if hasForwardArrow:
			result += "\t" + str(self.forwardArrow)
		if hasBackwardArrow:
			result += "\t" + str(self.backwardArrow)
		if self.subType == ptPictureBBox:
			result += "\t" + _join(self.flipped, self.pictureFilename) + "\n"
		i = self._savePointIter()
		for linePoints in map(None, *(i, )*12):
			result += "\t" + _join(*[p for p in linePoints if p != None]) + "\n"
		return result

	def _savePointIter(self):
		for p in self.points:
			yield p[0]
			yield p[1]
		if self.closed:
			yield self.points[0][0]
			yield self.points[0][1]

	def bounds(self):
		result = _Rect()
		for point in self.points:
			result(point)
		return result

	def _readSub(self, params):
		if self.forwardArrow == True:
			self.forwardArrow = Arrow(params)
			return True

		if self.backwardArrow == True:
			self.backwardArrow = Arrow(params)
			return True

		if self.subType == ptPictureBBox and self.pictureFilename == None:
			self.flipped = int(params[0])
			self.pictureFilename = params[1]
			return True

		pointCount = len(params) / 2
		for pointIndex in range(pointCount):
			self.points.append((int(params[pointIndex * 2]),
								int(params[pointIndex * 2 + 1])))

		expectedPoints = (self._pointCount + (self.closed and 1 or 0))
		moreToCome = len(self.points) < expectedPoints
		if len(self.points) > self._pointCount:
			if len(self.points) > expectedPoints:
				sys.stderr.write("WARNING: read too many points?!\n")
			del self.points[self._pointCount:]

		return moreToCome

def _readPolylineBase(params):
	result = PolylineBase()
	result.subType = int(params[0])
	result.closed = False
	if result.subType == ptPolyline:
		result.__class__ = PolyLine
	if result.subType == ptBox:
		result.__class__ = PolyBox
		result.closed = True
	if result.subType == ptPolygon:
		result.__class__ = Polygon
		result.closed = True
	if result.subType == ptArcBox:
		#result.__class__ = (not existing yet)
		pass
	if result.subType == ptPictureBBox:
		result.__class__ = PictureBBox
		result.closed = True
	result.lineStyle = int(params[1])
	result.lineWidth = int(params[2])
	result.penColor = int(params[3])
	result.fillColor = int(params[4])
	result.depth = int(params[5])
	result.penStyle = int(params[6])
	result.fillStyle = int(params[7])
	result.styleValue = float(params[8])
	result.joinStyle = int(params[9])
	result.capStyle = int(params[10])
	result.radius = int(params[11])
	subLines = 0
	if int(params[12]):
		result.forwardArrow = True
		subLines += 1
	if int(params[13]):
		result.backwardArrow = True
		subLines += 1
	result._pointCount = int(params[14])
	subLines += (result._pointCount+5)/6 # sublines to read for the points
	if result.closed:
		result._pointCount -= 1
	if result.subType == ptPictureBBox:
		subLines += 1
	return result, subLines

class PolyBox(PolylineBase):
	def __init__(self, x1, y1, x2, y2):
		PolylineBase.__init__(self)
		self.subType = ptBox
		self.points.append((x1, y1))
		self.points.append((x2, y1))
		self.points.append((x2, y2))
		self.points.append((x1, y2))
		self.closed = True

	def center(self):
		return ((self.points[0][0] + self.points[2][0])/2,
				(self.points[0][1] + self.points[2][1])/2)

	def width(self):
		return abs(self.points[2][0] - self.points[0][0])

	def height(self):
		return abs(self.points[2][1] - self.points[0][1])

class Polygon(PolylineBase):
	def __init__(self, points, closed):
		PolylineBase.__init__(self)
		self.subType = ptPolygon
		self.points = points
		self.closed = closed

class PolyLine(PolylineBase):
	def __init__(self, *points):
		PolylineBase.__init__(self)
		self.subType = ptPolyline
		self.points = points
		self.closed = False

class PictureBBox(PolylineBase):
	def __init__(self, x1, y1, x2, y2, filename, flipped = False):
		PolylineBase.__init__(self)
		self.subType = ptPictureBBox
		self.points.append((x1, y1))
		self.points.append((x2, y1))
		self.points.append((x2, y2))
		self.points.append((x1, y2))
		self.pictureFilename = filename
		self.flipped = flipped
		self.closed = True

class SplineBase(Object):
	def __init__(self):
		Object.__init__(self, figSpline)
		self.points = []
		self.shapeFactors = []
		self.closed = True

	def __str__(self):
		pointCount = len(self.points)
		if self.closed:
			pointCount += 1

		hasForwardArrow = (self.forwardArrow != None and 1 or 0)
		hasBackwardArrow = (self.backwardArrow != None and 1 or 0)

		result = _join(self.type, self.subType,
					   self.lineStyle, self.lineWidth,
					   self.penColor, self.fillColor,
					   self.depth, self.penStyle,
					   self.fillStyle, self.styleValue, self.capStyle,
					   hasForwardArrow, hasBackwardArrow,
					   pointCount) + "\n"

		if hasForwardArrow:
			result += "\t" + str(self.forwardArrow)
		if hasBackwardArrow:
			result += "\t" + str(self.backwardArrow)
		result += "\t" + _join(self.points[0][0], self.points[0][1])
		for point in self.points[1:]:
			result += _join("", point[0], point[1])
		if self.closed:
			result += _join("", self.points[0][0], self.points[0][1])
		if self.subType in (stOpenXSpline, stClosedXSpline):
			result += "\n\t" + _join(*self.shapeFactors) + "\n"
		return result

	def bounds(self):
		result = _Rect()
		for point in self.points:
			result(point)
		return result

	def _readSub(self, params):
		if self.forwardArrow == True:
			self.forwardArrow = Arrow(params)
			return True

		if self.backwardArrow == True:
			self.backwardArrow = Arrow(params)
			return True

		expectedPoints = (self._pointCount + (self.closed and 1 or 0))
		if len(self.points) < expectedPoints:
			pointCount = len(params) / 2
			for pointIndex in range(pointCount):
				self.points.append((int(params[pointIndex * 2]),
									int(params[pointIndex * 2 + 1])))
			if len(self.points) > expectedPoints:
				sys.stderr.write("WARNING: read too many points?!\n")
				del self.points[expectedPoints:]
			return True

		if len(self.shapeFactors) < expectedPoints:
			sfCount = len(params)
			for sfIndex in range(sfCount):
				self.shapeFactors.append(float(params[sfIndex]))
			moreToCome = len(self.shapeFactors) < expectedPoints
			if len(self.shapeFactors) > expectedPoints:
				sys.stderr.write("WARNING: read too many shapeFactors?!\n")
				del self.shapeFactors[expectedPoints:]
			if moreToCome:
				return True

		if self.closed:
			del self.points[-1]
			del self.shapeFactors[-1]
		return False

class ApproximatedSpline(SplineBase):
	pass

class InterpolatedSpline(SplineBase):
	pass

class XSpline(SplineBase):
	pass

def _readSplineBase(params):
	result = SplineBase()
	result.subType = int(params[0])
	if result.subType == stClosedApproximated:
		result.__class__ = ApproximatedSpline
	elif result.subType == stOpenInterpolated:
		result.__class__ = InterpolatedSpline
		result.closed = False
	elif result.subType == stClosedInterpolated:
		result.__class__ = InterpolatedSpline
	elif result.subType == stOpenXSpline:
		result.__class__ = XSpline
	elif result.subType == stClosedXSpline:
		result.__class__ = XSpline
	result.lineStyle = int(params[1])
	result.lineWidth = int(params[2])
	result.penColor = int(params[3])
	result.fillColor = int(params[4])
	result.depth = int(params[5])
	result.penStyle = int(params[6])
	result.fillStyle = int(params[7])
	result.styleValue = float(params[8])
	result.capStyle = int(params[9])
	subLines = 0
	if int(params[10]):
		result.forwardArrow = True
		subLines += 1
	if int(params[11]):
		result.backwardArrow = True
		subLines += 1
	result._pointCount = int(params[12])
	subLines += (result._pointCount+5)/6 # sublines to read for the points
	if result.closed:
		result._pointCount -= 1
	return result, subLines

class Text(Object):
	def __init__(self, x, y, text, alignment = alignLeft):
		Object.__init__(self, figText)
		self.text = text
		self.font = fontDefault
		self.fontSize = 12.0
		self.fontAngle = 0.0
		self.fontFlags = ffPostScript
		self.height = 136
		self.length = 100 # dummy value
		self.x = x
		self.y = y
		self.subType = alignment

	def bounds(self):
		result = _Rect()
		if self.subType == alignLeft:
			result((self.x,               self.y - self.height))
			result((self.x + self.length, self.y))
		elif self.subType == alignCentered:
			result((self.x - self.length/2, self.y - self.height))
			result((self.x + self.length/2, self.y))
		elif self.subType == alignRight:
			result((self.x,               self.y - self.height))
			result((self.x + self.length, self.y))
		return result

	def __str__(self):
		result = _join(self.type, self.subType,
					   self.penColor, self.depth, self.penStyle,
					   self.font, self.fontSize, self.fontAngle, self.fontFlags,
					   self.height, self.length, self.x, self.y,
					   self.text + "\\001") + "\n"

		return result

def _readText(params):
	result = Text(int(params[10]), int(params[11]),
				  params[12][:-4], int(params[0]))
	result.penColor = int(params[1])
	result.depth = int(params[2])
	result.penStyle = int(params[3])
	result.font = int(params[4])
	result.fontSize = float(params[5])
	result.fontAngle = float(params[6])
	result.fontFlags = int(params[7])
	result.height = float(params[8])
	result.length = float(params[9])
	return result, 0

class Compound(object):
	def __init__(self, parent = None):
		self.type = figCompoundBegin
		self.objects = []
		self._bounds = _Rect()
		if parent != None:
			parent.append(self)

	def bounds(self):
		return self._bounds

	def append(self, object):
		self.objects.append(object)
		self._bounds(object.bounds())

	def __str__(self):
		if len(self.objects) < 1:
			return ""
		result = ""
		for o in self.objects:
			result += str(o)
		return _join(figCompoundBegin,
					 int(self._bounds.x1), int(self._bounds.y1),
					 int(self._bounds.x2), int(self._bounds.y2)) + "\n" + \
			   result + str(figCompoundEnd) + "\n"

def _readCompound(params):
	result = Compound()
	result._bounds.x1 = int(params[0])
	result._bounds.y1 = int(params[1])
	result._bounds.x2 = int(params[2])
	result._bounds.y2 = int(params[3])
	return result

class _AllObjectIter(object):
	def __init__(self, file, skipCompounds = True):
		self.file = file
		self.iters = [iter(file.objects)]
		self.skipCompounds = skipCompounds

	def __iter__(self):
		return self

	def next(self):
		if not len(self.iters) > 0:
			raise StopIteration
		try:
			next = self.iters[-1].next()
			if next.type == figCompoundBegin:
				self.iters.append(iter(next.objects))
				if not self.skipCompounds:
					return next
			else:
				return next
		except StopIteration:
			del self.iters[-1]
		return self.next()

class File(object):
	def __init__(self, inputFile = None):
		self.objects = []
		self.colors = []
		self.colorhash = {}
		self.filename = None

		if inputFile == None:
			self.landscape = 1
			self.centered = 1
			self.metric = 1
			self.paperSize = "A4"
			self.magnification = 100.0
			self.singlePage = 1
			self.transparentColor = -2 # no transparency, -1 = background, else color#
			self.ppi = 1200 # figure units per inch
		else:
			lineIndex = 0
			stack = []
			currentObject = None
			subLineExpected = 0
			if type(inputFile) == str:
				self.filename = inputFile
				inputFile = file(inputFile).readlines()
			elif hasattr(inputFile, "readlines"):
				if hasattr(inputFile, "name"):
					self.filename = inputFile.name
				inputFile = inputFile.readlines()
			# for error messages:
			filename = self.filename and "'%s'" % self.filename or "<unnamed>"
			for line in inputFile:
				if line.startswith("#"):
					continue
				line = line.strip()
				#print line
				if lineIndex == 0:
					self.landscape = (line.startswith("Landscape"))
				elif lineIndex == 1:
					self.centered = (line.startswith("Center"))
				elif lineIndex == 2:
					self.metric = (line.startswith("Metric"))
				elif lineIndex == 3:
					self.paperSize = line
				elif lineIndex == 4:
					self.magnification = float(line)
				elif lineIndex == 5:
					self.singlePage = (line.startswith("Single"))
				elif lineIndex == 6:
					self.transparentColor = int(line)
				elif lineIndex == 7:
					res, sysDummy = re.split(" +", line)
					self.ppi = int(res)
				else:
				  try:
					params = re.split(" +", line)
					if subLineExpected:
						subLineExpected = currentObject._readSub(params)
					else:
						objectType = int(params[0])
						subLineExpected = 0
						if objectType == figCustomColor:
							self.colors.append(
								CustomColor(int(params[1]), params[2]))
						elif objectType == figPolygon:
							currentObject, subLineExpected = _readPolylineBase(params[1:])
						elif objectType == figArc:
							currentObject, subLineExpected = _readArcBase(params[1:])
						elif objectType == figSpline:
							currentObject, subLineExpected = _readSplineBase(params[1:])
						elif objectType == figText:
							currentObject, subLineExpected = _readText(params[1:])
						elif objectType == figEllipse:
							currentObject, subLineExpected = _readEllipseBase(params[1:])
						elif objectType == figCompoundBegin:
							stack.append(_readCompound(params[1:]))
						elif objectType == figCompoundEnd:
							currentObject = stack.pop()
						else:
							raise ValueError(
								"Unhandled object type %s!" % (objectType, ))
					if currentObject != None and not subLineExpected:
						if len(stack) > 0:
							stack[-1].append(currentObject)
						else:
							self.objects.append(currentObject)
						currentObject = None
				  except ValueError:
					  sys.stderr.write("Parse error in %s, line %i:\n%s\n\n" %
									   (filename, lineIndex + 1, line))
					  raise
				lineIndex += 1

	def allObjects(self, includeCompounds = False):
		"""Returns an iterator iterating over all objects in this
		document, recursively entering compound objects.  You can use
		the optional parameter includeCompounds (default: False) to
		get the compound objects themselves returned, too."""
		return _AllObjectIter(self, not includeCompounds)

	def append(self, object):
		"""Adds the object to this document, i.e. appends an object to
		self.objects (or self.colors if it's a CustomColor)."""
		if type(object) == CustomColor:
			self.colors.append(object)
		else:
			self.objects.append(object)

	def remove(self, object):
		self.objects.remove(object)

	def addColor(self, hexCode):
		result = CustomColor(colorCustom0 + len(self.colors), hexCode)
		self.colors.append(result)
		self.colorhash[hexCode] = result
		return result

	def getColor(self, color, similarity = None):
		"""Returns a color object for the given color, adding a new
		custom color to this document if it does not yet exist.  The
		color can be given as tuple of 0..255 values for R,G,B or as
		hex string (e.g. (0, 255, 0) or '#00ff00' for green)."""
		
		if type(color) == float: # accept grayvalues as float (0..1)
			color = int(round((color*255)))
		if type(color) == int: # accept grayvalues as int (0..255)
			color = (color, color, color)
		if type(color) == types.TupleType: # accept colors as 3-tuple of (0..255)
			if type(color[0]) == float:
				color = (int(round((color[0]*255))),
						 int(round((color[1]*255))),
						 int(round((color[2]*255))))
			color = "#%02x%02x%02x" % color
		if type(color) != types.StringType: # accept RGB color objects
			color = "#%02x%02x%02x" % tuple(color)
		assert len(color) == 7, "too large values given for red, green, or blue"
		try:
			return self.colorhash[color]
		except KeyError:
			if similarity != None:
				if similarity > 0.0:
					t = CustomColor(None, color)
					for hex in self.colorhash:
						o = self.colorhash[hex]
						def sq(x): return x*x
						if math.sqrt(sq(o[0]-t[0]) +
									 sq(o[1]-t[1]) +
									 sq(o[2]-t[2])) < similarity:
							return o
				else:
					raise # if similarity == 0.0 or < 0, don't add color
			return self.addColor(color)

	def colorRGB(self, color):
		"""Returns a the R,G,B tuple for the given color index."""
		if color < 0:
			return None
		elif color < colorCustom0:
			return standardColors[color]
		else:
			return self.colors[color].rgb()

	def gray(self, grayLevel):
		"""Returns a color representing the given graylevel (see getColor).
		grayLevel can be a float in the range 0.0 - 1.0 or a 0 - 255 integer."""
		return self.getColor((grayLevel, grayLevel, grayLevel))

	def headerStr(self):
		"""Returns the first lines of the XFig file output, which contain
		global document information like orientation / units / ..."""
		result = "#FIG 3.2\n"
		if self.landscape:
			result += "Landscape\n"
		else:
			result += "Portrait\n"
		if self.centered:
			result += "Center\n"
		else:
			result += "Flush Left\n"
		if self.metric:
			result += "Metric\n"
		else:
			result += "Inches\n"
		result += self.paperSize + "\n"
		result += str(self.magnification) + "\n"
		if self.singlePage:
			result += "Single\n"
		else:
			result += "Multiple\n"
		result += str(self.transparentColor) + "\n"
		result += str(self.ppi) + " 2\n" # (2: only used coordinate system)
		return result

	def objectsStr(self):
		"""Returns the part of the XFig file containing all objects
		(but not the custom colors).  This is the same as str(object)
		concatenated for each object in (figfile).objects."""
		result = ""
		for object in self.objects:
			result += str(object)
		return result

	def __str__(self):
		"""Returns the contents of this file in the XFig file format as string.
		See save()."""
		result = self.headerStr()
		for color in self.colors:
			result += repr(color)
		result += self.objectsStr()
		return result

	def save(self, filename):
		"""Saves the contents of this file in the XFig file format to
		the file 'filename'.  figfile.save(filename) is equivalent to:
		
		  file(filename, "w").write(str(figfile))"""
		
		file(filename, "w").write(str(self))

	def save(self, filename):
		"""Saves the contents of this file in the XFig file format to
		the file 'filename'.  figfile.save(filename) is equivalent to:
		
		  file(filename, "w").write(str(figfile))"""
		
		file(filename, "w").write(str(self))

	def saveEPS(self, basename):
		"""Saves the contents of this file to [basename].fig and calls
		fig2dev to create a [basename].eps, too.  The basename
		(without either .fig or .eps!) is returned, so that you can
		use expressions like:

		  resultBasename = figFile.saveEPS(namePrefix + "_%d" % index)"""

		self.save(basename + ".fig")
		cin, cout = os.popen4("fig2dev -Leps %s.fig %s.eps" % ((basename, )*2))
		cin.close(); print cout.read()
		del cin, cout

		return basename
