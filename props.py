"""Scenery and objects: sun, clouds, trees, houses, bus, cars, traffic light,
school building and the dustbins.  Everything uses matrices from transforms.py."""
import math
import pygame
import gfx
from gfx import poly, rect, circle, ellipse, line, polyline
from transforms import (compose, translate, scale, rotate, shear_x, transform_points,
                        rotate_about)
from algorithms import bresenham, midpoint_circle, scanline_fill
from characters import draw_head
from settings import BIN_INFO
import ui

# ------------------------------------------------------------------- sky
_ring_cache = {}


def _ring(r, color, thick=3):
    """Circle outline built from the midpoint circle algorithm (cached)."""
    key = (r, color, thick)
    if key not in _ring_cache:
        s = pygame.Surface((2 * r + 8, 2 * r + 8), pygame.SRCALPHA)
        for px, py in midpoint_circle(r + 4, r + 4, r):
            s.fill(color, (px, py, thick, thick))
        _ring_cache[key] = s
    return _ring_cache[key]


def draw_sun(surf, x, y, t, r=36):
    ring = _ring(r + 8, (255, 170, 0))
    surf.blit(ring, ring.get_rect(center=(x, y)))
    circle(surf, (255, 222, 40), x, y, r, None, (255, 170, 0), 3)
    for i in range(12):                     # rotating rays: rotation + Bresenham
        m = compose(translate(x, y), rotate(i * 30 + t * 12))
        (x1, y1), (x2, y2) = transform_points([(r + 14, 0), (r + 30, 0)], m)
        for px, py in bresenham(x1, y1, x2, y2):
            surf.fill((255, 200, 30), (px - 1, py - 1, 3, 3))


def draw_cloud(surf, x, y, size=1.0, color=(255, 255, 255)):
    for dx, dy, r in ((0, 0, 24), (-26, 8, 18), (26, 8, 20), (8, -12, 20), (-8, 12, 16), (12, 12, 16)):
        pygame.draw.circle(surf, color, (int(x + dx * size), int(y + dy * size)), int(r * size))


class Clouds:
    def __init__(self, n=5, speed=14):
        self.c = [[i * 210 + 60, 60 + (i * 53) % 110, 0.7 + (i % 3) * 0.25] for i in range(n)]
        self.speed = speed

    def update(self, dt):
        for c in self.c:
            c[0] += self.speed * c[2] * dt
            if c[0] > 1050:
                c[0] = -90

    def draw(self, surf):
        for x, y, s in self.c:
            draw_cloud(surf, x, y, s)


def draw_hills(surf, cam, base_y, color=(120, 190, 120), factor=0.3, seed=0):
    off = -(cam * factor)
    pts = [(0, base_y + 60)]
    for i in range(-2, 14):
        px = i * 130 + off % 130 - 130
        pts.append((px, base_y - 40 - ((i + seed) * 37) % 50))
        pts.append((px + 65, base_y - 10))
    pts.append((1100, base_y + 60))
    pygame.draw.polygon(surf, color, pts)


# ------------------------------------------------------------------ trees
def draw_tree(surf, x, base_y, size=1.0, sway=0.0, flip=False, tint=0):
    """Swaying tree.  Shear transformation bends the top.  flip=True reflects it
    about the base line (used for the pond reflection)."""
    fy = -1 if flip else 1
    m = compose(translate(x, base_y), scale(size, size * fy), shear_x(sway))
    g = (50, 160, 70)
    g2 = (70, 185, 90)
    poly(surf, (115, 78, 45), [(-7, 0), (7, 0), (5, -42), (-5, -42)], m)
    for cx, cy, r, c in ((-20, -52, 20, g), (20, -52, 20, g), (0, -70, 26, g2), (0, -50, 24, g)):
        circle(surf, c, cx, cy, r, m)


