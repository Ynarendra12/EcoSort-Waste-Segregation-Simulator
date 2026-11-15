"""Small drawing helpers.  Every helper accepts an optional matrix `m` so that
shapes can be defined in their own local coordinates and then transformed."""
import math
import pygame
from transforms import transform_points, scale_factor

OUTLINE = (35, 35, 50)


def poly(surf, color, pts, m=None, outline=OUTLINE, width=2):
    p = transform_points(pts, m) if m else list(pts)
    if len(p) < 3:
        return
    pygame.draw.polygon(surf, color, p)
    if outline:
        pygame.draw.polygon(surf, outline, p, width)


def rect(surf, color, x, y, w, h, m=None, outline=OUTLINE, width=2):
    poly(surf, color, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], m, outline, width)


def ellipse_pts(cx, cy, rx, ry, n=28):
    return [(cx + rx * math.cos(2 * math.pi * i / n),
             cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def ellipse(surf, color, cx, cy, rx, ry, m=None, outline=OUTLINE, width=2):
    poly(surf, color, ellipse_pts(cx, cy, rx, ry), m, outline, width)


def circle(surf, color, cx, cy, r, m=None, outline=OUTLINE, width=2):
    if m is None:
        x, y, rr = cx, cy, r
    else:
        (x, y), = transform_points([(cx, cy)], m)
        rr = r * scale_factor(m)
    x, y, rr = int(round(x)), int(round(y)), max(1, int(round(rr)))
    pygame.draw.circle(surf, color, (x, y), rr)
    if outline and rr > 2:
        pygame.draw.circle(surf, outline, (x, y), rr, width)


def line(surf, color, p0, p1, m=None, width=2):
    if m:
        p0, p1 = transform_points([p0, p1], m)
    pygame.draw.line(surf, color, p0, p1, max(1, int(width)))


def polyline(surf, color, pts, m=None, width=2):
    p = transform_points(pts, m) if m else list(pts)
    if len(p) >= 2:
        pygame.draw.lines(surf, color, False, p, max(1, int(width)))


def make_gradient(w, h, top, bottom):
    """Vertical colour gradient surface."""
    s = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(s, c, (0, y), (w, y))
    return s


def lerp(a, b, t):
    return a + (b - a) * t


def approach(value, target, step):
    if value < target:
        return min(value + step, target)
    return max(value - step, target)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))
