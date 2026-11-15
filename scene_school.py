"""
School Day:  Home -> Bus ride (traffic light) -> Arrive at school -> Classroom
             -> Canteen (waste segregation game)
"""
import math
import random
import pygame
import ui
import props
from gfx import make_gradient, approach, clamp, lerp, rect, circle, poly, line
from scene_base import Scene
from settings import WIDTH, HEIGHT
from characters import KINDS, draw_character
from binlevel import BinLevel, FLOOR_Y
from items import draw_item
from transforms import window_to_viewport, compose, translate, rotate_about
from algorithms import cohen_sutherland, bresenham

BUS_SIZE = 1.35
# ----- home layout
HOME_Y = 505            # y of the home compound
WALK_Y = 553            # y on the pavement beside the bus
HOME_BUS_X = 770
HOME_BUS_Y = 580
GATE_X = 430
CH_SIZE = 0.95
# ----- ride layout
ANCHOR = 420
BUS_Y = 574
FAR_LANE_Y = 508
CRUISE = 235
ROUTE_START = 300
STOP_FRONT = 2240
LIGHT_X = 2350
SCHOOL_STOP = 3900
SCHOOL_X = 4230
FRONT_OFF = 114 * BUS_SIZE
DOOR_OFF = 82 * BUS_SIZE


