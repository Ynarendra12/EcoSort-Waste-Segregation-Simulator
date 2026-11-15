"""Base class every scene inherits from."""


class Scene:
    concepts = []          # lines shown in the F1 'Graphics concepts' panel

    def __init__(self, game):
        self.game = game

    def enter(self):
        pass

    def handle_event(self, e):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass
