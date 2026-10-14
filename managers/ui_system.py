import pygame
import math
import random

# ==============================================================================
# "SPACE INVADERS ARCADE" COLOR PALETTE & DESIGN SYSTEM
# ==============================================================================
DARK_BG       = (5, 7, 15)          # Deep Arcade CRT Black-Navy
PANEL_BG      = (14, 18, 32)        # Tactical Cabinet Dark Fill
PANEL_BG_SUB  = (20, 26, 46)        # Secondary Card Fill
PANEL_BORDER  = (42, 58, 95)        # Crisp Slate-Blue Border
PANEL_HOVER   = (28, 38, 68)        # Interactive Hover Fill

NEON_GREEN    = (57, 255, 20)       # Classic Space Invaders Phosphor Green
CYAN          = (0, 243, 255)       # Primary Arcade Neon Cyan
CYAN_DIM      = (30, 125, 145)
VIOLET        = (175, 120, 255)     # Electric Arcade Purple
VIOLET_DIM    = (85, 55, 140)
MAGENTA       = (255, 55, 145)      # UFO / Laser Neon Pink
DANGER_RED    = (255, 60, 80)       # Red Alert / Hull Warning

WHITE         = (245, 248, 255)     # Crisp Arcade White
TEXT_MUTED    = (155, 170, 205)     # Secondary HUD Label
TEXT_DIM      = (90, 105, 140)      # Subtle Terminal Hint

GOLD          = (255, 215, 60)      # 1st Place High Score Gold
SILVER        = (220, 230, 242)     # 2nd Place Silver
BRONZE        = (230, 155, 95)      # 3rd Place Bronze


# ==============================================================================
# PROCEDURAL PIXEL-ART SPACE INVADERS (2-FRAME ANIMATED MATRICES)
# ==============================================================================
INVADER_MATRICES = {
    "crab": [
        [
            "  #     #  ",
            "   #   #   ",
            "  #######  ",
            " ## ### ## ",
            "###########",
            "# ####### #",
            "# #     # #",
            "   ## ##   ",
        ],
        [
            "  #     #  ",
            "#  #   #  #",
            "# ####### #",
            "### ### ###",
            "###########",
            "  #######  ",
            "  #     #  ",
            " #       # ",
        ],
    ],
    "squid": [
        [
            "   ##   ",
            "  ####  ",
            " ###### ",
            "## ## ##",
            "########",
            "  #  #  ",
            " # ## # ",
            "# #  # #",
        ],
        [
            "   ##   ",
            "  ####  ",
            " ###### ",
            "## ## ##",
            "########",
            " # ## # ",
            "#      #",
            " #    # ",
        ],
    ],
    "octopus": [
        [
            "    ####    ",
            " ########## ",
            "############",
            "###  ##  ###",
            "############",
            "   ##  ##   ",
            "  ## ## ##  ",
            "##        ##",
        ],
        [
            "    ####    ",
            " ########## ",
            "############",
            "###  ##  ###",
            "############",
            "  ###  ###  ",
            " ##  ##  ## ",
            "  ##    ##  ",
        ],
    ],
    "ufo": [
        [
            "    ######    ",
            "  ##########  ",
            " #### ## #### ",
            "##############",
            "  ### ## ###  ",
            "   #      #   ",
        ],
        [
            "    ######    ",
            "  ##########  ",
            " ## #### #### ",
            "##############",
            "  ### ## ###  ",
            "   #      #   ",
        ],
    ],
}

_SPRITE_CACHE = {}

def draw_invader_sprite(screen, x, y, kind="crab", scale=3, color=NEON_GREEN, frame=0, center=True, glow=True):
    """Draw an authentic pixel-art Space Invader sprite with optional neon glow."""
    frames = INVADER_MATRICES.get(kind, INVADER_MATRICES["crab"])
    matrix = frames[frame % len(frames)]
    key = (kind, scale, color, frame % len(frames), glow)

    if key not in _SPRITE_CACHE:
        rows = len(matrix)
        cols = len(matrix[0])
        w, h = cols * scale, rows * scale
        pad = 6 if glow else 0
        surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)

        if glow:
            glow_col = (*color[:3], 45)
            for r_idx, row in enumerate(matrix):
                for c_idx, ch in enumerate(row):
                    if ch == "#":
                        pygame.draw.rect(
                            surf,
                            glow_col,
                            (pad + c_idx * scale - 2, pad + r_idx * scale - 2, scale + 4, scale + 4),
                        )

        for r_idx, row in enumerate(matrix):
            for c_idx, ch in enumerate(row):
                if ch == "#":
                    pygame.draw.rect(
                        surf,
                        color,
                        (pad + c_idx * scale, pad + r_idx * scale, scale, scale),
                    )
        _SPRITE_CACHE[key] = surf

    surf = _SPRITE_CACHE[key]
    draw_x = x - surf.get_width() // 2 if center else x
    draw_y = y - surf.get_height() // 2 if center else y
    screen.blit(surf, (draw_x, draw_y))
    return surf.get_rect(topleft=(draw_x, draw_y))


