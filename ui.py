"""Text, buttons, toasts and particle effects."""
import math
import random
import pygame
from transforms import compose, translate, rotate, transform_points
from algorithms import dda_line

_fonts = {}


def font(size, bold=True):
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont("comicsansms,trebuchetms,verdana,arial", size, bold=bold)
    return _fonts[key]


def text(surf, s, size, color, pos, anchor="center", shadow=None, bold=True):
    f = font(size, bold)
    img = f.render(s, True, color)
    r = img.get_rect(**{anchor: pos})
    if shadow:
        surf.blit(f.render(s, True, shadow), r.move(2, 2))
    surf.blit(img, r)
    return r


def wrap(s, size, max_w, bold=True):
    f = font(size, bold)
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if f.size(t)[0] <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def panel(surf, rect, color=(20, 30, 50), alpha=170, radius=14, border=None):
    r = pygame.Rect(rect)
    s = pygame.Surface(r.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=radius)
    if border:
        pygame.draw.rect(s, border, s.get_rect(), 3, border_radius=radius)
    surf.blit(s, r.topleft)


def lighten(c, k=40):
    return tuple(min(255, v + k) for v in c)


class Button:
    def __init__(self, rect, label, color=(56, 168, 90), size=28, text_color=(255, 255, 255)):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.size = size
        self.text_color = text_color

    def hover(self, mouse):
        return self.rect.collidepoint(mouse)

    def draw(self, surf, mouse, selected=False):
        r = self.rect.inflate(10, 6) if (self.hover(mouse) or selected) else self.rect
        col = lighten(self.color) if (self.hover(mouse) or selected) else self.color
        pygame.draw.rect(surf, (0, 0, 0), r.move(0, 4), border_radius=16)
        pygame.draw.rect(surf, col, r, border_radius=16)
        pygame.draw.rect(surf, (255, 255, 255), r, 3, border_radius=16)
        text(surf, self.label, self.size, self.text_color, r.center, shadow=(0, 0, 0))

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos))


class Toast:
    def __init__(self):
        self.msg = None
        self.t = 0
        self.color = (255, 255, 255)
        self.bg = (30, 40, 70)

    def show(self, msg, color=(255, 255, 255), bg=(30, 40, 70), dur=3.0):
        self.msg, self.color, self.bg, self.t = msg, color, bg, dur

    def update(self, dt):
        if self.t > 0:
            self.t -= dt

    def draw(self, surf, y=100):
        if self.t <= 0 or not self.msg:
            return
        lines = wrap(self.msg, 24, 700)
        h = 14 + 30 * len(lines)
        r = pygame.Rect(0, 0, 740, h)
        r.center = (480, y + h // 2)
        panel(surf, r, self.bg, 225, 16, border=(255, 255, 255))
        for i, ln in enumerate(lines):
            text(surf, ln, 24, self.color, (480, r.top + 22 + 30 * i))


def draw_sparkle(surf, x, y, r, color):
    """4-pointed star made of DDA lines."""
    for dx, dy, k in ((1, 0, r), (0, 1, r), (1, 1, r * 0.65), (1, -1, r * 0.65)):
        for px, py in dda_line(x - dx * k, y - dy * k, x + dx * k, y + dy * k):
            surf.fill(color, (px, py, 2, 2))


class Particles:
    COLORS = [(255, 90, 90), (255, 200, 40), (80, 200, 120), (80, 160, 255), (230, 120, 255)]

    def __init__(self):
        self.items = []

    def burst(self, x, y, n=26, colors=None, power=300, stars=True):
        colors = colors or self.COLORS
        for _ in range(n):
            a = random.uniform(0, 2 * math.pi)
            sp = random.uniform(0.3, 1.0) * power
            self.items.append(dict(
                x=x, y=y, vx=math.cos(a) * sp, vy=math.sin(a) * sp - 140,
                rot=random.uniform(0, 360), vr=random.uniform(-500, 500),
                life=random.uniform(0.8, 1.4), t=0, g=520,
                color=random.choice(colors), star=stars and random.random() < 0.35))

    def rain(self, n, width=960):
        for _ in range(n):
            self.items.append(dict(
                x=random.uniform(0, width), y=random.uniform(-40, -5),
                vx=random.uniform(-30, 30), vy=random.uniform(60, 170),
                rot=random.uniform(0, 360), vr=random.uniform(-300, 300),
                life=random.uniform(5, 8), t=0, g=0,
                color=random.choice(self.COLORS), star=False))

    def update(self, dt):
        for p in self.items:
            p["t"] += dt
            p["vy"] += p["g"] * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["rot"] += p["vr"] * dt
        self.items = [p for p in self.items if p["t"] < p["life"] and p["y"] < 640]

    def draw(self, surf):
        for p in self.items:
            if p["star"]:
                draw_sparkle(surf, int(p["x"]), int(p["y"]), 7, p["color"])
            else:
                m = compose(translate(p["x"], p["y"]), rotate(p["rot"]))
                pts = transform_points([(-5, -3), (5, -3), (5, 3), (-5, 3)], m)
                pygame.draw.polygon(surf, p["color"], pts)
