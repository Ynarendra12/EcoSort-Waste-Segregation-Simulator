"""
BinLevel - the main game: eat a snack, then carry the waste to the right dustbin.
Canteen (school) and Park (picnic) both use this class; they only differ in the
background they draw.
"""
import math
import random
import pygame
import ui
from gfx import lerp, clamp, approach
from settings import WIDTH, HEIGHT, BIN_INFO, BIN_ORDER, POINTS_CORRECT, PENALTY_WRONG
from characters import draw_character, hand_pos, mouth_pos, NAMES
from items import ITEMS, ORDER, draw_item
import props

FLOOR_Y = 550          # where the player's feet are
BIN_BASE = 506         # dustbins stand a little further back
BIN_XS = {"wet": 660, "dry": 775, "recycle": 890}
COUNTER_ZONE = (170, 360)
CHAR_SIZE = 1.45


class BinLevel:
    level_id = "level"
    title = "Level"
    source_name = "Counter"
    goal = 4
    concepts = []

    def __init__(self, game):
        self.game = game
        self.kind = game.character
        self.t = 0.0
        self.px = 300.0
        self.facing = 1
        self.walk_t = 0.0
        self.moving = False
        self.score = 0
        self.correct = 0
        self.wrong = 0
        self.holding = None          # waste item key being carried
        self.menu_open = False
        self.eat = None              # dict(t, item) while eating
        self.drop = None             # dict(t, bin, item, start) while dropping
        self.done_timer = None
        self.toast = ui.Toast()
        self.particles = ui.Particles()
        self.bins = {k: dict(lid=0.0, lid_t=0.0, shake=0.0, shake_t=0.0) for k in BIN_ORDER}
        self.menu_cards = []
        self.prompt_rect = None
        self.prompt_action = None
        self.toast.show("Walk to the %s and pick something to eat!" % self.source_name.lower())

    # ---------------------------------------------------------- hooks
    def update_background(self, dt):
        pass

    def draw_background(self, surf):
        surf.fill((200, 230, 255))

    # ---------------------------------------------------------- helpers
    def near_source(self):
        return COUNTER_ZONE[0] <= self.px <= COUNTER_ZONE[1]

    def nearest_bin(self):
        best, bd = None, 70
        for k, x in BIN_XS.items():
            d = abs(self.px - x)
            if d < bd:
                best, bd = k, d
        return best

    def busy(self):
        return self.eat is not None or self.drop is not None or self.done_timer is not None

    # ---------------------------------------------------------- events
    def handle_event(self, e):
        g = self.game
        if self.menu_open:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.menu_open = False
                elif pygame.K_1 <= e.key <= pygame.K_6:
                    self.choose(ORDER[e.key - pygame.K_1])
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for key, r in self.menu_cards:
                    if r.collidepoint(e.pos):
                        self.choose(key)
                        return
            return
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
            self.interact()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.prompt_rect and self.prompt_rect.collidepoint(e.pos):
                self.interact()

    def interact(self):
        if self.busy():
            return
        if self.holding:
            b = self.nearest_bin()
            if b:
                self.pour(b)
            else:
                self.toast.show("Walk close to a dustbin first!", dur=2)
        elif self.near_source():
            self.menu_open = True
            self.game.sounds.play("click")

    def choose(self, key):
        self.menu_open = False
        self.game.sounds.play("click")
        self.eat = dict(t=0.0, item=key, bites=0)

    def pour(self, bin_kind):
        item = ITEMS[self.holding]
        if item["bin"] == bin_kind:
            hp = hand_pos(self.px, FLOOR_Y, CHAR_SIZE, self.facing)
            self.drop = dict(t=0.0, bin=bin_kind, item=self.holding, start=hp)
            self.bins[bin_kind]["lid_t"] = 75.0
            self.game.sounds.play("drop")
        else:
            self.wrong += 1
            self.score = max(0, self.score - PENALTY_WRONG)
            self.bins[bin_kind]["shake_t"] = 0.6
            right = BIN_INFO[item["bin"]]["label"]
            self.toast.show("Oops! %s goes into the %s bin. Try again!" % (item["waste"], right),
                            (255, 230, 230), (150, 40, 40), 3.5)
            self.game.sounds.play("bad")

    # ---------------------------------------------------------- update
    def update(self, dt):
        self.t += dt
        self.toast.update(dt)
        self.particles.update(dt)
        self.update_background(dt)
        for b in self.bins.values():
            b["lid"] = approach(b["lid"], b["lid_t"], 260 * dt)
            if b["shake_t"] > 0:
                b["shake_t"] -= dt
        if self.done_timer is not None:
            self.done_timer -= dt
            if self.done_timer <= 0:
                self.game.finish_level(self.level_id, dict(
                    score=self.score, correct=self.correct, wrong=self.wrong))
            return
        if self.menu_open:
            return
        if self.eat:
            self.update_eat(dt)
            return
        if self.drop:
            self.update_drop(dt)
            return
        d = self.game.input_dir()
        self.moving = d != 0
        if d:
            self.facing = d
            self.walk_t += dt * 11
            self.px = clamp(self.px + d * 230 * dt, 60, 905)
        else:
            self.walk_t += dt * 2

    def update_eat(self, dt):
        e = self.eat
        e["t"] += dt
        self.walk_t += dt * 2
        self.moving = False
        bites = int(max(0, e["t"] - 0.6) / 0.45)
        if bites > e["bites"] and bites <= 3:
            e["bites"] = bites
            self.game.sounds.play("crunch")
            mx, my = mouth_pos(self.px, FLOOR_Y, CHAR_SIZE, self.facing)
            self.particles.burst(mx, my, 6, [(255, 210, 120), (255, 255, 255)], 120, False)
        if e["t"] >= 2.4:
            self.holding = e["item"]
            self.eat = None
            w = ITEMS[self.holding]["waste"]
            self.toast.show("Yummy! Now throw the %s in the right dustbin." % w.lower(), dur=4)

    def update_drop(self, dt):
        d = self.drop
        d["t"] += dt / 0.9
        if d["t"] >= 1.0:
            item = ITEMS[d["item"]]
            self.correct += 1
            self.score += POINTS_CORRECT
            self.holding = None
            self.drop = None
            self.bins[d["bin"]]["lid_t"] = 0.0
            self.particles.burst(BIN_XS[d["bin"]], BIN_BASE - 100, 30)
            self.game.sounds.play("good")
            if self.correct >= self.goal:
                self.toast.show("Super! All waste sorted. You are an Eco Hero!", (255, 255, 160),
                                (30, 110, 60), 3)
                self.done_timer = 2.2
                self.game.sounds.play("win")
            else:
                self.toast.show("Great job! " + item["tip"], (230, 255, 230), (30, 110, 60), 3.5)

    # ---------------------------------------------------------- drawing
    def draw(self, surf):
        self.draw_background(surf)
        # dustbins + sign
        props.draw_bin_sign(surf, 775, 372, 340)
        near = self.nearest_bin() if self.holding else None
        for k in BIN_ORDER:
            b = self.bins[k]
            sh = math.sin(self.t * 50) * 0.12 * max(0, b["shake_t"] / 0.6) if b["shake_t"] > 0 else 0
            props.draw_bin(surf, BIN_XS[k], BIN_BASE, k, b["lid"], sh, 1.0, highlight=(near == k))
        self.draw_source(surf)
        # player
        held = None
        if self.holding and not self.drop:
            held = (self.holding, True)
        if self.eat:
            held = None
        draw_character(surf, self.kind, self.px, FLOOR_Y, CHAR_SIZE, self.facing, self.walk_t,
                       self.moving, "school" if self.uniform else "casual", held=held,
                       arm_front=(-70 if self.eat else None),
                       mood="cheer" if self.eat else "smile")
        self.draw_eating(surf)
        self.draw_dropping(surf)
        self.particles.draw(surf)
        self.draw_hud(surf)
        self.draw_prompt(surf)
        self.toast.draw(surf, 70)
        if self.menu_open:
            self.draw_menu(surf)

    uniform = True

    def draw_source(self, surf):
        pass

    def source_item_pos(self):
        return (200, 440)

    def draw_eating(self, surf):
        if not self.eat:
            return
        e = self.eat
        mx, my = mouth_pos(self.px, FLOOR_Y, CHAR_SIZE, self.facing)
        src = self.source_item_pos()
        t = e["t"]
        if t < 0.6:
            u = t / 0.6
            x = lerp(src[0], mx + 10 * self.facing, u)
            y = lerp(src[1], my + 20, u) - math.sin(u * math.pi) * 40
            size = lerp(1.0, 0.85, u)
        else:
            x, y = mx + 18 * self.facing, my + 22
            size = max(0.1, 0.85 - 0.22 * e["bites"])
        if e["bites"] < 4 and t < 2.4:
            draw_item(surf, e["item"], x, y, size, 0)
        if t > 0.6:
            ui.text(surf, "Crunch! Yum!", 22, (255, 255, 255), (self.px, FLOOR_Y - 215), shadow=(0, 0, 0))

    def draw_dropping(self, surf):
        d = self.drop
        if not d:
            return
        u = d["t"]
        tx, ty = BIN_XS[d["bin"]], BIN_BASE - 112
        sx, sy = d["start"]
        x = lerp(sx, tx, u)
        y = lerp(sy, ty, u) - math.sin(u * math.pi) * 90       # parabola-like arc
        size = lerp(1.0, 0.45, u)                               # scaling
        angle = u * 540                                         # rotation
        draw_item(surf, d["item"], x, y, size * 0.75, angle, waste=True)

    def draw_hud(self, surf):
        ui.panel(surf, (0, 0, WIDTH, 52), (20, 30, 50), 190, 0)
        ui.text(surf, self.title, 26, (255, 235, 120), (16, 26), "midleft")
        ui.text(surf, "Sorted: %d / %d" % (self.correct, self.goal), 26, (255, 255, 255), (480, 26))
        ui.text(surf, "Score: %d" % self.score, 26, (150, 255, 170), (WIDTH - 16, 26), "midright")
        if self.holding:
            tip = "Carrying: %s - walk to a dustbin" % ITEMS[self.holding]["waste"]
        elif self.eat:
            tip = "Eating..."
        else:
            tip = "Arrows / A D = walk     E / Enter / click the button = do the action"
        ui.panel(surf, (0, HEIGHT - 34, WIDTH, 34), (20, 30, 50), 170, 0)
        ui.text(surf, tip, 20, (255, 255, 255), (WIDTH // 2, HEIGHT - 17))

    def draw_prompt(self, surf):
        self.prompt_rect = None
        if self.busy() or self.menu_open:
            return
        label, color = None, (60, 130, 230)
        if self.holding:
            b = self.nearest_bin()
            if b:
                label = "Pour into %s bin  [E]" % BIN_INFO[b]["label"]
                color = BIN_INFO[b]["color"]
        elif self.near_source():
            label = "Open %s menu  [E]" % self.menu_name
        if label:
            r = pygame.Rect(0, 0, 330, 46)
            r.center = (int(clamp(self.px, 180, 780)), FLOOR_Y - 225)
            self.prompt_rect = r
            bob = int(math.sin(self.t * 6) * 3)
            r = r.move(0, bob)
            pygame.draw.rect(surf, (0, 0, 0), r.move(0, 4), border_radius=14)
            pygame.draw.rect(surf, color, r, border_radius=14)
            pygame.draw.rect(surf, (255, 255, 255), r, 3, border_radius=14)
            ui.text(surf, label, 22, (255, 255, 255), r.center, shadow=(0, 0, 0))

    menu_name = "snack"

    def draw_menu(self, surf):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        surf.blit(ov, (0, 0))
        panel = pygame.Rect(0, 0, 620, 400)
        panel.center = (WIDTH // 2, HEIGHT // 2 + 10)
        pygame.draw.rect(surf, (255, 248, 225), panel, border_radius=20)
        pygame.draw.rect(surf, (230, 150, 60), panel, 6, border_radius=20)
        ui.text(surf, self.menu_title, 34, (200, 90, 30), (panel.centerx, panel.top + 38))
        ui.text(surf, "Click one (or press 1-6). Esc = close", 18, (110, 80, 60), (panel.centerx, panel.top + 72))
        mouse = self.game.mouse()
        self.menu_cards = []
        for i, key in enumerate(ORDER):
            col, row = i % 3, i // 3
            r = pygame.Rect(panel.left + 30 + col * 192, panel.top + 100 + row * 142, 176, 128)
            hover = r.collidepoint(mouse)
            pygame.draw.rect(surf, (255, 255, 255) if not hover else (255, 235, 170), r, border_radius=14)
            pygame.draw.rect(surf, (230, 150, 60), r, 4 if hover else 2, border_radius=14)
            draw_item(surf, key, r.centerx, r.centery - 12, 1.6 if hover else 1.4)
            ui.text(surf, "%d. %s" % (i + 1, ITEMS[key]["label"]), 20, (70, 50, 40), (r.centerx, r.bottom - 16))
            self.menu_cards.append((key, r))
    menu_title = "Menu"
