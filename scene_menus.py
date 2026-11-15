"""Title / character select, place select, level result and final Eco Score."""
import math
import pygame
import ui
import props
import gfx
from gfx import make_gradient
from scene_base import Scene
from settings import WIDTH, HEIGHT, BIN_INFO
from characters import KINDS, NAMES, MOTTO, draw_character
from transforms import compose, translate, rotate, scale, transform_points


def star_points(r, inner=0.45):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * inner
        a = math.radians(-90 + i * 36)
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return pts


def draw_star(surf, x, y, r, filled, t=0.0, pulse=False):
    k = 1 + (0.08 * math.sin(t * 5) if pulse else 0)
    m = compose(translate(x, y), rotate(math.sin(t * 3) * 8 if pulse else 0), scale(k, k))
    pts = transform_points(star_points(r), m)
    pygame.draw.polygon(surf, (255, 205, 40) if filled else (170, 170, 185), pts)
    pygame.draw.polygon(surf, (150, 100, 10) if filled else (110, 110, 125), pts, 3)


def stars_for(stats):
    total = stats["correct"] + stats["wrong"]
    acc = stats["correct"] / total if total else 0
    return 3 if acc >= 0.9 else 2 if acc >= 0.6 else 1


def sky_scene(surf, sky, clouds, t, ground=True):
    surf.blit(sky, (0, 0))
    props.draw_sun(surf, 840, 90, t, 34)
    clouds.draw(surf)
    if ground:
        props.draw_hills(surf, 0, 420, (130, 200, 130), 0.0, 1)
        pygame.draw.rect(surf, (96, 190, 100), (0, 470, WIDTH, HEIGHT - 470))


