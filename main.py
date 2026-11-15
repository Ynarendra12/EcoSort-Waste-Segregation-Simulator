"""
EcoSort - Interactive Waste Segregation Simulator
Computer Graphics Lab mini project (Python + Pygame, 2D).

Run:   python main.py
"""
import sys
import pygame
from settings import WIDTH, HEIGHT, FPS, TITLE
import ui
from sound import Sounds
from scene_menus import TitleScene, PlacesScene, ResultScene, EndScene
from scene_school import SchoolScene
from scene_park import ParkScene


class Game:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.sounds = Sounds()
        self.character = "boy"
        self.results = {}
        self.scene = None
        self.show_help = False
        self.fake_dir = None          # used only by automated tests
        self.fake_mouse = None
        self.running = True
        self.go("title")

    # --------------------------------------------------------- shared state
    def reset(self):
        self.results = {}

    def total_score(self):
        return sum(r["score"] for r in self.results.values())

    def finish_level(self, level, stats):
        self.results[level] = stats
        self.go("result", level=level)

    # --------------------------------------------------------------- input
    def input_dir(self):
        if self.fake_dir is not None:
            return self.fake_dir
        k = pygame.key.get_pressed()
        return int(k[pygame.K_RIGHT] or k[pygame.K_d]) - int(k[pygame.K_LEFT] or k[pygame.K_a])

    def mouse(self):
        return self.fake_mouse if self.fake_mouse is not None else pygame.mouse.get_pos()

    # -------------------------------------------------------------- scenes
    def go(self, name, **kw):
        classes = {"title": TitleScene, "places": PlacesScene, "school": SchoolScene,
                   "park": ParkScene, "result": ResultScene, "end": EndScene}
        self.scene = classes[name](self, **kw)
        self.scene.enter()

    # ---------------------------------------------------------------- loop
    def draw_help(self):
        lines = getattr(self.scene, "concepts", None) or []
        r = pygame.Rect(40, 70, 880, 70 + 30 * len(lines))
        ui.panel(self.screen, r, (10, 20, 40), 235, 16, border=(255, 220, 90))
        ui.text(self.screen, "Computer Graphics concepts in this screen (F1 to close)", 26,
                (255, 220, 90), (r.centerx, r.top + 30))
        for i, ln in enumerate(lines):
            ui.text(self.screen, "- " + ln, 20, (255, 255, 255), (r.left + 24, r.top + 68 + i * 30), "midleft", bold=False)

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F1:
                    self.show_help = not self.show_help
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and isinstance(self.scene, TitleScene):
                    self.running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and isinstance(self.scene, (SchoolScene, ParkScene)):
                    if not getattr(self.scene, "menu_blocking_escape", lambda: False)():
                        self.go("places")
                else:
                    self.scene.handle_event(e)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            if self.show_help:
                self.draw_help()
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
