#!/usr/bin/env python2
from __future__ import division
import os
import sys
import cv2
import numpy as np

# class DragDropHandler(object):
# 	def __init__(self, cbstart, cbdrag, cbstop):
# 		self.cbstart = cbstart
# 		self.cbdrag = cbdrag
# 		self.cbstop = cbstop
# 		self.data_origin = None

# 	def on_down(self, event, x, y, flags, param):
# 		self.data_origin = self.cbstart()
# 		self.screen_origin = (x,y)

# 	def on_drag(self, event, x, y, flags, param):
# 		self.cbdrag()


winw,winh = 1366, 768

scrollbarwidth = 256
scrollbarheight = 800

selection_start = 0.0
selection_range = 0.2

scrollbar_drag_start_origin = None
scrollbar_drag_start_screen = None

visualization_drag_start_origin = None
visualization_drag_start_screen = None

visualization_offset = 0 # draggable, wraps around
visualization_width = scrollbarwidth

infile = np.memmap(sys.argv[1], dtype=np.uint8, mode='r')

im_scrollbar = None
im_scrollbar_display = None

def round_down(x, k):
	return (x // k) * k

def redraw_scrollbar():
	global im_scrollbar
	global im_scrollbar_display

	height = scrollbarheight

	if im_scrollbar is None:
		im_scrollbar = np.pad(infile, (0, -len(infile) % scrollbarwidth), 'constant').reshape((-1, scrollbarwidth))
		im_scrollbar_display = None

	if im_scrollbar_display is None:
		im_scrollbar_display = cv2.resize(im_scrollbar, dsize=(scrollbarwidth, height), interpolation=cv2.INTER_AREA)

	canvas = im_scrollbar_display.copy()

	cv2.rectangle(
		canvas,
		(0,              int(0.5 + (selection_start) * scrollbarheight)),
		(scrollbarwidth, int(0.5 + (selection_start + selection_range) * scrollbarheight)),
		(255, 255, 255))

	print "selection: {:08x}h + {:d} bytes".format(
		int(len(infile) * selection_start),
		int(len(infile) * selection_range),
	)

	cv2.imshow("scrollbar", canvas)

	return im_scrollbar

def redraw_visualization():
	start = round_down(int(selection_start * len(infile)), scrollbarwidth)
	start += visualization_offset

	stop  = start + int(selection_range * len(infile))

	bytes = np.unpackbits(infile[start:stop]) * 255
	bytes = np.pad(bytes, (0, -len(bytes) % visualization_width), 'constant').reshape((-1, visualization_width))
	bytes = cv2.resize(bytes, (512, 800), interpolation=cv2.INTER_AREA)
	cv2.imshow("visualization", bytes)

def on_scrollbar_scroll(event, x, y, flags, param):
	global selection_range
	direction = (flags > 0) - (flags < 0)
	selection_range *= (1.0 - direction * 0.1)
	redraw_scrollbar()
	redraw_visualization()

def on_scrollbar_down(event, x, y, flags, param):
	global scrollbar_drag_start_origin, scrollbar_drag_start_screen
	scrollbar_drag_start_screen = y / scrollbarheight
	scrollbar_drag_start_origin = selection_start

def on_scrollbar_drag(event, x, y, flags, param):
	scrollbar_drag_now_screen = y / scrollbarheight
	delta = scrollbar_drag_now_screen - scrollbar_drag_start_screen
	global selection_start

	selection_start = scrollbar_drag_start_origin + delta
	if selection_start < 0:
		selection_start = 0
	elif selection_start + selection_range >= 1.0:
		selection_start = 1.0 - selection_range

	redraw_scrollbar()
	redraw_visualization()

def on_scrollbar_up(event, x, y, flags, param):
	global scrollbar_drag_start_origin, scrollbar_drag_start_screen
	scrollbar_drag_start_screen = None
	scrollbar_drag_start_origin = None

def on_visualization_scroll(event, x, y, flags, param):
	global visualization_width
	direction = (flags > 0) - (flags < 0)
	visualization_width += direction
	print "width: {}".format(visualization_width)
	redraw_visualization()

def visualization_callback(event, x, y, flags, param):
	if event == 10: # scroll wheel
		on_visualization_scroll(event, x, y, flags, param)

	elif event == 1: # mouse down
		on_visualization_down(event, x, y, flags, param)

	elif event == 0 and flags == 1: # mouse drag
		on_visualization_drag(event, x, y, flags, param)

	elif event == 4: # mouse up
		on_visualization_up(event, x, y, flags, param)

def scrollbar_callback(event, x, y, flags, param):
	if event == 10: # scroll wheel
		on_scrollbar_scroll(event, x, y, flags, param)

	elif event == 1: # mouse down
		on_scrollbar_down(event, x, y, flags, param)

	elif event == 0 and flags == 1: # mouse drag
		on_scrollbar_drag(event, x, y, flags, param)

	elif event == 4: # mouse up
		on_scrollbar_up(event, x, y, flags, param)

cv2.namedWindow("visualization")
cv2.setMouseCallback("visualization", visualization_callback)

cv2.namedWindow("scrollbar")
cv2.setMouseCallback("scrollbar", scrollbar_callback)

redraw_visualization()
redraw_scrollbar()

while True:
	key = cv2.waitKey(500)

	if key == -1:
		continue
	
	elif key in (13, 10, 27):
		break

	else:
		print "key {:x}".format(key)

cv2.destroyAllWindows()