# ===================================================================== title
class TitleScene(Scene):
    concepts = [
        "Characters: polygons + circles, each limb has its own matrix (hierarchical modelling)",
        "Walking: rotation of arms/legs about shoulder and hip joints",
        "Selected card grows: scaling transformation",
        "Whiskers of the cat: Bresenham line algorithm",
        "Sun: midpoint circle algorithm + rotating rays",
    ]

    def __init__(self, game):
        super().__init__(game)
        self.t = 0
        self.sky = make_gradient(WIDTH, HEIGHT, (100, 180, 255), (210, 240, 255))
        self.clouds = props.Clouds()
        self.sel = KINDS.index(game.character) if game.character in KINDS else 1
        self.cards = [pygame.Rect(48 + i * 218, 215, 200, 250) for i in range(4)]
        self.start = ui.Button((360, 505, 240, 62), "START  >", (255, 140, 40), 32)

    def go_next(self):
        self.game.character = KINDS[self.sel]
        self.game.sounds.play("click")
        self.game.go("places")

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_a):
                self.sel = (self.sel - 1) % 4
                self.game.sounds.play("click")
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                self.sel = (self.sel + 1) % 4
                self.game.sounds.play("click")
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.go_next()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.cards):
                if r.collidepoint(e.pos):
                    self.sel = i
                    self.game.sounds.play("click")
            if self.start.clicked(e):
                self.go_next()

    def update(self, dt):
        self.t += dt
        self.clouds.update(dt)

    def draw(self, surf):
        sky_scene(surf, self.sky, self.clouds, self.t)
        # title with a gentle bounce
        bounce = math.sin(self.t * 2.5) * 4
        ui.text(surf, "EcoSort", 84, (255, 255, 255), (WIDTH // 2, 62 + bounce), shadow=(40, 120, 70))
        ui.text(surf, "Sort the waste.  Save the planet!", 28, (40, 100, 60), (WIDTH // 2, 126))
        ui.text(surf, "Choose your character", 30, (60, 60, 90), (WIDTH // 2, 178), shadow=(255, 255, 255))
        mouse = self.game.mouse()
        for i, r in enumerate(self.cards):
            sel = i == self.sel
            rr = r.inflate(12, 12) if sel else r
            ui.panel(surf, rr, (255, 255, 255), 215 if sel else 150, 22,
                     border=(255, 150, 40) if sel else None)
            k = KINDS[i]
            size = 1.6 + 0.05 * math.sin(self.t * 4) if sel else 1.25
            draw_character(surf, k, r.centerx, r.bottom - 62, size, 1, self.t * 9 if sel else self.t,
                           moving=sel, outfit="school")
            ui.text(surf, NAMES[k], 26, (50, 50, 80), (r.centerx, r.bottom - 26))
        ui.text(surf, MOTTO[KINDS[self.sel]], 22, (255, 255, 255), (WIDTH // 2, 480), shadow=(0, 0, 0))
        self.start.draw(surf, mouse)
        ui.text(surf, "Left / Right = choose    Enter = start    F1 = graphics concepts    Esc = quit",
                17, (30, 60, 40), (WIDTH // 2, 585))


# ==================================================================== places
class PlacesScene(Scene):
    concepts = [
        "Thumbnail scenes: polygons transformed with translate / scale",
        "Stars: polygon rotation + pulsing scale",
        "Character idle animation: small bob and arm swing",
    ]

    def __init__(self, game):
        super().__init__(game)
        self.t = 0
        self.sky = make_gradient(WIDTH, HEIGHT, (120, 195, 255), (215, 242, 255))
        self.clouds = props.Clouds()
        self.cards = {"school": pygame.Rect(60, 130, 400, 230), "park": pygame.Rect(500, 130, 400, 230)}
        self.locked = [(60 + i * 220, 390, 200, 70, n) for i, n in
                       enumerate(["Temple", "Market", "Restaurant", "Game Zone"])]
        self.back = ui.Button((40, 520, 170, 52), "< Back", (110, 120, 160), 24)
        self.finish = ui.Button((660, 515, 260, 60), "Finish: Eco Score", (255, 140, 40), 26)

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_1:
                self.game.go("school")
            elif e.key == pygame.K_2:
                self.game.go("park")
            elif e.key == pygame.K_ESCAPE:
                self.game.go("title")
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for name, r in self.cards.items():
                if r.collidepoint(e.pos):
                    self.game.sounds.play("click")
                    self.game.go(name)
            if self.back.clicked(e):
                self.game.go("title")
            if self.finish.clicked(e):
                self.game.sounds.play("click")
                self.game.go("end")

    def update(self, dt):
        self.t += dt
        self.clouds.update(dt)

    def thumb_school(self, surf, r):
        pygame.draw.rect(surf, (150, 215, 255), r)
        pygame.draw.rect(surf, (96, 190, 100), (r.left, r.bottom - 60, r.width, 60))
        props.draw_school(surf, r.centerx, r.bottom - 52, self.t)
        props.draw_bus(surf, r.left + 80, r.bottom - 8, self.t * 200, 1.0, ["boy", None, "cat", "girl"], 0.5)

    def thumb_park(self, surf, r):
        pygame.draw.rect(surf, (150, 215, 255), r)
        pygame.draw.rect(surf, (96, 190, 100), (r.left, r.bottom - 90, r.width, 90))
        pygame.draw.ellipse(surf, (90, 170, 235), (r.centerx - 90, r.bottom - 70, 180, 42))
        for i, x in enumerate((r.left + 50, r.right - 60, r.left + 130)):
            props.draw_tree(surf, x, r.bottom - 60, 0.9, math.sin(self.t * 2 + i) * 0.08)
        props.draw_sun(surf, r.right - 60, r.top + 50, self.t, 20)

    def draw(self, surf):
        sky_scene(surf, self.sky, self.clouds, self.t)
        ui.text(surf, "Where do you want to go today?", 42, (255, 255, 255), (WIDTH // 2, 60), shadow=(40, 100, 60))
        ui.text(surf, "Click a place to start (or press 1 / 2)", 22, (50, 70, 90), (WIDTH // 2, 100))
        mouse = self.game.mouse()
        for name, r in self.cards.items():
            hover = r.collidepoint(mouse)
            rr = r.inflate(14, 14) if hover else r
            pygame.draw.rect(surf, (255, 255, 255), rr.inflate(10, 10), border_radius=18)
            clip = surf.get_clip()
            surf.set_clip(rr)
            (self.thumb_school if name == "school" else self.thumb_park)(surf, rr)
            surf.set_clip(clip)
            pygame.draw.rect(surf, (255, 150, 40) if hover else (80, 90, 120), rr, 5, border_radius=4)
            label = "1. School Day" if name == "school" else "2. Park Picnic"
            ui.text(surf, label, 30, (255, 255, 255), (rr.centerx, rr.top + 28), shadow=(0, 0, 0))
            if name in self.game.results:
                n = stars_for(self.game.results[name])
                for i in range(3):
                    draw_star(surf, rr.right - 100 + i * 32, rr.bottom - 26, 13, i < n)
                ui.text(surf, "Done!", 22, (255, 255, 160), (rr.left + 50, rr.bottom - 26), shadow=(0, 0, 0))
        for x, y, w, h, n in self.locked:
            ui.panel(surf, (x, y, w, h), (60, 70, 100), 150, 14)
            ui.text(surf, n, 24, (230, 230, 240), (x + w // 2, y + 26))
            ui.text(surf, "Coming soon", 17, (200, 200, 220), (x + w // 2, y + 52), bold=False)
        draw_character(surf, self.game.character, 390, 575, 0.95, 1, self.t, False, "school")
        self.back.draw(surf, mouse)
        self.finish.draw(surf, mouse)
        ui.text(surf, "Score so far: %d" % self.game.total_score(), 24, (40, 80, 50), (300, 545), "midleft")


# ==================================================================== result
class ResultScene(Scene):
    concepts = ["Star shapes: polygon points computed with trigonometry, rotated and scaled by matrices",
                "Confetti: each piece is a rectangle rotated every frame (rotation matrix)"]

    def __init__(self, game, level="school"):
        super().__init__(game)
        self.level = level
        self.stats = game.results[level]
        self.n = stars_for(self.stats)
        self.t = 0
        self.sky = make_gradient(WIDTH, HEIGHT, (255, 225, 150), (255, 250, 220))
        self.particles = ui.Particles()
        self.btn = ui.Button((360, 500, 240, 62), "Continue  >", (56, 168, 90), 30)
        game.sounds.play("win")

    def go(self):
        self.game.go("places")

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.go()
        elif self.btn.clicked(e):
            self.go()

    def update(self, dt):
        self.t += dt
        if int(self.t * 3) != int((self.t - dt) * 3):
            self.particles.rain(3)
        self.particles.update(dt)

    def draw(self, surf):
        surf.blit(self.sky, (0, 0))
        self.particles.draw(surf)
        name = "School Day" if self.level == "school" else "Park Picnic"
        ui.text(surf, "Level Complete!", 62, (230, 100, 40), (WIDTH // 2, 70), shadow=(255, 255, 255))
        ui.text(surf, name, 32, (90, 90, 120), (WIDTH // 2, 126))
        for i in range(3):
            draw_star(surf, WIDTH // 2 - 90 + i * 90, 205, 38, i < self.n, self.t + i, pulse=i < self.n)
        s = self.stats
        total = s["correct"] + s["wrong"]
        acc = int(100 * s["correct"] / total) if total else 0
        ui.panel(surf, (270, 270, 420, 190), (255, 255, 255), 220, 20, border=(255, 170, 60))
        rows = [("Score", str(s["score"])), ("Correct drops", str(s["correct"])),
                ("Wrong tries", str(s["wrong"])), ("Accuracy", "%d%%" % acc)]
        for i, (a, b) in enumerate(rows):
            ui.text(surf, a, 28, (80, 80, 110), (300, 305 + i * 42), "midleft")
            ui.text(surf, b, 30, (40, 140, 70), (660, 305 + i * 42), "midright")
        draw_character(surf, self.game.character, 150, 520, 1.7, 1, self.t * 9, True, "school", mood="cheer",
                       arm_front=-150, arm_back=-150)
        draw_character(surf, self.game.character, 810, 520, 1.7, -1, self.t * 9, True, "school", mood="cheer",
                       arm_front=-150, arm_back=-150)
        self.btn.draw(surf, self.game.mouse())


# ======================================================================= end
class EndScene(Scene):
    concepts = ["Confetti rain: rotation matrices", "Trophy cup: polygons + circle",
                "Character cheering: arms rotated about the shoulders"]

    def __init__(self, game):
        super().__init__(game)
        self.t = 0
        self.sky = make_gradient(WIDTH, HEIGHT, (90, 160, 255), (220, 245, 255))
        self.clouds = props.Clouds()
        self.particles = ui.Particles()
        self.again = ui.Button((250, 510, 220, 56), "Play again", (56, 168, 90), 26)
        self.quit = ui.Button((500, 510, 220, 56), "Quit", (200, 80, 80), 26)
        res = game.results
        self.total = game.total_score()
        c = sum(r["correct"] for r in res.values())
        w = sum(r["wrong"] for r in res.values())
        self.acc = int(100 * c / (c + w)) if (c + w) else 0
        self.n = 0 if not res else (3 if self.acc >= 90 else 2 if self.acc >= 60 else 1)
        self.title = ["Keep trying!", "Eco Beginner", "Eco Star", "ECO HERO"][self.n]
        if self.n:
            game.sounds.play("win")
        self.particles.rain(60)

    def handle_event(self, e):
        if self.again.clicked(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN):
            self.game.reset()
            self.game.go("title")
        elif self.quit.clicked(e):
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self, dt):
        self.t += dt
        self.clouds.update(dt)
        if int(self.t * 4) != int((self.t - dt) * 4) and self.n:
            self.particles.rain(2)
        self.particles.update(dt)

    def draw(self, surf):
        sky_scene(surf, self.sky, self.clouds, self.t)
        self.particles.draw(surf)
        ui.text(surf, "Your Eco Score", 40, (255, 255, 255), (WIDTH // 2, 48), shadow=(30, 80, 50))
        ui.text(surf, str(self.total), 96, (255, 240, 120), (WIDTH // 2, 130), shadow=(150, 90, 10))
        ui.text(surf, self.title, 44, (255, 255, 255), (WIDTH // 2, 210), shadow=(200, 80, 30))
        for i in range(3):
            draw_star(surf, WIDTH // 2 - 70 + i * 70, 275, 28, i < self.n, self.t + i, pulse=i < self.n)
        ui.text(surf, "Accuracy %d%%" % self.acc, 26, (40, 80, 50), (WIDTH // 2, 330), shadow=(255, 255, 255))
        ui.panel(surf, (230, 360, 500, 130), (255, 255, 255), 215, 18, border=(60, 160, 90))
        ui.text(surf, "Remember", 24, (60, 130, 80), (WIDTH // 2, 382))
        for i, k in enumerate(("wet", "dry", "recycle")):
            info = BIN_INFO[k]
            y = 412 + i * 26
            pygame.draw.rect(surf, info["color"], (260, y - 10, 24, 20), border_radius=5)
            ui.text(surf, "%s bin: %s" % (info["label"].title(), info["desc"].lower()), 20,
                    (50, 50, 80), (296, y), "midleft")
        draw_character(surf, self.game.character, 130, 540, 1.9, 1, self.t * 9, True, "school",
                       arm_front=-150, arm_back=-150, mood="cheer")
        draw_character(surf, self.game.character, 830, 540, 1.9, -1, self.t * 9, True, "school",
                       arm_front=-150, arm_back=-150, mood="cheer")
        mouse = self.game.mouse()
        self.again.draw(surf, mouse)
        self.quit.draw(surf, mouse)
