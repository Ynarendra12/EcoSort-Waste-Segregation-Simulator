"""
Classic computer graphics algorithms implemented by hand.

* dda_line            - Digital Differential Analyzer line drawing
* bresenham           - Bresenham's line drawing
* midpoint_circle     - Midpoint circle drawing
* cohen_sutherland    - Line clipping against a rectangular window
* scanline_fill       - Scan-line polygon filling
"""
import math


def dda_line(x0, y0, x1, y1):
    """DDA line: step along the longer axis in equal increments."""
    dx, dy = x1 - x0, y1 - y0
    steps = int(max(abs(dx), abs(dy)))
    if steps == 0:
        return [(int(round(x0)), int(round(y0)))]
    xi, yi = dx / steps, dy / steps
    x, y = x0, y0
    pts = []
    for _ in range(steps + 1):
        pts.append((int(round(x)), int(round(y))))
        x += xi
        y += yi
    return pts


def bresenham(x0, y0, x1, y1):
    """Bresenham line: integer-only decision parameter."""
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    pts = []
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    return pts


def midpoint_circle(cx, cy, r):
    """Midpoint circle: compute one octant and mirror it 8 ways."""
    pts = []
    x, y = 0, int(r)
    p = 1 - int(r)
    while x <= y:
        for ox, oy in ((x, y), (y, x), (-x, y), (-y, x),
                       (x, -y), (y, -x), (-x, -y), (-y, -x)):
            pts.append((int(cx) + ox, int(cy) + oy))
        x += 1
        if p < 0:
            p += 2 * x + 1
        else:
            y -= 1
            p += 2 * (x - y) + 1
    return pts


# ------------------------------------------------- Cohen-Sutherland clipping
_LEFT, _RIGHT, _TOP, _BOTTOM = 1, 2, 4, 8


def _outcode(x, y, xmin, ymin, xmax, ymax):
    code = 0
    if x < xmin:
        code |= _LEFT
    elif x > xmax:
        code |= _RIGHT
    if y < ymin:
        code |= _TOP        # screen y grows downward
    elif y > ymax:
        code |= _BOTTOM
    return code


def cohen_sutherland(x0, y0, x1, y1, xmin, ymin, xmax, ymax):
    """
    Clip a line to the window.  Returns the clipped (x0, y0, x1, y1) or None if
    the line is completely outside.
    """
    c0 = _outcode(x0, y0, xmin, ymin, xmax, ymax)
    c1 = _outcode(x1, y1, xmin, ymin, xmax, ymax)
    while True:
        if not (c0 | c1):
            return x0, y0, x1, y1          # trivially accepted
        if c0 & c1:
            return None                    # trivially rejected
        out = c0 or c1
        if out & _BOTTOM:
            x = x0 + (x1 - x0) * (ymax - y0) / (y1 - y0)
            y = ymax
        elif out & _TOP:
            x = x0 + (x1 - x0) * (ymin - y0) / (y1 - y0)
            y = ymin
        elif out & _RIGHT:
            y = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0)
            x = xmax
        else:
            y = y0 + (y1 - y0) * (xmin - x0) / (x1 - x0)
            x = xmin
        if out == c0:
            x0, y0 = x, y
            c0 = _outcode(x0, y0, xmin, ymin, xmax, ymax)
        else:
            x1, y1 = x, y
            c1 = _outcode(x1, y1, xmin, ymin, xmax, ymax)


# --------------------------------------------------------- scan-line filling
def scanline_fill(poly):
    """
    Scan-line polygon fill.  For every horizontal line (scan line) we find where
    it crosses the polygon edges, sort the crossings and fill between pairs.
    Returns a list of spans (y, x_left, x_right).
    """
    n = len(poly)
    ys = [p[1] for p in poly]
    ymin, ymax = int(math.floor(min(ys))), int(math.ceil(max(ys)))
    spans = []
    for y in range(ymin, ymax + 1):
        yc = y + 0.5
        xs = []
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            if y1 == y2:
                continue
            if (y1 <= yc < y2) or (y2 <= yc < y1):
                xs.append(x1 + (yc - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            spans.append((y, int(round(xs[i])), int(round(xs[i + 1]))))
    return spans
