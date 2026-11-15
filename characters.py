"""
Characters.  Each character is built from polygons and circles.  The body is a
hierarchy: the whole character has a base matrix, and arms / legs / tail each
get their own matrix (base x translate to the joint x rotate by the swing angle).
That is how the walking animation is produced.
"""
import math
from gfx import poly, rect, circle, ellipse, line, polyline
from transforms import (compose, translate, scale, rotate, transform_points)
from algorithms import bresenham
from items import draw_item

KINDS = ["duck", "boy", "girl", "cat"]
NAMES = {"duck": "Ducky", "boy": "Raju", "girl": "Meena", "cat": "Kitty"}
MOTTO = {"duck": "Quack! Let's keep ponds clean!",
         "boy": "Ready to be an Eco Hero!",
         "girl": "Clean planet, happy planet!",
         "cat": "Meow! Sort it right!"}

LOOK = {
    "boy": dict(skin=(247, 200, 160), hair=(40, 30, 30), shirt=(70, 130, 230), legs=(60, 90, 170)),
    "girl": dict(skin=(247, 200, 160), hair=(95, 55, 30), shirt=(255, 110, 170), legs=(247, 200, 160)),
    "duck": dict(skin=(255, 219, 60), hair=None, shirt=(90, 200, 255), legs=(255, 150, 30)),
    "cat": dict(skin=(255, 172, 72), hair=None, shirt=(190, 120, 255), legs=(255, 172, 72)),
    "teacher": dict(skin=(240, 190, 150), hair=(60, 40, 30), shirt=(150, 70, 170), legs=(150, 70, 170)),
    "vendor": dict(skin=(230, 180, 140), hair=(50, 50, 50), shirt=(255, 255, 255), legs=(80, 80, 90)),
}
NAVY = (35, 50, 110)
DARK = (30, 25, 25)


def _eye(surf, m, x, y, r=3.6):
    circle(surf, (255, 255, 255), x, y, r, m, (35, 35, 50), 1)
    circle(surf, (20, 20, 30), x + 1.2, y, r * 0.5, m, None)


def draw_head(surf, kind, m, mood="smile"):
    """Head centred on (0, 0) with radius 17, looking to the right."""
    L = LOOK[kind]
    skin = L["skin"]
    if kind == "cat":
        poly(surf, skin, [(-15, -6), (-13, -29), (-2, -14)], m)
        poly(surf, skin, [(2, -14), (13, -29), (15, -6)], m)
        poly(surf, (255, 150, 170), [(-12, -10), (-11, -23), (-5, -14)], m, None)
        poly(surf, (255, 150, 170), [(5, -14), (11, -23), (12, -10)], m, None)
        circle(surf, skin, 0, 0, 17, m)
        for dx in (-5, 0, 5):
            line(surf, (190, 105, 30), (dx, -17), (dx, -10), m, 2)
        _eye(surf, m, 6, -2)
        _eye(surf, m, -6, -2)
        poly(surf, (255, 120, 150), [(-2.5, 4), (2.5, 4), (0, 7)], m, None)
        # whiskers drawn with Bresenham's line algorithm
        sc = max(1, int(abs(m[0][0]) + 0.5))
        for side in (-1, 1):
            for dy in (-1, 3):
                (x0, y0), (x1, y1) = transform_points([(side * 5, 6 + dy), (side * 25, 3 + dy * 2.2)], m)
                for px, py in bresenham(x0, y0, x1, y1):
                    surf.fill((60, 40, 30), (px, py, sc, sc))
        return
    if kind == "duck":
        circle(surf, skin, -3, -18, 5, m)
        circle(surf, skin, 4, -19, 4, m)
        circle(surf, skin, 0, 0, 17, m)
        poly(surf, (255, 140, 0), [(12, 1), (30, 4), (12, 11)], m)
        line(surf, (170, 80, 0), (14, 6), (28, 5), m, 1)
        _eye(surf, m, 6, -5)
        return
    # human heads
    if kind == "girl":
        circle(surf, L["hair"], -4, 2, 19, m)
        circle(surf, L["hair"], -17, 9, 7, m)
        poly(surf, (255, 90, 160), [(-15, -1), (-9, 1), (-15, 5)], m)
        poly(surf, (255, 90, 160), [(-19, -1), (-13, 3), (-19, 7)], m)
    if kind == "vendor":
        pass
    circle(surf, skin, 0, 0, 17, m)
    if L["hair"]:
        arc = [(18 * math.cos(math.radians(a)), 18 * math.sin(math.radians(a)))
               for a in range(180, 361, 15)]
        fringe = [(14, -6), (8, -10), (2, -6), (-4, -11), (-10, -5), (-17, -2)]
        poly(surf, L["hair"], arc + fringe, m, None)
    if kind == "teacher":
        circle(surf, L["hair"], -7, -19, 8, m)
    if kind == "vendor":
        poly(surf, (255, 255, 255), [(-17, -6), (17, -6), (14, -20), (-14, -20)], m)
        poly(surf, (255, 255, 255), [(10, -8), (24, -6), (10, -4)], m)
    _eye(surf, m, 6, -2)
    if kind == "teacher":
        circle(surf, (255, 255, 255), 7, -2, 6, m, (60, 60, 80), 2)
    if kind == "vendor":
        poly(surf, (40, 30, 30), [(1, 6), (12, 6), (10, 9), (3, 9)], m, None)
    else:
        if mood == "cheer":
            poly(surf, (150, 40, 40), [(1, 5), (11, 5), (6, 12)], m)
        else:
            polyline(surf, (150, 40, 40), [(2, 6), (7, 9), (12, 6)], m, 2)


