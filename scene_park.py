"""Park Picnic: same waste-sorting game, different place."""
import math
import pygame
import ui
import props
from gfx import make_gradient, rect, circle, poly, line, ellipse
from scene_base import Scene
from settings import WIDTH, HEIGHT
from characters import KINDS, draw_character
from binlevel import BinLevel
from items import draw_item
from transforms import compose, translate, rotate, rotate_about, reflect_x, shear_x, scale
from algorithms import dda_line

POND = pygame.Rect(215, 392, 330, 78)


class ParkLevel(BinLevel):
    level_id = "park"
    title = "Park Picnic"
    source_name = "Picnic basket"
    menu_name = "picnic basket"
    menu_title = "Picnic Basket"
    goal = 5
    uniform = False
    concepts = [
        "Pond reflection: REFLECTION matrix (scale 1,-1 about the shore line) drawn then faded",
        "Windmill blades: ROTATION about the hub      Trees / grass / flag: SHEAR (sway)",
        "Ball bouncing: TRANSLATION along a parabola  Butterflies: rotation + scaling (wing flap)",
        "Fence rails: DDA line algorithm              Sun ring: MIDPOINT circle algorithm",
        "Waste drop: arc (translation) + shrinking (scale) + spinning (rotation) + lid rotation",
    ]

    def __init__(self, game):
        super().__init__(game)
        self.sky = make_gradient(WIDTH, HEIGHT, (105, 185, 255), (215, 240, 255))
        self.clouds = props.Clouds(6, 12)
        self.static = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.paint_static(self.static)
        others = [k for k in KINDS if k != self.kind]
        self.kids = (others[0], others[1])
        self.mask = pygame.Surface(POND.size, pygame.SRCALPHA)
        pygame.draw.ellipse(self.mask, (255, 255, 255, 255), self.mask.get_rect())
        self.refl = pygame.Surface(POND.size, pygame.SRCALPHA)

    def paint_static(self, s):
        # picket fence: rails drawn with the DDA line algorithm
        for y in (330, 348):
            for px, py in dda_line(0, y, WIDTH, y):
                s.fill((250, 250, 250), (px, py, 1, 4))
        for x in range(10, WIDTH, 30):
            rect(s, (250, 250, 250), x, 318, 14, 44, None, (150, 150, 160), 1)

    def update_background(self, dt):
        self.clouds.update(dt)

    def draw_background(self, surf):
        t = self.t
        surf.blit(self.sky, (0, 0))
        props.draw_sun(surf, 120, 100, t, 32)
        self.clouds.draw(surf)
        props.draw_hills(surf, 0, 290, (150, 205, 150), 0, 0)
        props.draw_hills(surf, 0, 330, (110, 185, 115), 0, 3)
        self.draw_windmill(surf, 810, 330, t)
        pygame.draw.rect(surf, (96, 190, 100), (0, 330, WIDTH, 270))
        surf.blit(self.static, (0, 0))
        pygame.draw.rect(surf, (118, 200, 108), (0, 470, WIDTH, 130))
        # pond + reflection
        pygame.draw.ellipse(surf, (90, 170, 235), POND)
        self.refl.fill((0, 0, 0, 0))
        for i, x in enumerate((POND.left + 70 - POND.left, POND.right - 70 - POND.left)):
            sway = math.sin(t * 2 + i * 2) * 0.07
            props.draw_tree(self.refl, x, 0, 0.8, sway, flip=True)
        # a reflected sun-glow
        pygame.draw.circle(self.refl, (255, 240, 160), (POND.width // 2, 30), 10)
        self.refl.blit(self.mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.refl.set_alpha(150)
        surf.blit(self.refl, POND.topleft)
        for k in range(3):
            w = 60 + 40 * ((t * 0.6 + k * 0.33) % 1)
            pygame.draw.ellipse(surf, (200, 230, 255), (POND.centerx - w / 2 + k * 10, POND.centery + 6 - w / 10, w, w / 5), 1)
        pygame.draw.ellipse(surf, (60, 140, 200), POND, 3)
        # trees on the far shore (swaying with shear)
        for i, x in enumerate((POND.left + 70, POND.right - 70)):
            props.draw_tree(surf, x, POND.top, 0.8, math.sin(t * 2 + i * 2) * 0.07)
        for i, (x, s) in enumerate(((60, 1.2), (150, 0.9), (610, 1.0))):
            props.draw_tree(surf, x, 400 + i * 4, s, math.sin(t * 2 + i) * 0.07)
        # swaying grass tufts (shear)
        for i in range(14):
            gx = 20 + i * 70
            m = compose(translate(gx, 478), shear_x(math.sin(t * 3 + i) * 0.4))
            for dx in (-5, 0, 5):
                line(surf, (60, 150, 70), (dx, 0), (dx, -14), m, 3)
        self.draw_butterflies(surf, t)
        self.draw_kids(surf, t)

    def draw_windmill(self, surf, x, base, t):
        poly(surf, (240, 225, 200), [(x - 22, base), (x + 22, base), (x + 12, base - 110), (x - 12, base - 110)])
        poly(surf, (200, 80, 70), [(x - 16, base - 110), (x + 16, base - 110), (x, base - 134)])
        for a in (0, 90, 180, 270):
            m = compose(translate(x, base - 100), rotate(a + t * 40))
            poly(surf, (250, 250, 250), [(0, -4), (52, -4), (52, 10), (0, 4)], m)
        circle(surf, (120, 80, 50), x, base - 100, 7)

    def draw_butterflies(self, surf, t):
        for i in range(3):
            cx = 330 + i * 150 + math.sin(t * 0.8 + i) * 50
            cy = 360 + math.sin(t * 1.7 + i * 2) * 25
            flap = abs(math.sin(t * 9 + i))
            for side in (-1, 1):
                m = compose(translate(cx, cy), scale(max(0.15, flap) * side, 1))
                poly(surf, (255, 150, 60) if i % 2 else (230, 90, 220),
                     [(0, 0), (12, -9), (14, 3), (3, 6)], m)

    def draw_kids(self, surf, t):
        # two NPC kids playing catch with a bouncing ball
        draw_character(surf, self.kids[0], 380, 515, 1.05, 1, t + 1, False, "casual",
                       arm_front=-60 + math.sin(t * 3) * 10)
        draw_character(surf, self.kids[1], 560, 515, 1.05, -1, t + 2, False, "casual",
                       arm_front=-60 + math.cos(t * 3) * 10)
        u = (t * 0.7) % 1.0
        bx = 395 + 165 * (u if int(t * 0.7) % 2 == 0 else 1 - u)
        by = 470 - math.sin(u * math.pi) * 70
        circle(surf, (255, 90, 90), bx, by, 8)
        circle(surf, (255, 255, 255), bx - 2, by - 2, 3, None, None)

    def draw_source(self, surf):
        # picnic blanket (checked) + basket
        pts = [(40, 508), (300, 508), (330, 556), (10, 556)]
        poly(surf, (240, 90, 90), pts)
        for i in range(7):
            x0 = 40 + i * 37
            poly(surf, (255, 255, 255), [(x0, 508), (x0 + 16, 508), (x0 + 16 - 15 + i * 0, 556), (x0 - 15, 556)], None, None)
        poly(surf, None or (240, 90, 90), pts, None, (150, 40, 40), 3)
        rect(surf, (190, 130, 70), 120, 458, 90, 52)
        for yy in (470, 484, 498):
            line(surf, (140, 90, 50), (120, yy), (210, yy), None, 2)
        line(surf, (140, 90, 50), (125, 458), (165, 428), None, 4)
        line(surf, (140, 90, 50), (205, 458), (165, 428), None, 4)
        ui.text(surf, "PICNIC", 18, (255, 255, 255), (165, 484), shadow=(0, 0, 0))
        for i, k in enumerate(("chips", "banana", "juice")):
            draw_item(surf, k, 60 + i * 34, 520, 0.8)

    def source_item_pos(self):
        return (165, 470)

    def draw_hud(self, surf):
        super().draw_hud(surf)


class ParkScene(Scene):
    concepts = ParkLevel.concepts

    def __init__(self, game):
        super().__init__(game)
        self.level = ParkLevel(game)

    def menu_blocking_escape(self):
        if self.level.menu_open:
            self.level.menu_open = False
            return True
        return False

    def handle_event(self, e):
        self.level.handle_event(e)

    def update(self, dt):
        self.level.update(dt)

    def draw(self, surf):
        self.level.draw(surf)
