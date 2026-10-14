import pygame
import os

class AudioManager:
    """
    Central audio manager for Space Invaders 2.0.
    Handles retro arcade sound effects and volume controls with safe fallbacks.
    """
    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager
        self.sounds = {}
        self.is_initialized = False
        self.last_played = {}
        self.volume = 1.0

        if settings_manager:
            vol_val = settings_manager.get("volume", 100)
            self.volume = max(0.0, min(1.0, vol_val / 100.0))

        self._init_mixer()
        self._load_sounds()

    def _init_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.is_initialized = True
        except Exception as e:
            print(f"[AudioManager] Audio init failed (running in silent mode): {e}")
            self.is_initialized = False

    def _load_sounds(self):
        if not self.is_initialized:
            return

        sound_files = {
            "shoot": "assets/sounds/shoot.wav",
            "enemy_shoot": "assets/sounds/enemy_shoot.wav",
            "explosion": "assets/sounds/explosion.wav",
            "hit": "assets/sounds/hit.wav",
            "game_over": "assets/sounds/game_over.wav",
            "ui_click": "assets/sounds/ui_click.wav",
            "game_start": "assets/sounds/game_start.wav",
        }

        for name, path in sound_files.items():
            if os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                    snd.set_volume(self.volume)
                    self.sounds[name] = snd
                except Exception as e:
                    print(f"[AudioManager] Could not load sound {path}: {e}")

    def set_volume(self, volume_percent):
        """Set master volume from 0 to 100."""
        self.volume = max(0.0, min(1.0, volume_percent / 100.0))
        for snd in self.sounds.values():
            snd.set_volume(self.volume)
        if self.settings_manager:
            self.settings_manager.set("volume", int(self.volume * 100))

    def get_volume(self):
        """Return volume percentage (0 - 100)."""
        return int(self.volume * 100)

    def _play(self, name, min_interval_ms=50):
        if not self.is_initialized or self.volume <= 0.001:
            return

        snd = self.sounds.get(name)
        if not snd:
            return

        now = pygame.time.get_ticks()
        last = self.last_played.get(name, 0)
        if now - last < min_interval_ms:
            return

        try:
            snd.play()
            self.last_played[name] = now
        except Exception:
            pass

    def play_shoot(self):
        self._play("shoot", min_interval_ms=100)

    def play_enemy_shoot(self):
        self._play("enemy_shoot", min_interval_ms=120)

    def play_explosion(self):
        self._play("explosion", min_interval_ms=80)

    def play_hit(self):
        self._play("hit", min_interval_ms=150)

    def play_game_over(self):
        self._play("game_over", min_interval_ms=500)

    def play_ui_click(self):
        self._play("ui_click", min_interval_ms=60)

    def play_game_start(self):
        self._play("game_start", min_interval_ms=400)
