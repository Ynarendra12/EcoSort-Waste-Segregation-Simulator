"""Food items and the waste they leave behind.  Each is drawn from polygons in
local coordinates and placed with a matrix (translate x rotate x scale)."""
import math
from gfx import poly, rect, circle, ellipse, line, polyline
from transforms import compose, translate, rotate, scale

ITEMS = {
    "chips": dict(label="Chips", waste="Chips packet", bin="dry",
                  tip="Plastic wrappers are DRY waste."),
    "banana": dict(label="Banana", waste="Banana peel", bin="wet",
                   tip="Peels rot into compost - WET waste!"),
    "juice": dict(label="Juice box", waste="Juice carton", bin="recycle",
                  tip="Cartons can be RECYCLED into new paper."),
    "apple": dict(label="Apple", waste="Apple core", bin="wet",
                  tip="Apple cores are WET waste and make compost."),
    "sandwich": dict(label="Sandwich", waste="Paper wrapper", bin="dry",
                     tip="Used paper wrappers go in the DRY bin."),
    "bottle": dict(label="Water bottle", waste="Plastic bottle", bin="recycle",
                   tip="Plastic bottles are RECYCLED into new things."),
}
ORDER = ["chips", "banana", "juice", "apple", "sandwich", "bottle"]


# ------------------------------------------------------------------- food
def _chips(s, m):
    poly(s, (230, 60, 50), [(-15, -22), (15, -22), (18, 22), (-18, 22)], m)
    poly(s, (230, 60, 50), [(-15, -22), (-11, -28), (-7, -22), (-3, -28), (1, -22),
                            (5, -28), (9, -22), (13, -28), (15, -22)], m)
    circle(s, (255, 205, 60), 0, 0, 9, m)
    circle(s, (255, 150, 40), 0, 0, 4, m, None)


def _banana(s, m):
    outer, inner = [], []
    for a in range(195, 346, 10):
        r = math.radians(a)
        outer.append((26 * math.cos(r), -14 - 26 * math.sin(r)))
        inner.append((17 * math.cos(r), -14 - 17 * math.sin(r)))
    poly(s, (255, 226, 60), outer + inner[::-1], m)
    circle(s, (110, 70, 30), outer[0][0], outer[0][1], 3, m, None)
    circle(s, (110, 70, 30), outer[-1][0], outer[-1][1], 3, m, None)


def _juice(s, m):
    rect(s, (255, 150, 40), -14, -20, 28, 40, m)
    rect(s, (255, 255, 255), -14, -4, 28, 8, m, None)
    circle(s, (255, 200, 60), 0, -12, 5, m, None)
    polyline(s, (230, 40, 70), [(6, -20), (9, -34), (16, -34)], m, 3)


def _apple(s, m):
    circle(s, (220, 40, 50), 0, 4, 18, m)
    circle(s, (255, 150, 150), -7, -3, 4, m, None)
    line(s, (110, 70, 30), (0, -14), (2, -25), m, 3)
    ellipse(s, (70, 190, 80), 9, -21, 7, 4, m)


def _sandwich(s, m):
    rect(s, (232, 190, 110), -22, 6, 44, 10, m)
    rect(s, (80, 190, 80), -24, 1, 48, 6, m)
    rect(s, (225, 60, 50), -22, -4, 44, 6, m)
    poly(s, (240, 200, 120), [(-22, -4), (22, -4), (18, -16), (0, -20), (-18, -16)], m)


def _bottle(s, m):
    poly(s, (150, 210, 255), [(-10, -10), (10, -10), (12, 24), (-12, 24)], m)
    poly(s, (150, 210, 255), [(-5, -22), (5, -22), (10, -10), (-10, -10)], m)
    rect(s, (40, 110, 220), -6, -29, 12, 7, m)
    rect(s, (255, 255, 255), -11, 2, 22, 10, m, None)


# ------------------------------------------------------------------ waste
def _w_chips(s, m):
    poly(s, (200, 50, 45), [(-14, -6), (-6, -15), (2, -10), (12, -15), (17, -2),
                            (10, 6), (15, 14), (2, 12), (-8, 17), (-16, 8), (-10, 0)], m)
    line(s, (140, 30, 30), (-8, -4), (4, 4), m, 2)
    line(s, (140, 30, 30), (2, -8), (8, 8), m, 2)
    circle(s, (255, 205, 60), -2, 6, 3, m, None)


def _w_banana(s, m):
    poly(s, (235, 200, 60), [(0, 0), (-22, -6), (-26, 8), (-8, 10)], m)
    poly(s, (235, 200, 60), [(0, 0), (22, -8), (28, 6), (8, 10)], m)
    poly(s, (225, 190, 55), [(0, 0), (-6, 12), (2, 26), (10, 12)], m)
    circle(s, (255, 245, 200), 0, 2, 5, m, None)
    circle(s, (120, 80, 30), -16, 0, 2, m, None)
    circle(s, (120, 80, 30), 18, -1, 2, m, None)


def _w_juice(s, m):
    poly(s, (215, 120, 30), [(-16, -8), (14, -14), (18, 10), (-12, 14)], m)
    line(s, (150, 80, 20), (-10, -2), (10, 4), m, 2)
    polyline(s, (230, 40, 70), [(6, -12), (14, -26), (22, -22)], m, 3)


def _w_apple(s, m):
    poly(s, (240, 225, 170), [(-8, -18), (8, -18), (5, -8), (10, 0), (5, 8), (8, 18),
                              (-8, 18), (-5, 8), (-10, 0), (-5, -8)], m)
    ellipse(s, (90, 50, 30), -2, -1, 2, 3, m, None)
    ellipse(s, (90, 50, 30), 3, 3, 2, 3, m, None)
    line(s, (110, 70, 30), (0, -18), (2, -26), m, 3)


def _w_sandwich(s, m):
    poly(s, (235, 235, 230), [(-18, -4), (-8, -14), (4, -10), (16, -14), (20, 0),
                              (12, 10), (16, 18), (0, 14), (-12, 18), (-20, 8)], m)
    line(s, (200, 60, 50), (-10, -4), (8, 6), m, 2)
    line(s, (200, 60, 50), (-4, -8), (14, 2), m, 2)


def _w_bottle(s, m):
    poly(s, (160, 215, 255), [(-10, -14), (10, -10), (6, -2), (12, 6), (4, 12),
                              (10, 20), (-10, 22), (-6, 12), (-12, 4), (-6, -4)], m)
    rect(s, (40, 110, 220), -6, -24, 12, 7, m)


def _lunchbox(s, m):
    rect(s, (255, 120, 60), -16, -10, 32, 22, m)
    rect(s, (255, 200, 80), -16, -10, 32, 6, m)
    polyline(s, (35, 35, 50), [(-8, -10), (-8, -16), (8, -16), (8, -10)], m, 3)
    circle(s, (255, 255, 255), 0, 3, 3, m, None)


_FOOD = {"chips": _chips, "banana": _banana, "juice": _juice, "apple": _apple,
         "sandwich": _sandwich, "bottle": _bottle, "lunchbox": _lunchbox}
_WASTE = {"chips": _w_chips, "banana": _w_banana, "juice": _w_juice, "apple": _w_apple,
          "sandwich": _w_sandwich, "bottle": _w_bottle}


def draw_item(surf, key, x, y, size=1.0, angle=0.0, waste=False):
    m = compose(translate(x, y), rotate(angle), scale(size, size))
    (_WASTE[key] if waste else _FOOD[key])(surf, m)