class SchoolScene(Scene):
    concepts = [
        "Gate slides open: TRANSLATION          Bus door opens: SCALING about its hinge",
        "Wheels / sun rays / bell: ROTATION about a pivot (T x R x T^-1 = composite transform)",
        "Walking character: HIERARCHICAL modelling (arms and legs rotate about joints)",
        "Road dashes: BRESENHAM line + COHEN-SUTHERLAND clipping to the screen window",
        "Mini-map: WINDOW-to-VIEWPORT mapping       Trees swaying: SHEAR",
        "Sun ring: MIDPOINT circle algorithm        Dustbin body: SCAN-LINE polygon fill",
        "Camera follows the bus: world scrolls with a TRANSLATION (parallax clouds and hills)",
    ]

    def __init__(self, game):
        super().__init__(game)
        self.kind = game.character
        self.t = 0.0
        self.phase = "home"
        self.fade, self.fade_dir, self.fade_to = 0.0, 0, None
        self.sky = make_gradient(WIDTH, HEIGHT, (105, 185, 255), (215, 240, 255))
        self.clouds = props.Clouds(6, 10)
        self.rng = random.Random(5)
        others = [k for k in KINDS if k != self.kind]
        self.others = others
        self.seats = [others[0], others[1], None, others[2]]
        self.you_seat = 2
        self.toast = ui.Toast()
        self.msg_t = 0
        # ---- home state
        self.px, self.py = 175.0, float(HOME_Y)
        self.facing = 1
        self.walk_t = 0.0
        self.moving = False
        self.gate_open = 0.0
        self.door_scale = 1.0
        self.wheel = 0.0
        self.board = None
        self.board_t = 0.0
        self.you_size = CH_SIZE
        self.you_visible = True
        self.intro_t = 0.0
        # ---- ride state
        self.bus_x = float(ROUTE_START)
        self.speed = 0.0
        self.lstate = "wait"       # wait -> yellow -> red -> done
        self.ltimer = 0.0
        self.red_started = False
        self.light_shown = "green"
        self.make_world()
        # ---- arrive state
        self.arr_t = 0.0
        self.walkers = []
        # ---- class state
        self.ct = 0.0
        self.bell_t = -1.0
        self.rang = False
        self.level = None
        self.toast.show("Good morning! Bag, lunch box and water bottle are packed. Walk to the bus ->", dur=6)

    # ================================================================ world
    def make_world(self):
        r = self.rng
        self.trees, self.shops, self.cars = [], [], []
        x = -150.0
        while x < 4800:
            self.trees.append((x + r.uniform(0, 50), r.uniform(0.8, 1.25), r.uniform(0, 6)))
            x += r.uniform(120, 200)
        x = 100.0
        pal = [(255, 190, 150), (170, 215, 255), (255, 235, 150), (200, 235, 190), (240, 180, 210)]
        while x < 3800:
            w, h = r.choice([90, 110, 130]), r.choice([70, 90, 110])
            self.shops.append((x, w, h, r.choice(pal)))
            x += w + r.uniform(25, 70)
        for i in range(5):
            self.cars.append(dict(x=ROUTE_START + 500 + i * 800 + r.uniform(0, 200), v=r.uniform(120, 190),
                                  color=r.choice([(220, 60, 60), (60, 120, 220), (80, 190, 110), (240, 240, 245), (150, 90, 200)]),
                                  wheel=0.0))

    # ================================================================ phases
    def goto(self, name):
        if self.fade_dir == 0:
            self.fade_dir, self.fade_to = 1, name

    def start_phase(self, name):
        self.phase = name
        if name == "ride":
            self.door_scale = 1.0
            self.toast.show("The bus is on its way to school. Watch the traffic light!", dur=4)
        elif name == "class":
            self.ct = 0.0
        elif name == "canteen":
            self.level = CanteenLevel(self.game)

    def skip(self):
        if self.phase == "ride":
            self.bus_x, self.speed, self.lstate = SCHOOL_STOP - 1, 0, "done"
        elif self.phase == "arrive":
            self.goto("class")
        elif self.phase == "class":
            if self.ct < 9.5:
                self.ct = 9.5
            else:
                self.goto("canteen")

    def menu_blocking_escape(self):
        if self.phase == "canteen" and self.level and self.level.menu_open:
            self.level.menu_open = False
            return True
        return False

    # ================================================================ events
    def handle_event(self, e):
        if self.phase == "canteen" and self.level:
            self.level.handle_event(e)
        elif e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_n):
            self.skip()

    # ================================================================ update
    def update(self, dt):
        self.t += dt
        self.clouds.update(dt)
        self.toast.update(dt)
        if self.fade_dir == 1:
            self.fade += dt * 2.2
            if self.fade >= 1:
                self.fade, self.fade_dir = 1.0, -1
                self.start_phase(self.fade_to)
        elif self.fade_dir == -1:
            self.fade -= dt * 2.2
            if self.fade <= 0:
                self.fade, self.fade_dir = 0.0, 0
        if self.phase == "home":
            self.update_home(dt)
        elif self.phase in ("ride", "arrive"):
            self.update_ride(dt)
        elif self.phase == "class":
            self.update_class(dt)
        elif self.phase == "canteen":
            self.level.update(dt)

    # ---- home
    def update_home(self, dt):
        door_x = HOME_BUS_X + DOOR_OFF
        self.intro_t += dt
        self.gate_open = approach(self.gate_open, 1.0 if 330 < self.px < 560 else 0.0, dt * 1.6)
        near = self.px > door_x - 190
        self.door_scale = approach(self.door_scale, 0.1 if near else 1.0, dt * 2.2)
        if self.board is None:
            d = self.game.input_dir()
            self.moving = d != 0
            if d:
                self.facing = d
                self.walk_t += dt * 11
                self.px = clamp(self.px + d * 190 * dt, 70, door_x)
            else:
                self.walk_t += dt * 2
            # walk down from the gate onto the pavement as we leave the compound
            self.py = HOME_Y + clamp((self.px - 450) / 80, 0, 1) * (WALK_Y - HOME_Y)
            if self.px >= door_x - 6 and self.door_scale < 0.2:
                self.board, self.board_t = "step", 0.0
                self.moving = False
        elif self.board == "step":
            self.board_t += dt
            u = clamp(self.board_t / 0.8, 0, 1)
            self.you_size = lerp(CH_SIZE, 0.55, u)
            self.py = WALK_Y - 28 * u
            if u >= 1:
                self.board, self.board_t = "wait", 0.0
                self.you_visible = False
                self.seats[self.you_seat] = self.kind
        elif self.board == "wait":
            self.board_t += dt
            if self.board_t > 0.6:
                self.door_scale = approach(self.door_scale, 1.0, dt * 2.2)
            if self.board_t > 1.6:
                self.goto("ride")
        self.wheel += 0

    # ---- ride + arrive (shared world)
    def update_ride(self, dt):
        front = self.bus_x + FRONT_OFF
        dist = STOP_FRONT - front
        if self.phase == "ride":
            if self.lstate == "wait" and 0 < dist < 460:
                self.lstate, self.ltimer = "yellow", 1.3
            elif self.lstate == "yellow":
                self.ltimer -= dt
                if self.ltimer <= 0:
                    self.lstate, self.red_started = "red", False
                    self.game.sounds.play("honk")
            elif self.lstate == "red":
                if not self.red_started and self.speed < 3:
                    self.red_started, self.ltimer = True, 5.0
                elif self.red_started:
                    self.ltimer -= dt
                    if self.ltimer <= 0:
                        self.lstate = "done"
            self.light_shown = {"wait": "green", "yellow": "yellow", "red": "red", "done": "green"}[self.lstate]
            # target speed
            target = CRUISE
            if self.lstate in ("yellow", "red"):
                target = clamp(dist * 1.6, 0, CRUISE)
            school_dist = SCHOOL_STOP - self.bus_x
            if self.lstate == "done" or self.bus_x > STOP_FRONT:
                target = min(CRUISE, school_dist * 1.6)
            rate = 150 if target > self.speed else 700
            self.speed = approach(self.speed, target, rate * dt)
            if self.lstate in ("yellow", "red") and dist < 0.5:
                self.speed = 0
                self.bus_x = STOP_FRONT - FRONT_OFF
            if school_dist < 1.0 and self.lstate == "done":
                self.speed, self.bus_x = 0, float(SCHOOL_STOP)
                self.phase, self.arr_t = "arrive", 0.0
                self.setup_walkers()
                self.toast.show("We reached school! Everyone gets down from the bus.", dur=4)
            self.bus_x += self.speed * dt
            self.wheel += self.speed * dt / (19 * BUS_SIZE) * 57.3
            if self.lstate == "wait" and dist > 600:
                pass
        else:
            self.update_arrive(dt)
        # traffic in the other lane
        cam = self.bus_x - ANCHOR
        for c in self.cars:
            if self.phase == "ride":
                c["x"] -= c["v"] * dt
                c["wheel"] -= c["v"] * dt / 12 * 57.3
            if c["x"] < cam - 160:
                c["x"] = cam + WIDTH + self.rng.uniform(150, 1000)

    def setup_walkers(self):
        order = [(self.others[0], 0), (self.others[1], 1), (self.kind, 2), (self.others[2], 3)]
        self.walkers = []
        for k, seat in order:
            self.walkers.append(dict(kind=k, seat=seat, delay=1.6 + len(self.walkers) * 1.5,
                                     me=(seat == self.you_seat), p=0.0, wt=0.0))

    def update_arrive(self, dt):
        self.arr_t += dt
        self.door_scale = approach(self.door_scale, 0.1 if self.arr_t > 0.6 else 1.0, dt * 2.2)
        for w in self.walkers:
            p = (self.arr_t - w["delay"]) / 3.2
            w["p"] = clamp(p, 0, 1)
            if p > 0:
                self.seats[w["seat"]] = None
                w["wt"] += dt * 9
            if w["me"] and p >= 1:
                self.goto("class")

    # ---- class
    def update_class(self, dt):
        self.ct += dt
        if self.ct >= 9.5 and not self.rang:
            self.rang = True
            self.bell_t = 0.0
            self.game.sounds.play("bell")
        if self.rang:
            self.bell_t += dt
        if self.ct >= 12.5:
            self.goto("canteen")

    # ================================================================ drawing
    def draw(self, surf):
        if self.phase == "home":
            self.draw_home(surf)
        elif self.phase in ("ride", "arrive"):
            self.draw_world(surf)
        elif self.phase == "class":
            self.draw_class(surf)
        elif self.phase == "canteen":
            self.level.draw(surf)
        if self.phase != "canteen":
            self.toast.draw(surf, 62)
            self.draw_banner(surf)
        if self.fade > 0:
            ov = pygame.Surface((WIDTH, HEIGHT))
            ov.set_alpha(int(255 * self.fade))
            surf.blit(ov, (0, 0))

    def draw_banner(self, surf):
        names = {"home": "1. Home", "ride": "2. Bus ride", "arrive": "3. At school",
                 "class": "4. Classroom", "canteen": "5. Canteen"}
        ui.panel(surf, (0, 0, WIDTH, 40), (20, 30, 50), 190, 0)
        ui.text(surf, "School Day  -  " + names[self.phase], 24, (255, 235, 120), (14, 20), "midleft")
        ui.text(surf, "Space = skip this part     Esc = back to places", 17, (200, 210, 230), (WIDTH - 12, 20), "midright")

    # ---- home
    def draw_home(self, surf):
        surf.blit(self.sky, (0, 0))
        props.draw_sun(surf, 860, 100, self.t, 32)
        self.clouds.draw(surf)
        props.draw_hills(surf, 0, 330, (130, 200, 130), 0, 2)
        pygame.draw.rect(surf, (96, 190, 100), (0, 330, WIDTH, 175))
        for i, (x, s) in enumerate(((620, 1.0), (700, 0.8), (900, 1.15), (560, 0.7))):
            props.draw_tree(surf, x, 500, s, math.sin(self.t * 2 + i) * 0.07)
        pygame.draw.rect(surf, (205, 205, 215), (0, HOME_Y, WIDTH, 50))
        pygame.draw.rect(surf, (70, 72, 80), (0, 555, WIDTH, 45))
        for x in range(0, WIDTH, 70):
            pygame.draw.rect(surf, (255, 255, 255), (x, 582, 36, 4))
        props.draw_home(surf, 20, HOME_Y)
        props.draw_gate(surf, GATE_X, HOME_Y, self.gate_open)
        props.draw_bus(surf, HOME_BUS_X, HOME_BUS_Y, self.wheel, self.door_scale, self.seats,
                       BUS_SIZE, self.you_seat if self.seats[self.you_seat] else None)
        if self.you_visible:
            held = ("lunchbox", False)
            draw_character(surf, self.kind, self.px, self.py, self.you_size, self.facing, self.walk_t,
                           self.moving, "school", held=held)
        # packed checklist
        ui.panel(surf, (14, 50, 238, 104), (255, 255, 255), 215, 14, border=(70, 160, 100))
        ui.text(surf, "Packed for school", 20, (50, 110, 70), (133, 70))
        for i, s in enumerate(("School bag", "Lunch box", "Water bottle")):
            ui.text(surf, "[x] " + s, 18, (60, 60, 90), (30, 96 + i * 21), "midleft")
        if self.board is None and self.px < 300:
            ui.text(surf, "Press  ->  or  D  to walk", 24, (255, 255, 255), (WIDTH // 2, 580), shadow=(0, 0, 0))

    # ---- world (ride + arrive)
    def draw_world(self, surf):
        cam = self.bus_x - ANCHOR
        surf.blit(self.sky, (0, 0))
        props.draw_sun(surf, 860, 100, self.t, 32)
        self.clouds.draw(surf)
        props.draw_hills(surf, cam, 330, (150, 205, 150), 0.15, 0)
        props.draw_hills(surf, cam, 380, (110, 185, 115), 0.35, 3)
        pygame.draw.rect(surf, (96, 190, 100), (0, 400, WIDTH, 52))
        for x, w, h, col in self.shops:
            sx = x - cam
            if -200 < sx < WIDTH + 50:
                props.draw_shop(surf, sx, 430, w, h, col)
        # school building
        props.draw_school(surf, SCHOOL_X - cam, 452, self.t)
        for i, (x, s, ph) in enumerate(self.trees):
            sx = x - cam
            if -80 < sx < WIDTH + 80 and not (SCHOOL_X - 230 < x < SCHOOL_X + 230):
                props.draw_tree(surf, sx, 452, s * 0.9, math.sin(self.t * 2 + ph) * 0.07)
        # road
        pygame.draw.rect(surf, (200, 200, 210), (0, 446, WIDTH, 8))
        pygame.draw.rect(surf, (70, 72, 80), (0, 454, WIDTH, 134))
        pygame.draw.rect(surf, (200, 200, 210), (0, 588, WIDTH, 12))
        self.draw_dashes(surf, cam)
        zx = 2250 - cam
        if -100 < zx < WIDTH:
            for i in range(8):
                pygame.draw.rect(surf, (245, 245, 245), (zx, 460 + i * 16, 80, 8))
            pygame.draw.rect(surf, (245, 245, 245), (STOP_FRONT + 6 - cam, 530, 6, 56))
        lx = LIGHT_X - cam
        if -100 < lx < WIDTH + 100:
            cd = None
            if self.lstate == "red" and self.red_started:
                cd = max(0, math.ceil(self.ltimer))
            props.draw_traffic_light(surf, lx, 452, self.light_shown, cd)
        # far lane traffic
        for c in self.cars:
            sx = c["x"] - cam
            if -120 < sx < WIDTH + 120:
                props.draw_car(surf, sx, FAR_LANE_Y, c["color"], c["wheel"], 0.8, -1)
        # bus
        seats = list(self.seats)
        props.draw_bus(surf, ANCHOR, BUS_Y, self.wheel, self.door_scale, seats, BUS_SIZE,
                       self.you_seat if seats[self.you_seat] else None)
        # walkers
        for w in self.walkers:
            if 0 < w["p"] < 1:
                x0, y0 = ANCHOR + DOOR_OFF, BUS_Y - 6
                x1, y1 = SCHOOL_X - cam, 462
                u = w["p"]
                draw_character(surf, w["kind"], lerp(x0, x1, u), lerp(y0, y1, u),
                               lerp(CH_SIZE, 0.72, u), 1, w["wt"], True, "school")
                if w["me"]:
                    ui.text(surf, "YOU", 18, (255, 255, 255),
                            (lerp(x0, x1, u), lerp(y0, y1, u) - 125 * lerp(CH_SIZE, 0.72, u) - 6), shadow=(0, 0, 0))
        self.draw_minimap(surf)
        if self.phase == "ride" and self.lstate == "red":
            msg = "RED LIGHT! The bus waits..." if not self.red_started else "RED LIGHT! The bus waits  %d" % max(0, math.ceil(self.ltimer))
            ui.text(surf, msg, 34, (255, 90, 90), (WIDTH // 2, 120), shadow=(0, 0, 0))
        elif self.phase == "ride" and self.lstate == "yellow":
            ui.text(surf, "Yellow light - slow down", 30, (255, 220, 60), (WIDTH // 2, 120), shadow=(0, 0, 0))

    def draw_dashes(self, surf, cam):
        """Lane dashes: Bresenham line, clipped to the screen with Cohen-Sutherland."""
        y = 521
        first = int(cam // 90) * 90
        for wx in range(first - 90, first + WIDTH + 180, 90):
            x0, x1 = wx - cam, wx - cam + 46
            clipped = cohen_sutherland(x0, y, x1, y, 0, 0, WIDTH - 1, HEIGHT - 1)
            if clipped:
                for px, py in bresenham(*clipped):
                    surf.fill((250, 250, 250), (px, py - 2, 1, 5))

    def draw_minimap(self, surf):
        ui.panel(surf, (700, 46, 246, 64), (20, 30, 50), 190, 12)
        ui.text(surf, "ROUTE MAP", 14, (200, 215, 240), (823, 58))
        window = (ROUTE_START, 0, SCHOOL_STOP, 1)
        viewport = (722, 86, 924, 86)
        pygame.draw.line(surf, (255, 255, 255), (722, 86), (924, 86), 4)
        lx, ly = window_to_viewport(LIGHT_X, 0.5, window, viewport)
        pygame.draw.circle(surf, (255, 60, 60), (int(lx), 86), 6)
        sx, sy = window_to_viewport(SCHOOL_STOP, 0.5, window, viewport)
        pygame.draw.polygon(surf, (60, 200, 100), [(sx, 70), (sx + 12, 75), (sx, 80)])
        pygame.draw.line(surf, (255, 255, 255), (sx, 68), (sx, 90), 2)
        bx, by = window_to_viewport(min(self.bus_x, SCHOOL_STOP), 0.5, window, viewport)
        pygame.draw.circle(surf, (255, 200, 0), (int(bx), 86), 8)
        pygame.draw.circle(surf, (35, 35, 50), (int(bx), 86), 8, 2)

    # ---- classroom
    def draw_class(self, surf):
        ct = self.ct
        surf.fill((255, 238, 196))
        pygame.draw.rect(surf, (200, 150, 100), (0, 420, WIDTH, 180))
        for x in range(-100, WIDTH + 200, 90):
            pygame.draw.line(surf, (170, 120, 75), (x, 420), (x - 70, 600), 3)
        pygame.draw.line(surf, (150, 105, 65), (0, 420), (WIDTH, 420), 4)
        # windows on the right wall
        for wx in (640, 800):
            rect(surf, (170, 225, 255), wx, 90, 110, 120)
            line(surf, (35, 35, 50), (wx + 55, 90), (wx + 55, 210), None, 3)
            line(surf, (35, 35, 50), (wx, 150), (wx + 110, 150), None, 3)
        props.draw_sun(surf, 700, 130, ct, 14)
        # chalkboard
        rect(surf, (140, 95, 55), 40, 90, 470, 250)
        rect(surf, (40, 100, 70), 54, 104, 442, 222)
        lines = [("Today: Reduce - Reuse - Recycle", (255, 255, 255)),
                 ("WET bin = GREEN: food waste", (140, 255, 160)),
                 ("DRY bin = BLUE: paper, wrappers", (150, 200, 255)),
                 ("RECYCLE bin = RED: bottles, cartons", (255, 160, 160))]
        for i, (s, col) in enumerate(lines):
            start = 1.2 + i * 1.9
            n = int((ct - start) * 18)
            if n > 0:
                ui.text(surf, s[:n], 20, col, (74, 140 + i * 40), "midleft")
        rect(surf, (230, 230, 230), 60, 330, 420, 8)
        # bell (rotation about its hook)
        amp = 0
        if self.rang:
            amp = 28 * max(0, 1 - self.bell_t / 2.6) * math.sin(self.bell_t * 22)
        bm = compose(translate(895, 60), rotate_about(amp, 0, 0))
        line(surf, (80, 80, 90), (895, 40), (895, 60), None, 3)
        poly(surf, (255, 200, 40), [(-20, 30), (20, 30), (15, 2), (8, -12), (-8, -12), (-15, 2)], bm)
        circle(surf, (120, 80, 20), 0, 34, 5, bm)
        # teacher
        pt = math.sin(ct * 3.2) * 7
        draw_character(surf, "teacher", 548, 548, 1.55, -1, ct, False, "casual",
                       arm_front=-88 + pt, held=("pointer", False))
        # students: back row then front row (desks drawn after to hide legs)
        o = self.others
        back = [(740, o[2]), (870, o[0])]
        front = [(660, self.kind), (790, o[1]), (915, o[2])]
        cheer = self.rang
        for x, k in back:
            draw_character(surf, k, x, 505, 1.15, -1, ct + x, False, "school",
                           arm_front=-150 if cheer else None, arm_back=-150 if cheer else None,
                           mood="cheer" if cheer else "smile")
            self.draw_desk(surf, x, 505, 1.15)
        for x, k in front:
            draw_character(surf, k, x, 548, 1.4, -1, ct + x, False, "school",
                           arm_front=-150 if cheer else None, arm_back=-150 if cheer else None,
                           mood="cheer" if cheer else "smile")
            self.draw_desk(surf, x, 548, 1.4)
        bob = math.sin(self.t * 5) * 4
        ui.text(surf, "YOU", 22, (255, 255, 255), (660, 548 - 175 + bob), shadow=(0, 0, 0))
        if self.rang and 0 < self.bell_t < 3:
            ui.panel(surf, (230, 230, 500, 70), (200, 60, 60), 230, 18, border=(255, 255, 255))
            ui.text(surf, "RING RING RING!  Break time!", 34, (255, 255, 255), (480, 265))

    def draw_desk(self, surf, x, base, s):
        top = base - 64 * s
        rect(surf, (200, 150, 90), x - 75 * s, top, 82 * s, 8 * s + 2)
        rect(surf, (180, 130, 80), x - 70 * s, top + 8 * s, 70 * s, base - top - 8 * s)
        rect(surf, (230, 90, 60), x - 55 * s, top - 7 * s, 22 * s, 7 * s)     # book


# ====================================================================== canteen
class CanteenLevel(BinLevel):
    level_id = "school"
    title = "School Canteen"
    source_name = "Canteen counter"
    menu_name = "canteen"
    menu_title = "Canteen Menu"
    goal = 4
    concepts = ["Canteen: dustbin lid ROTATES, wrapper moves along an arc (TRANSLATION) while it "
                "SCALES down and ROTATES", "Wrong bin shakes with a SHEAR transformation"]

    def __init__(self, game):
        super().__init__(game)
        self.bg = pygame.Surface((WIDTH, HEIGHT))
        self.paint_bg(self.bg)
        others = [k for k in KINDS if k != self.kind]
        self.npcs = [(430, others[0], 1), (555, others[1], -1)]

    def paint_bg(self, s):
        s.fill((255, 240, 205))
        pygame.draw.rect(s, (225, 195, 150), (0, 470, WIDTH, 130))
        for x in range(-200, WIDTH + 200, 100):
            pygame.draw.line(s, (205, 170, 125), (x, 470), (x - 120, 600), 3)
        pygame.draw.line(s, (170, 130, 90), (0, 470), (WIDTH, 470), 4)
        # windows
        for wx in (330, 470):
            rect(s, (170, 225, 255), wx, 110, 100, 100)
            line(s, (35, 35, 50), (wx + 50, 110), (wx + 50, 210), None, 3)
        # canteen sign
        rect(s, (230, 90, 60), 40, 70, 260, 56, None, (255, 255, 255), 4)
        ui.text(s, "SCHOOL CANTEEN", 30, (255, 255, 255), (170, 98), shadow=(0, 0, 0))
        # eco poster
        rect(s, (255, 255, 255), 600, 110, 150, 110, None, (60, 150, 90), 4)
        ui.text(s, "KEEP", 22, (60, 150, 90), (675, 138))
        ui.text(s, "SCHOOL", 22, (60, 150, 90), (675, 162))
        ui.text(s, "CLEAN!", 22, (60, 150, 90), (675, 186))
        # menu board on wall
        rect(s, (40, 40, 55), 60, 150, 220, 130, None, (150, 100, 60), 5)
        ui.text(s, "TODAY'S MENU", 18, (255, 235, 120), (170, 170))
        for i, t_ in enumerate(("Chips  Banana", "Juice  Apple", "Sandwich  Water")):
            ui.text(s, t_, 17, (255, 255, 255), (170, 200 + i * 24), bold=False)

    def draw_background(self, surf):
        surf.blit(self.bg, (0, 0))
        # vendor behind the counter
        draw_character(surf, "vendor", 130, 500, 1.3, 1, self.t, False, "casual")

    def draw_source(self, surf):
        # NPC kids sitting at a table (drawn before the table so their legs hide)
        for x, k, f in self.npcs:
            draw_character(surf, k, x, 505, 1.25, f, self.t + x, False, "school")
        rect(surf, (190, 130, 80), 390, 462, 210, 12)
        rect(surf, (160, 110, 70), 400, 474, 190, 40)
        # counter
        rect(surf, (150, 95, 60), 30, 455, 235, 95)
        rect(surf, (200, 140, 90), 20, 446, 255, 14)
        for i, k in enumerate(("chips", "juice", "apple", "banana")):
            draw_item(surf, k, 60 + i * 52, 425, 1.0)
        ui.text(surf, "CANTEEN", 22, (255, 235, 150), (148, 505))

    def source_item_pos(self):
        return (150, 430)
