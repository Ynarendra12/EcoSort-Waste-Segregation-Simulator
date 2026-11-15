"""Sound effects generated in code (no audio files needed).  If the computer has
no sound device the game simply runs silently."""
import math
import random
import struct
import pygame


class Sounds:
    def __init__(self):
        self.enabled = False
        self.sounds = {}
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            info = pygame.mixer.get_init()
            if info and info[1] == -16:
                self.rate, _, self.channels = info
                self.enabled = True
        except Exception:
            self.enabled = False
        if self.enabled:
            try:
                self._build()
            except Exception:
                self.enabled = False

    def _make(self, notes, dur, vol=0.35, wave="sine", decay=True):
        samples = []
        for f in notes:
            n = int(self.rate * dur)
            for i in range(n):
                env = (1 - i / n) if decay else 1.0
                if wave == "sine":
                    v = math.sin(2 * math.pi * f * i / self.rate)
                elif wave == "square":
                    v = 1.0 if math.sin(2 * math.pi * f * i / self.rate) >= 0 else -1.0
                else:
                    v = random.uniform(-1, 1)
                s = int(32767 * vol * env * v)
                samples.extend([s] * self.channels)
        data = struct.pack("<%dh" % len(samples), *samples)
        return pygame.mixer.Sound(buffer=data)

    def _build(self):
        self.sounds["click"] = self._make([900], 0.05)
        self.sounds["good"] = self._make([660, 880], 0.10)
        self.sounds["bad"] = self._make([150], 0.35, 0.25, "square")
        self.sounds["bell"] = self._make([1318, 1318, 1318, 1318, 1318, 1318], 0.14, 0.4)
        self.sounds["honk"] = self._make([300, 400], 0.15, 0.2, "square", False)
        self.sounds["drop"] = self._make([500, 420, 340, 260], 0.06)
        self.sounds["crunch"] = self._make([0], 0.07, 0.3, "noise")
        self.sounds["win"] = self._make([523, 659, 784, 1047], 0.13)

    def play(self, name):
        if self.enabled and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass
