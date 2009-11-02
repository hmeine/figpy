#!/usr/bin/env python
import sys, fig, re, getopt

yOffset = 0.5 * fig.unitCM

f = fig.File()

tx = 0
lx = tx + 3 * fig.unitCM
xDist = 2 * fig.unitCM
length = 0.9*xDist

y = 0
for i in range(15):
	to = fig.Text((tx, y), "Arrow type %d:" % i)
	f.append(to)

	for j in range(2):
		lo = fig.Polyline([(lx + j*xDist, y), (lx + j*xDist + length, y)])
		lo.forwardArrow = fig.Arrow(i, j)
		f.append(lo)

	y += yOffset

f.save("test_arrowtypes.fig")