def get_fonts():
    """Load crisp arcade/monospace-prioritized fonts with safe fallbacks."""
    if not pygame.font.get_init():
        pygame.font.init()

    title_font  = pygame.font.SysFont("consolas", 36, bold=True)
    hero_font   = pygame.font.SysFont("consolas", 46, bold=True)
    header_font = pygame.font.SysFont("consolas", 22, bold=True)
    body_font   = pygame.font.SysFont("consolas", 16, bold=True)
    sub_font    = pygame.font.SysFont("segoeui", 13, bold=True)
    mono_font   = pygame.font.SysFont("consolas", 18, bold=True)
    mono_large  = pygame.font.SysFont("consolas", 32, bold=True)
    brand_font  = pygame.font.SysFont("consolas", 17, bold=True)
    tiny_font   = pygame.font.SysFont("consolas", 12, bold=True)

    return {
        "title": title_font,
        "hero": hero_font,
        "header": header_font,
        "body": body_font,
        "sub": sub_font,
        "mono": mono_font,
        "mono_large": mono_large,
        "brand": brand_font,
        "tiny": tiny_font,
    }


# ==============================================================================
# COSMIC BACKGROUND, RETRO HORIZON GRID & CRT SCANLINE OVERLAY
# ==============================================================================
def create_starfield(screen_width, screen_height, count=95):
    """Generate multi-layered arcade starfield with parallax speeds."""
    stars = []
    palette = [
        (100, 240, 255),
        (57, 255, 20),
        (255, 110, 185),
        (180, 150, 255),
        (255, 255, 255),
    ]
    for _ in range(count):
        x = random.randint(0, screen_width)
        y = random.randint(0, screen_height)
        layer = random.choice([1, 1, 2, 2, 3])
        base_col = random.choice(palette)
        if layer == 1:
            speed = random.uniform(0.15, 0.35)
            radius = 1
            tint = tuple(max(70, int(c * 0.55)) for c in base_col)
        elif layer == 2:
            speed = random.uniform(0.4, 0.75)
            radius = random.choice([1, 2])
            tint = tuple(max(120, int(c * 0.8)) for c in base_col)
        else:
            speed = random.uniform(0.85, 1.4)
            radius = 2
            tint = base_col
        stars.append({
            "x": x,
            "y": y,
            "speed": speed,
            "radius": radius,
            "tint": tint,
            "twinkle": random.uniform(0, 10),
        })
    return stars


_CACHED_NEBULA_SURF = None
_CACHED_CRT_SURF = None


def get_nebula_surface(screen_w, screen_h):
    global _CACHED_NEBULA_SURF
    if _CACHED_NEBULA_SURF is not None and _CACHED_NEBULA_SURF.get_size() == (screen_w, screen_h):
        return _CACHED_NEBULA_SURF

    try:
        from PIL import Image, ImageDraw, ImageFilter
        sw, sh = screen_w // 2, screen_h // 2
        img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        draw.ellipse([int(sw * 0.05), int(sh * 0.10), int(sw * 0.45), int(sh * 0.55)], fill=(90, 30, 160, 42))
        draw.ellipse([int(sw * 0.50), int(sh * 0.15), int(sw * 0.95), int(sh * 0.65)], fill=(10, 90, 155, 38))
        draw.ellipse([int(sw * 0.25), int(sh * 0.55), int(sw * 0.75), int(sh * 0.95)], fill=(20, 115, 75, 28))

        blurred = img.filter(ImageFilter.GaussianBlur(radius=28))
        upscaled = blurred.resize((screen_w, screen_h), Image.Resampling.BILINEAR)
        surf = pygame.image.fromstring(upscaled.tobytes(), (screen_w, screen_h), "RGBA")
    except Exception:
        surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)

    _CACHED_NEBULA_SURF = surf
    return _CACHED_NEBULA_SURF