def draw_shop(surf, x, base_y, w, h, color, label=None):
    rect(surf, color, x, base_y - h, w, h)
    rect(surf, (90, 90, 110), x - 4, base_y - h - 8, w + 8, 10)
    for i in range(max(1, int(w // 50))):
        rect(surf, (190, 230, 255), x + 10 + i * 46, base_y - h + 18, 30, 26)
    rect(surf, (120, 70, 40), x + w / 2 - 12, base_y - 38, 24, 38)


# ------------------------------------------------------------- house / gate
def draw_home(surf, x, base_y):
    # compound wall
    rect(surf, (235, 210, 170), x - 10, base_y - 36, 380, 36)
    # house body
    rect(surf, (255, 228, 170), x + 20, base_y - 190, 250, 190)
    poly(surf, (210, 80, 70), [(x, base_y - 190), (x + 145, base_y - 280), (x + 290, base_y - 190)])
    rect(surf, (190, 70, 60), x + 215, base_y - 270, 28, 60)
    # door
    rect(surf, (130, 80, 50), x + 115, base_y - 112, 56, 112)
    circle(surf, (255, 210, 60), x + 160, base_y - 55, 4)
    # windows
    for wx in (x + 45, x + 205):
        rect(surf, (170, 225, 255), wx, base_y - 150, 50, 50)
        line(surf, (35, 35, 50), (wx + 25, base_y - 150), (wx + 25, base_y - 100), None, 2)
        line(surf, (35, 35, 50), (wx, base_y - 125), (wx + 50, base_y - 125), None, 2)
    # nameplate
    rect(surf, (255, 255, 255), x + 105, base_y - 138, 76, 18)
    ui.text(surf, "HOME", 15, (60, 60, 80), (x + 143, base_y - 129))
    # flower pots
    for fx in (x + 80, x + 190):
        rect(surf, (200, 100, 60), fx, base_y - 16, 22, 16)
        circle(surf, (255, 90, 140), fx + 11, base_y - 24, 8)


def draw_gate(surf, x, base_y, open_amt):
    """Sliding gate: two leaves translate apart (translation)."""
    for side in (-1, 1):
        sh = side * open_amt * 52
        m = translate(x + sh, base_y)
        for i in range(5):
            rect(surf, (90, 100, 120), i * 11 * side + (0 if side == 1 else -52), -92, 6, 92, m, None)
        rect(surf, (70, 80, 100), (0 if side == 1 else -54), -88, 54, 6, m)
        rect(surf, (70, 80, 100), (0 if side == 1 else -54), -22, 54, 6, m)
    rect(surf, (235, 210, 170), x - 76, base_y - 108, 22, 108)
    rect(surf, (235, 210, 170), x + 54, base_y - 108, 22, 108)


# -------------------------------------------------------------------- bus
SEAT_X = [-92, -54, -16, 22]


def draw_bus(surf, x, base_y, wheel_ang=0.0, door_scale=1.0, seats=None, size=1.0,
             you_seat=None, t=0.0):
    """School bus facing right.  Wheels rotate, door leaf scales (opens) about
    its hinge, passengers are heads drawn with draw_head()."""
    M = compose(translate(x, base_y), scale(size, size))
    seats = seats or [None] * 4
    yellow = (255, 196, 0)
    poly(surf, yellow, [(-114, -20), (-114, -102), (96, -102), (114, -74), (114, -20)], M)
    rect(surf, (35, 35, 50), -114, -40, 228, 7, M, None)
    # windows + passengers
    for i, cx in enumerate(SEAT_X):
        rect(surf, (190, 228, 255), cx - 16, -94, 32, 34, M)
        if seats[i]:
            hm = compose(M, translate(cx, -72), scale(0.62, 0.62))
            draw_head(surf, seats[i], hm)
            if you_seat == i:
                ui.text(surf, "YOU", 14, (255, 255, 255),
                        transform_points([(cx, -108)], M)[0], shadow=(0, 0, 0))
        rect(surf, (190, 228, 255), cx - 16, -94, 32, 34, M, (35, 35, 50), 2)
    # door
    rect(surf, (45, 45, 65), 62, -98, 40, 78, M)
    hinge = compose(M, translate(102, 0), scale(door_scale, 1), translate(-102, 0))
    rect(surf, (170, 215, 245), 62, -98, 40, 78, hinge)
    line(surf, (35, 35, 50), (82, -98), (82, -20), hinge, 2)
    rect(surf, (200, 200, 210), 60, -20, 44, 6, M)               # step
    # front / back details
    poly(surf, (190, 228, 255), [(102, -96), (114, -74), (114, -60), (102, -60)], M)
    circle(surf, (255, 255, 160), 111, -32, 5, M)
    rect(surf, (230, 40, 40), -114, -34, 5, 10, M, None)
    # label
    ui.text(surf, "SCHOOL BUS", max(10, int(13 * size)), (30, 30, 40),
            transform_points([(-30, -48)], M)[0])
    # wheels (rotation)
    for wx in (-66, 62):
        pygame.draw.circle(surf, (35, 35, 50),
                           tuple(int(v) for v in transform_points([(wx, -20)], M)[0]), int(24 * size))
        wm = compose(M, translate(wx, -18), rotate(wheel_ang))
        circle(surf, (35, 35, 40), 0, 0, 19, wm, (10, 10, 10))
        circle(surf, (190, 190, 200), 0, 0, 9, wm, (60, 60, 70))
        for a in (0, 60, 120):
            line(surf, (90, 90, 100), (-9, 0), (9, 0), compose(wm, rotate(a)), 3)


def bus_door_world(x, size=1.0):
    return x + 82 * size


def draw_car(surf, x, base_y, color, wheel_ang=0.0, size=0.8, facing=-1):
    M = compose(translate(x, base_y), scale(size * facing, size))
    poly(surf, color, [(-48, -14), (-48, -30), (-30, -34), (-18, -52), (22, -52), (34, -34), (48, -30), (48, -14)], M)
    poly(surf, (190, 228, 255), [(-14, -34), (-6, -48), (18, -48), (26, -34)], M)
    line(surf, (35, 35, 50), (6, -48), (6, -34), M, 2)
    circle(surf, (255, 255, 160), 46, -24, 4, M)
    for wx in (-28, 28):
        wm = compose(M, translate(wx, -12), rotate(wheel_ang))
        circle(surf, (35, 35, 40), 0, 0, 12, wm, (10, 10, 10))
        line(surf, (190, 190, 200), (-8, 0), (8, 0), wm, 3)


def draw_traffic_light(surf, x, base_y, state, countdown=None):
    rect(surf, (60, 60, 75), x - 4, base_y - 150, 8, 150)
    rect(surf, (30, 30, 40), x - 16, base_y - 190, 32, 80, None, (255, 255, 255))
    poly(surf, (30, 30, 40), [(x - 16, base_y - 190), (x + 16, base_y - 190), (x + 16, base_y - 110), (x - 16, base_y - 110)])
    cols = {"red": (255, 50, 50), "yellow": (255, 215, 0), "green": (50, 225, 90)}
    for name, cy in (("red", -172), ("yellow", -150), ("green", -128)):
        col = cols[name] if state == name else (65, 65, 70)
        circle(surf, col, x, base_y + cy, 9, None, (10, 10, 10), 1)
        if state == name:
            pygame.draw.circle(surf, col, (x, int(base_y + cy)), 14, 2)
    if countdown is not None:
        ui.text(surf, str(countdown), 44, (255, 70, 70), (x + 44, base_y - 150), shadow=(0, 0, 0))


# ---------------------------------------------------------------- school
def draw_school(surf, x, base_y, t=0.0):
    """School building centred around x; big board at the entrance."""
    rect(surf, (255, 214, 160), x - 200, base_y - 190, 400, 190)
    rect(surf, (225, 90, 80), x - 215, base_y - 205, 430, 20)
    for i in range(4):
        for wx in (x - 175 + i * 50, x + 25 + i * 50):
            rect(surf, (180, 225, 255), wx, base_y - 150, 34, 36)
            rect(surf, (180, 225, 255), wx, base_y - 90, 34, 36)
    rect(surf, (255, 235, 200), x - 50, base_y - 120, 100, 120)
    pygame.draw.circle(surf, (120, 70, 40), (x, base_y - 70), 42)
    rect(surf, (120, 70, 40), x - 42, base_y - 70, 84, 70, None, None)
    pygame.draw.line(surf, (60, 40, 20), (x, base_y - 112), (x, base_y), 3)
    # big sign board
    rect(surf, (35, 110, 70), x - 130, base_y - 262, 260, 54, None, (255, 255, 255), 4)
    ui.text(surf, "MANAV RACHNA", 24, (255, 255, 255), (x, base_y - 245), shadow=(0, 0, 0))
    ui.text(surf, "INTERNATIONAL SCHOOL", 18, (255, 235, 140), (x, base_y - 221), shadow=(0, 0, 0))
    # flag waving (shear)
    fm = compose(translate(x + 170, base_y - 330))
    line(surf, (80, 80, 90), (x + 170, base_y - 330), (x + 170, base_y - 205), None, 4)
    wave = math.sin(t * 4) * 0.25
    poly(surf, (255, 140, 40), [(0, 0), (40, 0), (40, 12), (0, 12)], compose(fm, shear_x(wave)))
    poly(surf, (255, 255, 255), [(0, 12), (40, 12), (40, 24), (0, 24)], compose(fm, shear_x(wave)))
    poly(surf, (40, 170, 70), [(0, 24), (40, 24), (40, 36), (0, 36)], compose(fm, shear_x(wave)))


# ------------------------------------------------------------------ bins
_bin_shape = [(-38, -95), (38, -95), (32, 0), (-32, 0)]
_bin_spans = scanline_fill(_bin_shape)       # computed once with scan-line fill


def draw_bin(surf, x, base_y, kind, lid_open=0.0, shake=0.0, size=1.0, highlight=False):
    """Dustbin: body filled with the scan-line spans; the lid rotates about its
    hinge; wrong answers shake it with a shear transformation."""
    info = BIN_INFO[kind]
    M = compose(translate(x, base_y), shear_x(shake), scale(size, size))
    if highlight:
        pygame.draw.ellipse(surf, (255, 255, 255), pygame.Rect(x - 62 * size, base_y - 8, 124 * size, 18), 3)
    for yy, xa, xb in _bin_spans:                       # scan-line fill
        p0, p1 = transform_points([(xa, yy), (xb + 1, yy)], M)
        pygame.draw.line(surf, info["color"], p0, p1, max(1, int(size + 0.5)))
    poly(surf, None or info["color"], _bin_shape, M, (25, 25, 35), 3)
    for rx in (-16, 0, 16):                             # ribs
        line(surf, info["dark"], (rx * 0.9, -48), (rx * 0.75, -6), M, 3)
    rect(surf, (255, 255, 255), -30, -90, 60, 30, M, (25, 25, 35), 2)
    ui.text(surf, info["label"], max(10, int((17 if len(info["label"]) < 6 else 13) * size)),
            info["dark"], transform_points([(0, -75)], M)[0])
    lm = compose(M, rotate_about(-lid_open, -42, -99))
    poly(surf, info["dark"], [(-44, -105), (44, -105), (44, -95), (-44, -95)], lm, (25, 25, 35), 3)
    rect(surf, (230, 230, 240), -8, -111, 16, 7, lm)
    ui.text(surf, info["desc"], max(10, int(13 * size)), (255, 255, 255),
            transform_points([(0, 16)], M)[0], shadow=(0, 0, 0))


def draw_bin_sign(surf, x, y, w=330):
    """Big heading board above the dustbins."""
    rect(surf, (60, 60, 80), x - 5, y, 10, 40)
    pygame.draw.rect(surf, (35, 35, 50), (x - w // 2 - 3, y - 47, w + 6, 52), border_radius=10)
    pygame.draw.rect(surf, (255, 235, 90), (x - w // 2, y - 44, w, 46), border_radius=8)
    ui.text(surf, "DUSTBINS", 34, (35, 35, 50), (x, y - 21))
