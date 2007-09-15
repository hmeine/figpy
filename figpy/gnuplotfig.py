import fig, sys

class GnuplotFig(fig.File):
	"""Subclass of fig.File which separates objects into
	different layers / depths on load:
	  0: labels
	  1: horizontal tick labels
	  2: vertical tick labels
	  4: first frame
	  5: ticks
	 10: data
	100: second frame
	(Furthermore, the frames are converted into proper boxes.)

	If no logscale is used, the plot range is detected and stored in
	xRange/yRange as (start,end) pairs, where start/end are itself
	pairs of fig/plot coordinates.

	The two methods fig2plot and plot2fig can be used to transform
	vectors between the two coordinate systems."""

	__slots__ = ("xRange", "yRange")

	def __init__(self, filename):
		fig.File.__init__(self, filename)

		if self.comment:
			# already processed
			self.xRange, self.yRange = eval(self.comment)
			return

		self.landscape = False

		l = self.layer(0)
		i = 0
		while l[i].alignment == fig.alignRight:
			l[i].depth = 2
			i += 1
		while l[i].text.startswith(" "):
			l[i].depth = 1
			i += 1
		
		l = self.layer(10)
		frame1 = l[-1]
		i = 0
		while l[i].points != frame1.points:
			l[i].depth = 5
			i += 1
		frame2 = l[i]
		print "%d out of %d elements shifted from depth 10 -> 5" % (
			i, len(l))
			
		frame1.changeType(fig.ptBox)
		frame1.depth = 100
		frame2.changeType(fig.ptBox)
		frame2.depth = 4

		ticks = self.layer(5)
		if len(ticks) != 2*(len(self.layer(1)) + len(self.layer(2))):
			self.comment = "could not extract scale (logscale used?)"
			sys.stderr.write("WARNING: %s\n" % self.comment)
			return

		yTickLabels = self.layer(2)
		yTicks = [ticks[2*i] for i in range(len(yTickLabels))]
		self.yRange = ((yTicks[0].points[0][1], float(yTickLabels[0].text)),
					   (yTicks[-1].points[0][1], float(yTickLabels[-1].text)))

		xTickLabels = self.layer(1)
		xTicks = [ticks[2*(i+len(yTicks))] for i in range(len(xTickLabels))]
		self.xRange = ((xTicks[0].points[0][0], float(xTickLabels[0].text)),
					   (xTicks[-1].points[0][0], float(xTickLabels[-1].text)))

		self.comment = repr((self.xRange, self.yRange))

	def plot2fig(self, (x, y)):
		xBegin, xEnd = self.xRange
		yBegin, yEnd = self.yRange
		return fig.Vector(
			xBegin[0] + (xEnd[0]-xBegin[0])*(x - xBegin[1])/(xEnd[1]-xBegin[1]),
			yBegin[0] + (yEnd[0]-yBegin[0])*(y - yBegin[1])/(yEnd[1]-yBegin[1]))

	def fig2plot(self, (x, y)):
		xBegin, xEnd = self.xRange
		yBegin, yEnd = self.yRange
		return fig.Vector(
			xBegin[1] + (xEnd[1]-xBegin[1])*(x - xBegin[0])/(xEnd[0]-xBegin[0]),
			yBegin[1] + (yEnd[1]-yBegin[1])*(y - yBegin[0])/(yEnd[0]-yBegin[0]))

	def fixRedData(self):
		"""Somehow, Gnuplot does not assign the first linestyle the
		proper (red) color, but black.  Thus function corrects this
		(by assigning red to all black elements of depth 10)."""
		self.findObjects(depth = 10, penColor = fig.colorBlack) \
							   .penColor = fig.colorRed

	def addVerticalLine(self, xPos, **attr):
		figPos = self.plot2fig((xPos, 0))[0]
		frame = self.layer(4)[0].bounds()
		line = fig.Polyline([(figPos, frame.top()),
							 (figPos, frame.bottom())])
		self.append(line)
		for a in attr:
			setattr(line, a, attr[a])
		return line