def get_crt_surface(screen_w, screen_h):
    """Build a cached CRT scanline & subtle arcade cabinet frame overlay."""
    global _CACHED_CRT_SURF
    if _CACHED_CRT_SURF is not None and _CACHED_CRT_SURF.get_size() == (screen_w, screen_h):
        return _CACHED_CRT_SURF

    surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
    # Subtle horizontal CRT scanlines every 3px
    for y in range(0, screen_h, 3):
        pygame.draw.line(surf, (0, 0, 0, 38), (0, y), (screen_w, y), 1)

    # Outer arcade screen bezel glow
    pygame.draw.rect(surf, (0, 243, 255, 22), (0, 0, screen_w, screen_h), 2)
    _CACHED_CRT_SURF = surf
    return _CACHED_CRT_SURF


def draw_crt_overlay(screen):
    """Apply the cached CRT scanline effect on top of the current frame."""
    w, h = screen.get_size()
    screen.blit(get_crt_surface(w, h), (0, 0))


def draw_cosmic_background(screen, stars, tick=0, show_grid=True):
    """Render deep arcade space background with stars, synth grid, and scanlines."""
    screen_w, screen_h = screen.get_size()
    screen.fill(DARK_BG)

    # Ambient nebula glow
    nebula_surf = get_nebula_surface(screen_w, screen_h)
    screen.blit(nebula_surf, (0, 0))

    # Subtle background tactical grid
    if show_grid:
        grid_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        horizon_y = screen_h - 115
        pygame.draw.line(grid_surf, (0, 243, 255, 22), (0, horizon_y), (screen_w, horizon_y), 1)

        # Scrolling horizontal perspective lines at bottom
        offset = (tick * 0.4) % 18
        for i in range(6):
            gy = int(horizon_y + ((i * 18 + offset) ** 1.15) * 0.65)
            if gy < screen_h:
                alpha = max(8, min(40, int(10 + i * 5)))
                pygame.draw.line(grid_surf, (0, 243, 255, alpha), (0, gy), (screen_w, gy), 1)

        # Perspective radial lines from vanishing point
        vx, vy = screen_w // 2, horizon_y - 40
        for gx in range(-200, screen_w + 201, 100):
            pygame.draw.line(grid_surf, (175, 120, 255, 18), (vx, vy), (gx, screen_h), 1)

        screen.blit(grid_surf, (0, 0))

    # Drifting square pixel stars (authentic arcade style)
    for s in stars:
        s["y"] = (s["y"] + s["speed"]) % screen_h
        twinkle_factor = 0.75 + 0.25 * math.sin(tick * 0.06 + s["twinkle"])
        r, g, b = s["tint"]
        col = (
            max(0, min(255, int(r * twinkle_factor))),
            max(0, min(255, int(g * twinkle_factor))),
            max(0, min(255, int(b * twinkle_factor))),
        )
        sz = s["radius"] * 2
        pygame.draw.rect(screen, col, (int(s["x"]), int(s["y"]), sz, sz))