def _arm(surf, shirt, skin, m_arm):
    rect(surf, shirt, -3.8, 0, 7.6, 21, m_arm)
    circle(surf, skin, 0, 24, 4.6, m_arm)


def _leg(surf, color, shoe, m_leg, bare=False):
    rect(surf, color, -4.5, 0, 9, 29, m_leg)
    poly(surf, shoe, [(-5, 27), (11, 27), (11, 38), (-5, 38)], m_leg)


def draw_character(surf, kind, x, y, size=1.0, facing=1, t=0.0, moving=False,
                   outfit="school", arm_front=None, arm_back=None, held=None,
                   mood="smile"):
    """
    Draw a character with its feet at (x, y).
    t        - animation clock (walk cycle phase)
    moving   - swing arms and legs
    outfit   - 'school' (uniform, tie, bag) or 'casual'
    held     - (item_key, is_waste) shown in the front hand
    """
    L = LOOK[kind]
    swing = math.sin(t) * 32 if moving else 0
    bob = abs(math.sin(t)) * 3 if moving else math.sin(t * 0.6) * 0.8
    base = compose(translate(x, y), scale(size * facing, size))
    body = compose(base, translate(0, -bob))
    school = outfit == "school"

    if school:
        shirt = (245, 245, 245)
    elif kind == "teacher" or kind == "vendor":
        shirt = L["shirt"]
    else:
        shirt = L["shirt"]
    skin = L["skin"]

    # pick leg colour
    if kind == "boy":
        legcol = NAVY if school else L["legs"]
    elif kind == "girl":
        legcol = skin
    else:
        legcol = L["legs"]
    shoe = (40, 30, 30)

    fa = arm_front if arm_front is not None else (-55 if held else -swing * 0.8)
    ba = arm_back if arm_back is not None else swing * 0.8

    # cat tail (behind everything)
    if kind == "cat":
        m_tail = compose(body, translate(-8, -42), rotate(-20 + math.sin(t * 0.9) * 18))
        poly(surf, skin, [(-3, 0), (3, 0), (4, -26), (-14, -30), (-16, -22), (-4, -20)], m_tail)
    # backpack
    if school:
        poly(surf, (232, 92, 42), [(-21, -70), (-9, -70), (-9, -38), (-21, -38)], body)
        rect(surf, (200, 70, 30), -21, -58, 12, 8, body, None)
        ellipse(surf, (120, 210, 255), -15, -75, 3.5, 6, body)    # water bottle in side pocket
    # back arm
    m_ba = compose(body, translate(-11, -68), rotate(ba))
    _arm(surf, shirt, skin, m_ba)
    # legs
    m_l1 = compose(body, translate(-5, -38), rotate(swing))
    m_l2 = compose(body, translate(5, -38), rotate(-swing))
    _leg(surf, legcol, shoe, m_l1)
    _leg(surf, legcol, shoe, m_l2)
    # torso (+ outfit details)
    poly(surf, shirt, [(-13, -72), (13, -72), (11, -36), (-11, -36)], body)
    if kind in ("duck", "cat") and school:
        rect(surf, NAVY, -12, -42, 24, 10, body)
    if kind == "girl":
        poly(surf, NAVY if school else (255, 110, 170),
             [(-12, -42), (12, -42), (20, -18), (-20, -18)], body)
    if school and kind not in ("teacher", "vendor"):
        poly(surf, (215, 40, 40), [(-3, -71), (3, -71), (5, -54), (0, -47), (-5, -54)], body)
    if kind == "teacher":
        poly(surf, (250, 210, 90), [(-13, -72), (-4, -72), (13, -40), (13, -36), (4, -36)], body, None)
    if kind == "vendor":
        rect(surf, (240, 240, 245), -11, -56, 22, 20, body)
    # head
    draw_head(surf, kind, compose(body, translate(0, -89)), mood)
    # front arm
    m_fa = compose(body, translate(11, -68), rotate(fa))
    _arm(surf, shirt, skin, m_fa)
    # held item in the hand
    if held:
        key, is_waste = held
        if key == "pointer":
            line(surf, (120, 80, 40), (0, 24), (0, 70), m_fa, 3)
        else:
            (hx, hy), = transform_points([(0, 25)], m_fa)
            draw_item(surf, key, hx + 2 * size * facing, hy - 6 * size, size * 0.68,
                      math.sin(t * 2) * 6, waste=is_waste)


def hand_pos(x, y, size, facing, arm_angle=-55):
    """Screen position of the front hand (used by the eating / dropping animation)."""
    m = compose(translate(x, y), scale(size * facing, size), translate(11, -68), rotate(arm_angle))
    (p,) = transform_points([(0, 25)], m)
    return p


def mouth_pos(x, y, size, facing):
    m = compose(translate(x, y), scale(size * facing, size))
    (p,) = transform_points([(11, -85)], m)
    return p
