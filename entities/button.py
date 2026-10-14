import pygame

class MobileButtons:
    def __init__(self):
        self.left = pygame.Rect(20, 520, 80, 60)
        self.right = pygame.Rect(120, 520, 80, 60)
        self.fire = pygame.Rect(680, 520, 100, 60)

    def draw(self, screen):
        # Sleek glassmorphic controls with neon cyber styling
        btn_font = pygame.font.SysFont("bahnschrift", 16, bold=True)
        for rect, symbol, label, color in [
            (self.left, "<", "LEFT", (101, 244, 255)),
            (self.right, ">", "RIGHT", (101, 244, 255)),
            (self.fire, "^", "FIRE", (255, 76, 147)),
        ]:
            surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            surf.fill((20, 24, 39, 140))
            screen.blit(surf, rect.topleft)
            pygame.draw.rect(screen, (*color, 180), rect, 2, border_radius=8)

            txt = btn_font.render(label, True, color)
            screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

    def handle_mouse(self, player, events):
        mouse_pressed = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        if mouse_pressed[0]:
            if self.left.collidepoint(mouse_pos):
                player.move_left()
            if self.right.collidepoint(mouse_pos):
                player.move_right()
            if self.fire.collidepoint(mouse_pos):
                return True

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.fire.collidepoint(event.pos):
                    return True
        return False
