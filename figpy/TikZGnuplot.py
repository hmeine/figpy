import os, sys, numpy
import tikz

class Data(object):
	def __init__(self, data, **kwargs):
		self.props = kwargs
		self.data = data

	def iter2D(self):
		#print self.data
		if numpy.isscalar(self.data[0]):
			it = enumerate(self.data)
		else:
			it = iter(self.data)
		return it

	def gnuplotPlot(self):
		rest = dict(self.props)
		options = ""
		if "with" in rest:
			options += " with %s" % rest["with"]
			del rest["with"]
		if rest:
			options += " " + " ".join(
				"%s %r" % kv for kv in plotItem.props.items())
		return '"%s"%s' % (datFileName, options)

epsColors = ("black",
			 "red", "green", "blue", "magenta", "cyan", "yellow",
			 "black", "red", "gray", # here differs from X11 terminal
			 "red", "green", "blue", "magenta", "cyan", "yellow",
			 "black", "red", "gray")
epsMarks = ("", "+", "x", "asterisk", "square", "square*",
			"o", "*", "triangle", "triangle*",
			"triangle", "triangle*", # TODO: add rotation to mark options
			)

class Gnuplot(object):
	def __init__(self, mode = "pgfplots"):
		self.ranges = {}
		self.mode = mode
		self.xlabel = None
		self.ylabel = None

	def __call__(self, command):
		print command
		command = command.strip()
		if command.startswith("set terminal"):
			pass
		elif command.startswith("set output "):
			self.basename = os.path.splitext(eval(command[11:]))[0]
		elif command.startswith("set xlabel "):
			self.xlabel = eval(command[11:])
		elif command.startswith("set ylabel "):
			self.ylabel = eval(command[11:])
		else:
			print "WARNING: not parsed: '%s'." % command

	def set_range(self, rangeName, (min, max)):
		print "set %s [%s:%s]" % (rangeName, min, max)
		self.ranges[rangeName] = (min, max)

	@staticmethod
	def saveDataFile(plotItem, filename):
		f = file(filename, "w")
		for field in plotItem.iter2D():
			if numpy.isnan(field[1]):
				f.write("\n")
			else:
				f.write("%s\n" % " ".join(map(lambda f: "%.5f" % f, field)))
		f.close()

	def plot(self, *plotItems):
		f = file("%s_plots.tikz" % (self.basename, ), "w")

		if self.mode == "pgfplots":
			axisOptions = tikz.Options()
			if "xrange" in self.ranges:
				min, max = self.ranges["xrange"]
				axisOptions["\n  xmin"] = min
				axisOptions["xmax"] = max
			if "yrange" in self.ranges:
				min, max = self.ranges["yrange"]
				axisOptions["\n  ymin"] = min
				axisOptions["ymax"] = max
			if self.xlabel:
				axisOptions["\n  xlabel"] = "{%s}" % self.xlabel
			if self.ylabel:
				axisOptions["\n  ylabel"] = "{%s}" % self.ylabel
			f.write("\\begin{axis}%s\n\n" % axisOptions)

		for i, plotItem in enumerate(plotItems):
			color = epsColors[i+1]
			mark = epsMarks[i+1]

			pathOptions = tikz.Options()
			plotOptions = tikz.Options()
			markOptions = tikz.Options()
			w = plotItem.props.get("with", "lines").split()
			ignored = []
			while w:
				if w[0] in ("lines", "l"):
					pass
				elif w[0] in ("linespoints", "lp"):
					plotOptions.append("mark")
				elif w[0] in ("points", "p"):
					plotOptions.append("only marks")
				elif w[0] in ("pointsize", "ps"):
					del w[0]
					markOptions["scale"] = w[0]
				elif w[0]:
					ignored.append(w[0])
				del w[0]
			if ignored:
				sys.stderr.write("WARNING: with=%s ignored.\n" % ignored)

			if "mark" in plotOptions:
				plotOptions["mark"] = mark

			pathOptions.append(color)

			if markOptions:
				plotOptions.append(
					"mark options={%s}" % markOptions.commaSeparated())

			if self.mode == "tikz":
				datFileName = "%s_%d.dat" % (self.basename, i+1)
				self.saveDataFile(plotItem, datFileName)
				f.write("\draw%s plot%s file{%s};\n" % (
					pathOptions, plotOptions, datFileName))
			elif self.mode == "pgfplots":
				pathOptions.extend(plotOptions)
				coordinates = " ".join([
					"(%.5f,%.5f)" % p for p in plotItem.data])
				plots = coordinates.split("(nan,nan)")
				f.write(("\\addplot%s plot coordinates {\n  %s\n};\n" % (
					pathOptions, "\n  ".join(plots))))
				if "title" in plotItem.props:
					f.write(
						"\\addlegendentry{%s}\n" % plotItem.props["title"])
				f.write("\n")
			else:
				raise ValueError("Unknown mode (%s), should be 'tikz' or 'pgfplots'" % self.mode)

			print plotItem.props, plotOptions

		if self.mode == "pgfplots":
			f.write("\\end{axis}\n")
		
		f.close()
		