# ==============================================================================
# UI DRAWING HELPERS (ARCADE PANELS, NEON TEXT, HEARTS)
# ==============================================================================
def draw_panel(screen, rect, fill=PANEL_BG, border=PANEL_BORDER, radius=8, top_accent=None, glow_color=None):
    """Draw a tactical arcade HUD panel with glowing corner brackets and laser accents."""
    rect = pygame.Rect(rect)

    # Outer neon bloom
    if glow_color:
        glow_surf = pygame.Surface((rect.width + 12, rect.height + 12), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*glow_color[:3], 32), glow_surf.get_rect(), border_radius=radius + 4)
        screen.blit(glow_surf, (rect.x - 6, rect.y - 6))

    # Drop shadow
    shadow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 110), shadow_surf.get_rect(), border_radius=radius)
    screen.blit(shadow_surf, (rect.x + 3, rect.y + 4))

    # Main panel fill & border
    pygame.draw.rect(screen, fill, rect, border_radius=radius)
    if border:
        pygame.draw.rect(screen, border, rect, 1, border_radius=radius)

    # Tactical corner L-brackets when panel is large enough
    bracket_col = top_accent if top_accent else (border if border else CYAN_DIM)
    if bracket_col and rect.width >= 60 and rect.height >= 34:
        blen = min(10, rect.width // 6, rect.height // 3)
        x1, y1, x2, y2 = rect.left, rect.top, rect.right - 1, rect.bottom - 1
        # Top-Left
        pygame.draw.line(screen, bracket_col, (x1, y1), (x1 + blen, y1), 2)
        pygame.draw.line(screen, bracket_col, (x1, y1), (x1, y1 + blen), 2)
        # Top-Right
        pygame.draw.line(screen, bracket_col, (x2 - blen, y1), (x2, y1), 2)
        pygame.draw.line(screen, bracket_col, (x2, y1), (x2, y1 + blen), 2)
        # Bottom-Left
        pygame.draw.line(screen, bracket_col, (x1, y2), (x1 + blen, y2), 2)
        pygame.draw.line(screen, bracket_col, (x1, y2 - blen), (x1, y2), 2)
        # Bottom-Right
        pygame.draw.line(screen, bracket_col, (x2 - blen, y2), (x2, y2), 2)
        pygame.draw.line(screen, bracket_col, (x2, y2 - blen), (x2, y2), 2)

    # Top laser accent bar
    if top_accent:
        accent_rect = pygame.Rect(rect.x + 16, rect.y + 2, max(10, rect.width - 32), 2)
        pygame.draw.rect(screen, top_accent, accent_rect, border_radius=1)


def draw_glow_text(screen, font, text, cx, cy, color=CYAN, glow_alpha=55, center=True):
    """Render arcade neon text with a dark 3D drop-shadow and soft outer halo."""
    glow = font.render(text, True, color)
    gw, gh = glow.get_size()
    gx = cx - gw // 2 if center else cx
    gy = cy - gh // 2 if center else cy

    # Crisp retro arcade drop-shadow
    shadow = font.render(text, True, (5, 8, 18))
    screen.blit(shadow, (gx + 2, gy + 2))

    # Multi-pass neon glow
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        s = pygame.Surface((gw, gh), pygame.SRCALPHA)
        s.blit(glow, (0, 0))
        s.set_alpha(glow_alpha)
        screen.blit(s, (gx + dx, gy + dy))

    main_surf = font.render(text, True, color)
    screen.blit(main_surf, (gx, gy))
    return main_surf.get_rect(topleft=(gx, gy))


def draw_heart(screen, x, y, size=13, is_active=True, pulse=1.0):
    """Draw a pixel-art style neon arcade heart icon for Hull Integrity."""
    heart_matrix = [
        " ##   ## ",
        "#### ####",
        "#########",
        "#########",
        " ####### ",
        "  #####  ",
        "   ###   ",
        "    #    ",
    ]
    scale = max(2, int((size * pulse) / 4.5))
    color = (255, 55, 110) if is_active else (45, 52, 78)

    if is_active:
        glow_surf = pygame.Surface((9 * scale + 6, 8 * scale + 6), pygame.SRCALPHA)
        for r_idx, row in enumerate(heart_matrix):
            for c_idx, ch in enumerate(row):
                if ch == "#":
                    pygame.draw.rect(
                        glow_surf,
                        (255, 55, 110, 45),
                        (c_idx * scale + 1, r_idx * scale + 1, scale + 3, scale + 3),
                    )
        screen.blit(glow_surf, (x - 2, y - 1))

    for r_idx, row in enumerate(heart_matrix):
        for c_idx, ch in enumerate(row):
            if ch == "#":
                pygame.draw.rect(
                    screen,
                    color,
                    (x + c_idx * scale, y + r_idx * scale, scale, scale),
                )


# ==============================================================================
# INTERACTIVE ARCADE UI BUTTON
# ==============================================================================
class UIButton:
    def __init__(self, rect, text, style="secondary", icon=None, audio_manager=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.style = style  # "primary", "secondary", "danger", "gold", "tab"
        self.icon = icon
        self.audio = audio_manager
        self.is_hovered = False
        self.is_active = False
        self.was_hovered = False

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        if self.is_hovered and not self.was_hovered and self.audio:
            self.audio.play_ui_click()
        self.was_hovered = self.is_hovered

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.audio:
                    self.audio.play_ui_click()
                return True
        return False

    def draw(self, screen, font):
        r = self.rect
        hover = self.is_hovered

        if self.style == "primary":
            fill = (18, 68, 52) if hover else (12, 42, 36)
            border = NEON_GREEN if hover else CYAN
            text_color = NEON_GREEN if hover else WHITE
            glow_col = NEON_GREEN if hover else CYAN_DIM
            radius = 8
        elif self.style == "danger":
            fill = (85, 22, 35) if hover else (48, 15, 24)
            border = DANGER_RED
            text_color = WHITE
            glow_col = DANGER_RED if hover else None
            radius = 8
        elif self.style == "gold":
            fill = (70, 54, 16) if hover else (42, 32, 10)
            border = GOLD
            text_color = GOLD if hover else WHITE
            glow_col = GOLD if hover else None
            radius = 8
        elif self.style == "tab":
            fill = (28, 42, 72) if (hover or self.is_active) else (16, 20, 34)
            border = CYAN if self.is_active else (PANEL_BORDER if not hover else VIOLET)
            text_color = CYAN if self.is_active else (WHITE if hover else TEXT_MUTED)
            glow_col = CYAN if self.is_active else None
            radius = 6
        else:  # secondary
            fill = PANEL_HOVER if hover else PANEL_BG_SUB
            border = CYAN if hover else PANEL_BORDER
            text_color = CYAN if hover else TEXT_MUTED
            glow_col = CYAN if hover else None
            radius = 8

        draw_panel(
            screen,
            r,
            fill=fill,
            border=border,
            radius=radius,
            top_accent=border if (hover or self.is_active) else None,
            glow_color=glow_col,
        )

        # Add arcade selection chevrons on hover for primary/secondary buttons
        label = self.text
        if hover and self.style in ("primary", "secondary") and r.width >= 150:
            label = f"> {self.text} <"

        txt_surf = font.render(label, True, text_color)
        screen.blit(
            txt_surf,
            (r.centerx - txt_surf.get_width() // 2, r.centery - txt_surf.get_height() // 2),
        )

        # Active bottom indicator bar for tabs
        if self.style == "tab" and self.is_active:
            bar = pygame.Rect(r.x + 8, r.bottom - 3, r.width - 16, 2)
            pygame.draw.rect(screen, NEON_GREEN, bar, border_radius=1)


# ==============================================================================
# INTERACTIVE ARCADE TERMINAL TEXT INPUT FIELD
# ==============================================================================
class UITextInput:
    def __init__(self, rect, placeholder="Enter text...", masked=False, max_len=50, label=None):
        self.rect = pygame.Rect(rect)
        self.text = ""
        self.placeholder = placeholder
        self.masked = masked
        self.max_len = max_len
        self.label = label
        self.is_focused = False
        self.select_all = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.is_focused = self.rect.collidepoint(event.pos)
            self.select_all = False

        elif event.type == pygame.KEYDOWN and self.is_focused:
            ctrl = pygame.key.get_mods() & pygame.KMOD_CTRL
            if event.key == pygame.K_BACKSPACE:
                if ctrl or self.select_all:
                    self.text = ""
                    self.select_all = False
                else:
                    self.text = self.text[:-1]
            elif event.key == pygame.K_a and ctrl:
                self.select_all = True
            elif event.key == pygame.K_v and ctrl:
                try:
                    clip = pygame.scrap.get(pygame.SCRAP_TEXT)
                    if clip:
                        clip_str = clip.decode("utf-8", errors="ignore").replace("\x00", "").split("\n")[0]
                        self.text = (self.text + clip_str)[:self.max_len]
                except Exception:
                    pass
            elif (
                event.unicode
                and event.unicode.isprintable()
                and event.key != pygame.K_TAB
                and event.key != pygame.K_RETURN
            ):
                if self.select_all:
                    self.text = event.unicode
                    self.select_all = False
                elif len(self.text) < self.max_len:
                    self.text += event.unicode

    def draw(self, screen, font, label_font=None):
        r = self.rect

        # Terminal field label
        if self.label and label_font:
            lbl_color = NEON_GREEN if self.is_focused else TEXT_MUTED
            lbl = label_font.render(f"// {self.label}", True, lbl_color)
            screen.blit(lbl, (r.x + 2, r.y - lbl.get_height() - 4))

        fill = (18, 26, 44) if self.is_focused else (10, 14, 24)
        border = NEON_GREEN if self.is_focused else PANEL_BORDER
        glow = NEON_GREEN if self.is_focused else None
        draw_panel(screen, r, fill=fill, border=border, radius=8, glow_color=glow)

        # Terminal prompt prefix
        prompt_col = NEON_GREEN if self.is_focused else CYAN_DIM
        prompt_surf = font.render(">", True, prompt_col)
        screen.blit(prompt_surf, (r.x + 12, r.centery - prompt_surf.get_height() // 2))

        # Text content or placeholder
        display_str = ("*" * len(self.text)) if self.masked else self.text
        if display_str:
            txt_color = WHITE if not self.select_all else NEON_GREEN
            txt_surf = font.render(display_str, True, txt_color)
        else:
            txt_surf = font.render(self.placeholder, True, TEXT_DIM)

        text_x = r.x + 30
        screen.blit(txt_surf, (text_x, r.centery - txt_surf.get_height() // 2))

        # Arcade block cursor
        if self.is_focused and (pygame.time.get_ticks() // 400) % 2 == 0 and not self.select_all:
            cx_pos = text_x + (txt_surf.get_width() if display_str else 0) + 3
            cursor_rect = pygame.Rect(cx_pos, r.centery - 9, 8, 18)
            pygame.draw.rect(screen, NEON_GREEN, cursor_rect)