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


scrollbarwidth = 512
scrollbarheight = 1024

selection_start = 0 # bits
selection_width = 128
selection_height = 128
# selected bits = w*h

visualization_display_width = 512
visualization_display_height = 2048

scrollbar_drag_start_origin = None
scrollbar_drag_start_screen = None

visualization_drag_start_map = None
visualization_drag_start_screen = None

infile = np.memmap(sys.argv[1], dtype=np.uint8, mode='r')
sourcebits = np.unpackbits(infile) * 255

im_scrollbar = None
im_scrollbar_display = None

def round_down(x, k):
	return (x // k) * k

def round_up(x, k):
	return x + (-x % k)

def redraw_scrollbar():
	global im_scrollbar
	global im_scrollbar_display

	w = int(selection_width)
	h = int(selection_height)

	if im_scrollbar is None:
		im_scrollbar = np.pad(sourcebits, (0, -len(sourcebits) % scrollbarwidth), 'constant').reshape((-1, scrollbarwidth))
		im_scrollbar_display = None

	if im_scrollbar_display is None:
		im_scrollbar_display = cv2.resize(
			im_scrollbar,
			dsize=(scrollbarwidth, scrollbarheight),
			interpolation=cv2.INTER_AREA)

	canvas = im_scrollbar_display.copy()

	canvas = cv2.cvtColor(src=canvas, code=cv2.COLOR_GRAY2BGR)
	#print canvas.shape
	#canvas[:,:,(0,2)] = 0

	cv2.rectangle(
		canvas,
		(0,              int(selection_start / len(sourcebits) * scrollbarheight)),
		(scrollbarwidth, int((selection_start + w*h) / len(sourcebits) * scrollbarheight)),
		(0, 0, 255),
		thickness=2)

	cv2.imshow("scrollbar", canvas)

	return im_scrollbar

def redraw_visualization():
	w = int(selection_width)
	h = int(selection_height)

	start = selection_start
	stop  = selection_start + w*h

	pixels = sourcebits[start:stop].reshape((h, w))

	canvas = cv2.resize(
		pixels,
		(visualization_display_width, visualization_display_height),
		interpolation=cv2.INTER_AREA)
	cv2.imshow("visualization", canvas)

def redraw():
	global selection_start

	w = int(selection_width)
	h = int(selection_height)

	if selection_start < 0:
		selection_start = 0
	elif selection_start + w*h >= len(sourcebits):
		selection_start = len(sourcebits) - w*h

	redraw_scrollbar()
	redraw_visualization()
	print_status()
	
def on_scrollbar_scroll(event, x, y, flags, param):
	global selection_height
	direction = (flags > 0) - (flags < 0)
	k = 1.0/16
	if direction < 0:
		selection_height *= 1+k
	else:
		selection_height /= 1+k

	redraw()

def on_scrollbar_down(event, x, y, flags, param):
	global scrollbar_drag_start_origin, scrollbar_drag_start_screen
	scrollbar_drag_start_screen = y / scrollbarheight * len(sourcebits)
	scrollbar_drag_start_origin = selection_start

def on_scrollbar_drag(event, x, y, flags, param):
	w = int(selection_width)
	h = int(selection_height)

	scrollbar_drag_now_screen = y / scrollbarheight * len(sourcebits)
	delta = scrollbar_drag_now_screen - scrollbar_drag_start_screen
	global selection_start

	selection_start = scrollbar_drag_start_origin
	selection_start += int(round_down(delta * w*h*64.0/len(sourcebits), w))

	redraw()

def on_scrollbar_up(event, x, y, flags, param):
	global scrollbar_drag_start_origin, scrollbar_drag_start_screen
	scrollbar_drag_start_screen = None
	scrollbar_drag_start_origin = None

def on_visualization_scroll(event, x, y, flags, param):
	global selection_width
	direction = (flags > 0) - (flags < 0)
	selection_width += direction
	print_status()
	redraw_visualization()

def on_visualization_down(event, x, y, flags, param):
	global visualization_drag_start_map
	global visualization_drag_start_screen
	w = int(selection_width)
	h = int(selection_height)
	visualization_drag_start_screen = np.array([
		x / visualization_display_width  * w,
		y / visualization_display_height * h])
	visualization_drag_start_map = selection_start

def on_visualization_drag(event, x, y, flags, param):
	#visualization_drag_now_screen = np.array([x, y])

	w = int(selection_width)
	h = int(selection_height)

	offset_bits = visualization_drag_start_map
	offset_bits -= w * (
		int((y/visualization_display_height*h) - visualization_drag_start_screen[1])
	)
	offset_bits -= (x/visualization_display_width*w - visualization_drag_start_screen[0])

	global selection_start
	selection_start = int(offset_bits)

	redraw()

def on_visualization_up(event, x, y, flags, param):
	global visualization_drag_start_map, visualization_drag_start_screen
	visualization_drag_start_screen = None
	visualization_drag_start_map = None

def visualization_callback(event, x, y, flags, param):
	if event == 10: # scroll wheel
		on_visualization_scroll(event, x, y, flags, param)

	elif event == 1: # mouse down
		print "viz down"
		on_visualization_down(event, x, y, flags, param)

	elif event == 0 and flags == 1: # mouse drag
		on_visualization_drag(event, x, y, flags, param)

	elif event == 4: # mouse up
		on_visualization_up(event, x, y, flags, param)

def on_scrollbar_rightclick(event, x, y, flags, param):
	global selection_start

	w = int(selection_width)
	h = int(selection_height)

	center = y/scrollbarheight * len(sourcebits)
	selection_start = center - 0.5 * w*h
	selection_start = round(selection_start / selection_width) * selection_width

	redraw()

def scrollbar_callback(event, x, y, flags, param):
	if event == 10: # scroll wheel
		on_scrollbar_scroll(event, x, y, flags, param)

	elif event == 1: # mouse down
		on_scrollbar_down(event, x, y, flags, param)

	elif event == 0 and flags == 1: # mouse drag
		on_scrollbar_drag(event, x, y, flags, param)

	elif event == 4: # mouse up
		on_scrollbar_up(event, x, y, flags, param)

	elif event == 2: # right click
		on_scrollbar_rightclick(event, x, y, flags, param)

	elif event == 0 and flags == 2: # right drag
		on_scrollbar_rightclick(event, x, y, flags, param)


def hexdump(at, bytes):
	def charfunc(code):
		if code is None:
			return ' '
		elif 32 <= code < 128:
			return chr(code)
		else:
			return '.'

	for i in xrange(0, len(bytes), 16):
		row = bytes[i:i+16]
		print "{:8x} : {} : {}".format(
			at + i,
			' '.join(
				"{:02X}".format(row[j]) if j < len(row) else '  '
				for j in xrange(16)
			),
			''.join(
				charfunc(row[j] if j < len(row) else None)
				for j in xrange(16)
			),
		)

def process_key(keycode):
	global keybuffer
	global selection_start
	global selection_width

	w = int(selection_width)
	h = int(selection_height)

	if keycode == 0x08:
		keybuffer = keybuffer[:-1]
		sys.stdout.write('\b \b')

	elif keycode == 0x0D or keycode == 0x0A:
		print
		process_command(keybuffer)
		keybuffer = ""

	elif keycode == ord('-'):
		selection_width -= 1

	elif keycode in [ord('='), ord('+')]:
		selection_width += 1

	elif keycode == VK_PGUP:
		selection_start -= w*h

	elif keycode == VK_PGDN:
		selection_start += w*h

	elif keycode == VK_LEFT:
		selection_start -= 1

	elif keycode == VK_RIGHT:
		selection_start += 1

	elif keycode == VK_UP:
		selection_start -= w

	elif keycode == VK_DOWN:
		selection_start += w

	elif keycode == 4: # ctrl-d
		hexdump(selection_start // 8, np.packbits(sourcebits[selection_start:selection_start+w*h]))

	else:
		print "keycode", keycode

	redraw()

def process_command(cmd):
	if cmd.startswith('g'):
		global selection_start
		offset = int(cmd[1:], 16)
		selection_start = offset * 8

	elif cmd.startswith('w'):
		global selection_width
		width = int(cmd[1:], 0)
		selection_width = width

	elif cmd.startswith('h'):
		global selection_height
		height = int(cmd[1:], 0)
		selection_height = height

	redraw()

def print_status():
	print "start: 0x{:8x} + {} bits, {:.1f} x {:.1f} pixels".format(
		int(selection_start // 8),
		selection_start % 8,
		selection_width, selection_height,
	)

cv2.namedWindow("visualization", cv2.WINDOW_NORMAL)
cv2.namedWindow("scrollbar", cv2.WINDOW_NORMAL)

#cv2.resizeWindow("scrollbar", int(scrollbarwidth), int(scrollbarheight))

cv2.setMouseCallback("visualization", visualization_callback)
cv2.setMouseCallback("scrollbar", scrollbar_callback)

redraw()

keybuffer = ""

# [25.08. 22:10:29] <jn> keycode 65362
# [25.08. 22:10:29] <jn> start: 0x   6e3c3 + 2 bits, 128.0 x 128.0 pixels
# [25.08. 22:10:29] <jn> start: 0x   6e3c3 + 2 bits, 128.0 x 128.0 pixels
# [25.08. 22:10:29] <jn> keycode 65363
# [25.08. 22:10:29] <jn> start: 0x   6e3c3 + 2 bits, 128.0 x 128.0 pixels
# [25.08. 22:10:31] <jn> start: 0x   6e3c3 + 2 bits, 128.0 x 128.0 pixels
# [25.08. 22:10:34] <jn> keycode 65364
# [25.08. 22:10:36] <jn> start: 0x   6e3c3 + 2 bits, 128.0 x 128.0 pixels
# [25.08. 22:10:39] <jn> start: 0x   6e3c3 + 2 bits, 128.0 x 128.0 pixels
# [25.08. 22:10:41] <jn> keycode 65361
# [25.08. 22:10:42] <Cracki> hoch rechts unten links

if os.name == 'nt':
	VK_PGUP  = 2162688
	VK_PGDN  = 2228224
	VK_UP    = 2490368
	VK_DOWN  = 2621440
	VK_LEFT  = 2424832
	VK_RIGHT = 2555904
else:
	VK_PGUP  = 65365
	VK_PGDN  = 65366
	VK_UP    = 65362
	VK_DOWN  = 65364
	VK_LEFT  = 65361
	VK_RIGHT = 65363

while True:
	key = cv2.waitKey(500)

	if key == -1:
		continue
	
	elif key in (27,):
		break

	elif not (0x20 <= key < 0x80) or chr(key) in '-=+':
		process_key(key)

	else:
		keybuffer += chr(key)
		sys.stdout.write(chr(key))

cv2.destroyAllWindows()
