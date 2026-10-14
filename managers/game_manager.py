import pygame
import random
import math
import os
from entities.player import Player, SHIP_COLOR_MAP
from entities.button import MobileButtons
from entities.enemy import Enemy
from entities.bullet import Bullet
from managers.db_manager import DBManager
from managers.settings_manager import SettingsManager
from managers.audio_manager import AudioManager
from managers.ui_system import (
    DARK_BG, PANEL_BG, PANEL_BG_SUB, PANEL_BORDER, PANEL_HOVER,
    NEON_GREEN, CYAN, CYAN_DIM, VIOLET, VIOLET_DIM, MAGENTA, DANGER_RED,
    WHITE, TEXT_MUTED, TEXT_DIM, GOLD, SILVER, BRONZE,
    get_fonts, create_starfield, draw_cosmic_background,
    draw_panel, draw_glow_text, draw_heart,
    draw_invader_sprite, draw_crt_overlay,
    UIButton, UITextInput
)

SHIP_COLORS = ["green", "blue", "red", "yellow", "purple"]
CONTROL_SCHEMES = ["arrows", "wasd"]
DIFFICULTIES = ["easy", "normal", "hard"]
DIFFICULTY_LABELS = {"easy": "Easy", "normal": "Normal", "hard": "Hard"}
DIFFICULTY_SPAWN = {"easy": 3, "normal": 5, "hard": 8}

PILOT_TITLES = ["Space Cadet", "Starfighter", "Ace Pilot", "Galactic Hero", "Sector Legend"]


class GameManager:
    def __init__(self, screen, screen_width, screen_height, player_name=""):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.player_name = player_name.strip()
        self.previous_state = "dashboard"

        self.db = DBManager(user="root", password="")
        self.settings_manager = SettingsManager("settings.json")
        self.audio = AudioManager(self.settings_manager)

        self.fonts = get_fonts()
        self.stars = create_starfield(screen_width, screen_height, count=95)
        self.tick = 0
        self.explosions = []
        self.floating_texts = []
        self.wave_number = 1

        self.profile_ship_color = "green"
        self.profile_control = "arrows"
        self.profile_difficulty = "normal"
        self.profile_player_title = "Space Cadet"

        self.personal_best = 0
        self.latest_score = None
        self.total_games = 0
        self.leaderboard = []

        cx = screen_width // 2
        field_w = 380
        self.auth_mode = "login"
        self.auth_error = ""
        self.auth_success = ""

        self.login_user_input = UITextInput(
            (cx - field_w // 2, 240, field_w, 44),
            placeholder="Enter callsign / username...",
            label="PILOT CALLSIGN",
        )
        self.login_pass_input = UITextInput(
            (cx - field_w // 2, 314, field_w, 44),
            placeholder="Enter security key...",
            masked=True,
            label="SECURITY KEY",
        )
        self.login_btn = UIButton((cx - 190, 376, 182, 44), "INSERT COIN / IN", style="primary", audio_manager=self.audio)
        self.login_switch_reg_btn = UIButton((cx + 8, 376, 182, 44), "NEW PILOT", style="secondary", audio_manager=self.audio)
        self.login_lb_btn = UIButton((cx - 130, 434, 260, 36), "HIGH SCORES TABLE", style="gold", audio_manager=self.audio)

        self.reg_user_input = UITextInput(
            (cx - field_w // 2, 205, field_w, 44),
            placeholder="Choose callsign (3+ chars)...",
            label="NEW CALLSIGN",
        )
        self.reg_pass_input = UITextInput(
            (cx - field_w // 2, 278, field_w, 44),
            placeholder="Choose security key (4+ chars)...",
            masked=True,
            label="SECURITY KEY",
        )
        self.reg_conf_input = UITextInput(
            (cx - field_w // 2, 351, field_w, 44),
            placeholder="Confirm security key...",
            masked=True,
            label="CONFIRM KEY",
        )
        self.reg_submit_btn = UIButton((cx - 190, 415, 182, 44), "ENLIST PILOT", style="primary", audio_manager=self.audio)
        self.reg_back_btn = UIButton((cx + 8, 415, 182, 44), "< SIGN IN", style="secondary", audio_manager=self.audio)

        self.dash_nav_btn = UIButton((202, 12, 104, 36), "COMMAND", style="tab", audio_manager=self.audio)
        self.dash_nav_btn.is_active = True
        self.dash_lb_nav_btn = UIButton((312, 12, 114, 36), "HI-SCORES", style="tab", audio_manager=self.audio)
        self.dash_prof_nav_btn = UIButton((432, 12, 96, 36), "LOADOUT", style="tab", audio_manager=self.audio)
        self.dash_logout_btn = UIButton((704, 12, 82, 36), "LOG OUT", style="danger", audio_manager=self.audio)

        self.dash_play_btn = UIButton((45, 442, 382, 54), "LAUNCH MISSION", style="primary", audio_manager=self.audio)
        self.dash_view_full_lb_btn = UIButton((482, 522, 282, 38), "HALL OF FAME ->", style="gold", audio_manager=self.audio)

        self.lb_back_btn = UIButton((cx - 110, 535, 220, 44), "< RETURN", style="primary", audio_manager=self.audio)

        self.prof_save_btn = UIButton((cx - 180, 534, 172, 44), "SAVE CONFIG", style="primary", audio_manager=self.audio)
        self.prof_back_btn = UIButton((cx + 8, 534, 172, 44), "< RETURN", style="secondary", audio_manager=self.audio)
        self.profile_notice = ""

        self.paused_from_state = "playing"
        self.saved_volume = 100
        self.hud_pause_btn = UIButton((688, 12, 98, 34), "[ESC] PAUSE", style="secondary", audio_manager=self.audio)
        self.pause_resume_btn = UIButton((cx - 150, 230, 300, 46), "RESUME MISSION", style="primary", audio_manager=self.audio)
        self.pause_restart_btn = UIButton((cx - 150, 288, 300, 44), "RESTART MISSION", style="secondary", audio_manager=self.audio)
        self.pause_mute_btn = UIButton((cx - 150, 344, 300, 44), "AUDIO: ON", style="gold", audio_manager=self.audio)
        self.pause_hq_btn = UIButton((cx - 150, 400, 300, 44), "ABORT TO HQ", style="danger", audio_manager=self.audio)

        self.go_play_again_btn = UIButton((cx - 190, 442, 182, 48), "PLAY AGAIN", style="primary", audio_manager=self.audio)
        self.go_dashboard_btn = UIButton((cx + 8, 442, 182, 48), "COMMAND HQ", style="secondary", audio_manager=self.audio)
        self.go_view_lb_btn = UIButton((cx - 130, 502, 260, 38), "HIGH SCORES TABLE", style="gold", audio_manager=self.audio)

        self.reset_game()

    def reset_game(self):
        self.player = Player(self.screen_width, self.screen_height, self.profile_ship_color)
        self.buttons = MobileButtons()
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.explosions = []
        self.floating_texts = []

        self.score = 0
        self.wave_number = 1
        self.max_player_lives = 3
        self.player_lives = self.max_player_lives
        self.spawn_number = DIFFICULTY_SPAWN.get(self.profile_difficulty, 5)
        self.game_state = "login" if not self.player_name else "dashboard"

        self.timer = 0
        self.state_timer = 0
        self.enemy_direction = 1
        self.enemy_fire_timer = 0
        self.fire_cooldown = 0

    def _load_profile_from_db(self):
        if not self.player_name:
            return

        profile = self.db.get_player_profile(self.player_name)
        if profile:
            self.profile_ship_color = profile.get("ship_color", "green") or "green"
            self.profile_control = profile.get("control_scheme", "arrows") or "arrows"
            self.profile_difficulty = profile.get("difficulty", "normal") or "normal"
            self.profile_player_title = profile.get("player_title", "Space Cadet") or "Space Cadet"
            self.player.set_color(self.profile_ship_color)

        self.personal_best = self.db.get_player_best_score(self.player_name)
        self.latest_score = self.db.get_player_latest_score(self.player_name)
        self.total_games = self.db.get_player_games_count(self.player_name)
        self.leaderboard = self.db.get_top_scores(limit=10)

    def _save_profile_to_db(self):
        if not self.player_name:
            return
        self.db.get_or_create_player(self.player_name)
        self.db.update_player_profile(
            self.player_name,
            ship_color=self.profile_ship_color,
            player_title=self.profile_player_title,
            control_scheme=self.profile_control,
            difficulty=self.profile_difficulty,
        )

    def _after_login(self):
        self._load_profile_from_db()
        self.spawn_number = DIFFICULTY_SPAWN.get(self.profile_difficulty, 5)
        self.player.set_color(self.profile_ship_color)
        self.game_state = "dashboard"
        self.audio.play_ui_click()

    def _start_mission(self):
        self.player = Player(self.screen_width, self.screen_height, self.profile_ship_color)
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.explosions = []
        self.floating_texts = []
        self.score = 0
        self.wave_number = 1
        self.player_lives = self.max_player_lives
        self.spawn_number = DIFFICULTY_SPAWN.get(self.profile_difficulty, 5)
        self.spawn_enemies()
        self.game_state = "playing"
        self.audio.play_game_start()

    def spawn_enemies(self):
        self.enemies = []
        self.enemy_direction = 1
        for i in range(self.spawn_number):
            enemy = Enemy(i, self.spawn_number, self.screen_width, self.screen_height)
            enemy.direction = self.enemy_direction
            enemy.y = 90 + (i % 4) * 34
            self.enemies.append(enemy)
        self.timer = 0

    def update(self, events):
        self.tick += 1
        mouse_pos = pygame.mouse.get_pos()

        if self.game_state == "login":
            self.login_btn.update(mouse_pos)
            self.login_switch_reg_btn.update(mouse_pos)
            self.login_lb_btn.update(mouse_pos)
            self._update_login(events)
        elif self.game_state == "register":
            self.reg_submit_btn.update(mouse_pos)
            self.reg_back_btn.update(mouse_pos)
            self._update_register(events)
        elif self.game_state == "dashboard":
            self.dash_nav_btn.update(mouse_pos)
            self.dash_lb_nav_btn.update(mouse_pos)
            self.dash_prof_nav_btn.update(mouse_pos)
            self.dash_logout_btn.update(mouse_pos)
            self.dash_play_btn.update(mouse_pos)
            self.dash_view_full_lb_btn.update(mouse_pos)
            self._update_dashboard(events)
        elif self.game_state == "leaderboard":
            self.lb_back_btn.update(mouse_pos)
            self._update_leaderboard(events)
        elif self.game_state == "profile":
            self.prof_save_btn.update(mouse_pos)
            self.prof_back_btn.update(mouse_pos)
            self._update_profile(events)
        elif self.game_state in ("playing", "blinking"):
            self.hud_pause_btn.update(mouse_pos)
            self._update_playing(events)
        elif self.game_state == "paused":
            self.pause_resume_btn.update(mouse_pos)
            self.pause_restart_btn.update(mouse_pos)
            self.pause_mute_btn.update(mouse_pos)
            self.pause_hq_btn.update(mouse_pos)
            self._update_paused(events)
        elif self.game_state == "game_over":
            self.go_play_again_btn.update(mouse_pos)
            self.go_dashboard_btn.update(mouse_pos)
            self.go_view_lb_btn.update(mouse_pos)
            self._update_game_over(events)

        draw_crt_overlay(self.screen)

    def _update_login(self, events):
        for event in events:
            self.login_user_input.handle_event(event)
            self.login_pass_input.handle_event(event)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    if self.login_user_input.is_focused:
                        self.login_user_input.is_focused = False
                        self.login_pass_input.is_focused = True
                    else:
                        self.login_user_input.is_focused = True
                        self.login_pass_input.is_focused = False
                elif event.key == pygame.K_RETURN:
                    self._do_login()
                    return

            if self.login_btn.handle_event(event):
                self._do_login()
                return

            if self.login_switch_reg_btn.handle_event(event):
                self.reg_user_input.text = self.login_user_input.text
                self.reg_pass_input.text = ""
                self.reg_conf_input.text = ""
                self.auth_error = ""
                self.auth_success = ""
                self.reg_user_input.is_focused = True
                self.game_state = "register"
                return

            if self.login_lb_btn.handle_event(event):
                self.previous_state = "login"
                self.leaderboard = self.db.get_top_scores(limit=10)
                self.game_state = "leaderboard"
                return

        self._draw_login()

    def _do_login(self):
        user = self.login_user_input.text.strip()
        pw = self.login_pass_input.text
        if not user:
            self.auth_error = "Please enter your pilot callsign."
            return
        if not pw:
            self.auth_error = "Please enter your security key."
            return

        row = self.db.login_player(user, pw)
        if row:
            self.player_name = row["username"]
            self.auth_error = ""
            self.login_pass_input.text = ""
            self._after_login()
        else:
            self.auth_error = "Invalid callsign or security key."

    def _draw_login(self):
        draw_cosmic_background(self.screen, self.stars, self.tick)
        cx = self.screen_width // 2
        anim_frame = (self.tick // 24) % 2
        bob = int(math.sin(self.tick * 0.08) * 4)

        draw_invader_sprite(self.screen, cx - 285, 52 + bob, kind="crab", scale=3, color=NEON_GREEN, frame=anim_frame)
        draw_invader_sprite(self.screen, cx + 285, 52 - bob, kind="crab", scale=3, color=NEON_GREEN, frame=anim_frame)

        draw_glow_text(self.screen, self.fonts["hero"], "SPACE INVADERS", cx, 42, color=NEON_GREEN)
        draw_glow_text(self.screen, self.fonts["body"], "// SECTOR DEFENSE ARCADE 2.0 //", cx, 80, color=CYAN)


        card = pygame.Rect(cx - 225, 154, 450, 336)
        draw_panel(self.screen, card, fill=PANEL_BG, border=PANEL_BORDER, radius=12, top_accent=NEON_GREEN)

        tab_lbl = self.fonts["header"].render("[ PILOT AUTHENTICATION ]", True, WHITE)
        self.screen.blit(tab_lbl, (cx - tab_lbl.get_width() // 2, 174))

        self.login_user_input.draw(self.screen, self.fonts["mono"], label_font=self.fonts["tiny"])
        self.login_pass_input.draw(self.screen, self.fonts["mono"], label_font=self.fonts["tiny"])

        self.login_btn.draw(self.screen, self.fonts["body"])
        self.login_switch_reg_btn.draw(self.screen, self.fonts["body"])
        self.login_lb_btn.draw(self.screen, self.fonts["body"])

        if self.auth_error:
            err_bg = pygame.Rect(cx - 190, 502, 380, 28)
            pygame.draw.rect(self.screen, (55, 14, 22), err_bg, border_radius=6)
            pygame.draw.rect(self.screen, DANGER_RED, err_bg, 1, border_radius=6)
            err = self.fonts["tiny"].render(f"! {self.auth_error}", True, DANGER_RED)
            self.screen.blit(err, (cx - err.get_width() // 2, 510))

        if (self.tick // 30) % 2 == 0 and not self.auth_error:
            coin_txt = self.fonts["tiny"].render("* INSERT CREDENTIALS TO START MISSION *", True, GOLD)
            self.screen.blit(coin_txt, (cx - coin_txt.get_width() // 2, 542))

        hint = self.fonts["tiny"].render("TAB : SWITCH FIELD   |   ENTER : AUTHENTICATE", True, TEXT_DIM)
        self.screen.blit(hint, (cx - hint.get_width() // 2, self.screen_height - 24))

    def _update_register(self, events):
        for event in events:
            self.reg_user_input.handle_event(event)
            self.reg_pass_input.handle_event(event)
            self.reg_conf_input.handle_event(event)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    if self.reg_user_input.is_focused:
                        self.reg_user_input.is_focused = False
                        self.reg_pass_input.is_focused = True
                    elif self.reg_pass_input.is_focused:
                        self.reg_pass_input.is_focused = False
                        self.reg_conf_input.is_focused = True
                    else:
                        self.reg_conf_input.is_focused = False
                        self.reg_user_input.is_focused = True
                elif event.key == pygame.K_RETURN:
                    self._do_register()
                    return

            if self.reg_submit_btn.handle_event(event):
                self._do_register()
                return

            if self.reg_back_btn.handle_event(event):
                self.auth_error = ""
                self.login_user_input.text = self.reg_user_input.text
                self.login_pass_input.text = ""
                self.game_state = "login"
                return

        self._draw_register()

    def _do_register(self):
        user = self.reg_user_input.text.strip()
        pw = self.reg_pass_input.text
        conf = self.reg_conf_input.text

        if not user or len(user) < 3:
            self.auth_error = "Callsign must be at least 3 characters."
            return
        if not pw or len(pw) < 4:
            self.auth_error = "Security key must be at least 4 characters."
            return
        if pw != conf:
            self.auth_error = "Security keys do not match."
            return

        ok, result = self.db.register_player(user, pw)
        if ok:
            self.player_name = user
            self.auth_error = ""
            self._after_login()
        else:
            self.auth_error = result

    def _draw_register(self):
        draw_cosmic_background(self.screen, self.stars, self.tick)
        cx = self.screen_width // 2
        anim_frame = (self.tick // 24) % 2

        draw_invader_sprite(self.screen, cx - 280, 50, kind="octopus", scale=3, color=VIOLET, frame=anim_frame)
        draw_invader_sprite(self.screen, cx + 280, 50, kind="octopus", scale=3, color=VIOLET, frame=anim_frame)

        draw_glow_text(self.screen, self.fonts["hero"], "SPACE INVADERS", cx, 42, color=VIOLET)
        draw_glow_text(self.screen, self.fonts["body"], "// NEW PILOT ENLISTMENT TERMINAL //", cx, 82, color=CYAN)

        card = pygame.Rect(cx - 225, 125, 450, 360)
        draw_panel(self.screen, card, fill=PANEL_BG, border=PANEL_BORDER, radius=12, top_accent=VIOLET)

        tab_lbl = self.fonts["header"].render("[ REGISTER NEW CALLSIGN ]", True, WHITE)
        self.screen.blit(tab_lbl, (cx - tab_lbl.get_width() // 2, 145))

        self.reg_user_input.draw(self.screen, self.fonts["mono"], label_font=self.fonts["tiny"])
        self.reg_pass_input.draw(self.screen, self.fonts["mono"], label_font=self.fonts["tiny"])
        self.reg_conf_input.draw(self.screen, self.fonts["mono"], label_font=self.fonts["tiny"])

        self.reg_submit_btn.draw(self.screen, self.fonts["body"])
        self.reg_back_btn.draw(self.screen, self.fonts["body"])

        if self.auth_error:
            err_bg = pygame.Rect(cx - 190, 500, 380, 28)
            pygame.draw.rect(self.screen, (55, 14, 22), err_bg, border_radius=6)
            pygame.draw.rect(self.screen, DANGER_RED, err_bg, 1, border_radius=6)
            err = self.fonts["tiny"].render(f"! {self.auth_error}", True, DANGER_RED)
            self.screen.blit(err, (cx - err.get_width() // 2, 508))

    def _update_dashboard(self, events):
        for event in events:
            if self.dash_play_btn.handle_event(event):
                self._start_mission()
                return

            if self.dash_lb_nav_btn.handle_event(event) or self.dash_view_full_lb_btn.handle_event(event):
                self.previous_state = "dashboard"
                self.leaderboard = self.db.get_top_scores(limit=10)
                self.game_state = "leaderboard"
                return

            if self.dash_prof_nav_btn.handle_event(event):
                self.previous_state = "dashboard"
                self.profile_notice = ""
                self.game_state = "profile"
                return

            if self.dash_logout_btn.handle_event(event):
                self.player_name = ""
                self.auth_error = ""
                self.login_pass_input.text = ""
                self.game_state = "login"
                return

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self._start_mission()
                return

        self._draw_dashboard()

    def _draw_dashboard(self):
        draw_cosmic_background(self.screen, self.stars, self.tick)
        anim_frame = (self.tick // 25) % 2

        nav_rect = pygame.Rect(0, 0, self.screen_width, 60)
        draw_panel(self.screen, nav_rect, fill=(10, 14, 26), border=(35, 48, 82), radius=0)

        draw_invader_sprite(self.screen, 26, 30, kind="crab", scale=2, color=NEON_GREEN, frame=anim_frame, glow=False)
        draw_glow_text(self.screen, self.fonts["brand"], "INVADERS 2.0", 48, 21, color=NEON_GREEN, center=False)

        self.dash_nav_btn.draw(self.screen, self.fonts["tiny"])
        self.dash_lb_nav_btn.draw(self.screen, self.fonts["tiny"])
        self.dash_prof_nav_btn.draw(self.screen, self.fonts["tiny"])

        badge_rect = pygame.Rect(534, 12, 162, 36)
        draw_panel(self.screen, badge_rect, fill=PANEL_BG_SUB, border=CYAN_DIM, radius=6)
        p_name_surf = self.fonts["tiny"].render(f"PILOT: {self.player_name[:10]}", True, CYAN)
        p_title_surf = self.fonts["tiny"].render(self.profile_player_title[:16], True, NEON_GREEN)
        self.screen.blit(p_name_surf, (badge_rect.centerx - p_name_surf.get_width() // 2, 16))
        self.screen.blit(p_title_surf, (badge_rect.centerx - p_title_surf.get_width() // 2, 31))

        self.dash_logout_btn.draw(self.screen, self.fonts["tiny"])

        hero_x = 24
        hero_w = 425

        hero_card = pygame.Rect(hero_x, 72, hero_w, 74)
        draw_panel(self.screen, hero_card, fill=PANEL_BG, border=PANEL_BORDER, radius=10, top_accent=NEON_GREEN)
        tag_lbl = self.fonts["tiny"].render("// DEFENSE HEADQUARTERS • SECTOR 7", True, NEON_GREEN)
        self.screen.blit(tag_lbl, (hero_x + 16, 82))
        ready_lbl = self.fonts["header"].render("ALIEN FLEET DETECTED", True, WHITE)
        self.screen.blit(ready_lbl, (hero_x + 16, 98))
        sub_lbl = self.fonts["tiny"].render("Man your starfighter and repel the orbital invasion.", True, TEXT_MUTED)
        self.screen.blit(sub_lbl, (hero_x + 16, 124))

        stats_y = 156
        stat_w = 135

        card_pb = pygame.Rect(hero_x, stats_y, stat_w, 72)
        draw_panel(self.screen, card_pb, fill=PANEL_BG_SUB, border=GOLD, radius=8)
        lbl_pb = self.fonts["tiny"].render("HI-SCORE", True, GOLD)
        self.screen.blit(lbl_pb, (hero_x + 12, stats_y + 10))
        val_pb = self.fonts["mono"].render(f"{self.personal_best:05d}", True, GOLD)
        self.screen.blit(val_pb, (hero_x + 12, stats_y + 34))

        card_ls = pygame.Rect(hero_x + stat_w + 10, stats_y, stat_w, 72)
        draw_panel(self.screen, card_ls, fill=PANEL_BG_SUB, border=CYAN_DIM, radius=8)
        lbl_ls = self.fonts["tiny"].render("LAST SCORE", True, CYAN)
        self.screen.blit(lbl_ls, (card_ls.x + 12, stats_y + 10))
        val_ls_str = f"{self.latest_score:05d}" if self.latest_score is not None else "-----"
        val_ls = self.fonts["mono"].render(val_ls_str, True, WHITE)
        self.screen.blit(val_ls, (card_ls.x + 12, stats_y + 34))

        card_tg = pygame.Rect(hero_x + (stat_w + 10) * 2, stats_y, stat_w, 72)
        draw_panel(self.screen, card_tg, fill=PANEL_BG_SUB, border=VIOLET, radius=8)
        lbl_tg = self.fonts["tiny"].render("SORTIES", True, VIOLET)
        self.screen.blit(lbl_tg, (card_tg.x + 12, stats_y + 10))
        val_tg = self.fonts["mono"].render(f"{self.total_games:03d}", True, WHITE)
        self.screen.blit(val_tg, (card_tg.x + 12, stats_y + 34))

        hangar_card = pygame.Rect(hero_x, 238, hero_w, 342)
        draw_panel(self.screen, hangar_card, fill=PANEL_BG, border=PANEL_BORDER, radius=10, top_accent=CYAN)

        h_title = self.fonts["tiny"].render("// HANGAR BAY 01 • INTERCEPTOR READY", True, CYAN)
        self.screen.blit(h_title, (hero_x + 16, 248))

        dock_cx = hero_x + hero_w // 2
        dock_cy = 332
        pulse = 1.0 + 0.06 * math.sin(self.tick * 0.08)

        pygame.draw.line(self.screen, (25, 38, 64), (dock_cx - 85, dock_cy), (dock_cx + 85, dock_cy), 1)
        pygame.draw.line(self.screen, (25, 38, 64), (dock_cx, dock_cy - 60), (dock_cx, dock_cy + 60), 1)

        glow_surf = pygame.Surface((150, 150), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*NEON_GREEN, 24), (75, 75), int(56 * pulse))
        pygame.draw.circle(glow_surf, (*CYAN, 40), (75, 75), int(40 * pulse))
        self.screen.blit(glow_surf, (dock_cx - 75, dock_cy - 75))

        pygame.draw.circle(self.screen, (40, 62, 98), (dock_cx, dock_cy), 54, 2)
        pygame.draw.circle(self.screen, NEON_GREEN, (dock_cx, dock_cy), 58, 1)

        flame_h = 10 + int(6 * abs(math.sin(self.tick * 0.25)))
        pygame.draw.polygon(
            self.screen,
            CYAN,
            [
                (dock_cx - 8, dock_cy + 28),
                (dock_cx + 8, dock_cy + 28),
                (dock_cx, dock_cy + 28 + flame_h),
            ],
        )

        self.screen.blit(self.player.image, (dock_cx - self.player.width // 2, dock_cy - self.player.height // 2))

        spec_str = f"[ HULL: {self.profile_ship_color.upper()} ]  [ CTRL: {self.profile_control.upper()} ]  [ WAVE: {self.profile_difficulty.upper()} ]"
        spec_surf = self.fonts["tiny"].render(spec_str, True, NEON_GREEN)
        self.screen.blit(spec_surf, (dock_cx - spec_surf.get_width() // 2, 404))

        self.dash_play_btn.draw(self.screen, self.fonts["header"])

        ctrl_msg = "MOVE: ARROWS / WASD   •   FIRE: SPACEBAR   •   LAUNCH: ENTER"
        ctrl_surf = self.fonts["tiny"].render(ctrl_msg, True, TEXT_DIM)
        self.screen.blit(ctrl_surf, (dock_cx - ctrl_surf.get_width() // 2, 548))

        lb_panel_x = 468
        lb_panel_w = 310
        lb_panel = pygame.Rect(lb_panel_x, 72, lb_panel_w, 508)
        draw_panel(self.screen, lb_panel, fill=PANEL_BG, border=PANEL_BORDER, radius=10, top_accent=GOLD)

        draw_invader_sprite(self.screen, lb_panel_x + 28, 98, kind="ufo", scale=2, color=GOLD, frame=anim_frame, glow=False)
        lb_header = self.fonts["header"].render("TOP 5 ACES", True, GOLD)
        self.screen.blit(lb_header, (lb_panel_x + 54, 84))
        lb_sub = self.fonts["tiny"].render("LIVE ARCADE LEADERBOARD", True, TEXT_MUTED)
        self.screen.blit(lb_sub, (lb_panel_x + 54, 110))

        pygame.draw.line(self.screen, (38, 50, 82), (lb_panel_x + 14, 132), (lb_panel_x + lb_panel_w - 14, 132), 1)

        col_r = self.fonts["tiny"].render("RNK", True, TEXT_DIM)
        col_p = self.fonts["tiny"].render("PILOT", True, TEXT_DIM)
        col_s = self.fonts["tiny"].render("SCORE", True, TEXT_DIM)
        self.screen.blit(col_r, (lb_panel_x + 16, 140))
        self.screen.blit(col_p, (lb_panel_x + 56, 140))
        self.screen.blit(col_s, (lb_panel_x + lb_panel_w - col_s.get_width() - 18, 140))

        top5 = self.leaderboard[:5]
        row_y = 164
        rank_colors = {1: GOLD, 2: SILVER, 3: BRONZE}

        for i in range(1, 6):
            entry = top5[i - 1] if i <= len(top5) else None
            is_me = entry and entry.get("username") == self.player_name

            row_rect = pygame.Rect(lb_panel_x + 10, row_y, lb_panel_w - 20, 56)
            row_fill = (20, 44, 52) if is_me else ((20, 26, 44) if i % 2 == 1 else (14, 18, 32))
            row_border = NEON_GREEN if is_me else (GOLD if i == 1 else PANEL_BORDER)

            draw_panel(self.screen, row_rect, fill=row_fill, border=row_border, radius=6)

            r_col = rank_colors.get(i, TEXT_MUTED)
            badge_r = pygame.Rect(row_rect.x + 8, row_rect.y + 12, 30, 32)
            pygame.draw.rect(self.screen, (10, 14, 24), badge_r, border_radius=4)
            pygame.draw.rect(self.screen, r_col, badge_r, 1, border_radius=4)
            r_num = self.fonts["body"].render(f"{i}", True, r_col)
            self.screen.blit(r_num, (badge_r.centerx - r_num.get_width() // 2, badge_r.centery - r_num.get_height() // 2))

            if entry:
                p_name = entry.get("username", "Unknown")[:11]
                name_surf = self.fonts["body"].render(p_name, True, NEON_GREEN if is_me else WHITE)
                self.screen.blit(name_surf, (row_rect.x + 48, row_rect.y + 10))

                achieved = str(entry.get("achieved_at", ""))[:10]
                date_surf = self.fonts["tiny"].render(achieved or "VERIFIED", True, TEXT_DIM)
                self.screen.blit(date_surf, (row_rect.x + 48, row_rect.y + 32))

                score_surf = self.fonts["mono"].render(f"{entry.get('score', 0):05d}", True, r_col if i <= 3 else CYAN)
                self.screen.blit(score_surf, (row_rect.right - score_surf.get_width() - 12, row_rect.y + 18))
            else:
                empty_lbl = self.fonts["tiny"].render("--- SLOT OPEN ---", True, TEXT_DIM)
                self.screen.blit(empty_lbl, (row_rect.x + 48, row_rect.y + 21))

            row_y += 66

        self.dash_view_full_lb_btn.draw(self.screen, self.fonts["body"])

    def _update_leaderboard(self, events):
        for event in events:
            if self.lb_back_btn.handle_event(event) or (
                event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN)
            ):
                self.game_state = self.previous_state
                return

        self._draw_leaderboard()

    def _draw_leaderboard(self):
        draw_cosmic_background(self.screen, self.stars, self.tick)
        cx = self.screen_width // 2
        anim_frame = (self.tick // 20) % 2

        draw_invader_sprite(self.screen, cx - 265, 36, kind="ufo", scale=3, color=GOLD, frame=anim_frame)
        draw_invader_sprite(self.screen, cx + 265, 36, kind="ufo", scale=3, color=GOLD, frame=anim_frame)

        draw_glow_text(self.screen, self.fonts["title"], "HALL OF FAME", cx, 32, color=GOLD)
        draw_glow_text(self.screen, self.fonts["tiny"], "// TOP 10 SECTOR DEFENDERS //", cx, 62, color=CYAN)

        board_rect = pygame.Rect(cx - 340, 82, 680, 438)
        draw_panel(self.screen, board_rect, fill=PANEL_BG, border=PANEL_BORDER, radius=12, top_accent=GOLD)

        hdr_y = 96
        self.screen.blit(self.fonts["tiny"].render("RANK", True, TEXT_DIM), (board_rect.x + 24, hdr_y))
        self.screen.blit(self.fonts["tiny"].render("PILOT CALLSIGN", True, TEXT_DIM), (board_rect.x + 95, hdr_y))
        self.screen.blit(self.fonts["tiny"].render("DATE RECORDED", True, TEXT_DIM), (board_rect.x + 340, hdr_y))
        self.screen.blit(self.fonts["tiny"].render("HIGH SCORE", True, TEXT_DIM), (board_rect.right - 115, hdr_y))
        pygame.draw.line(self.screen, (38, 52, 86), (board_rect.x + 16, 114), (board_rect.right - 16, 114), 1)

        rank_colors = {1: GOLD, 2: SILVER, 3: BRONZE}
        scores = self.leaderboard[:10] if self.leaderboard else []

        row_y = 122
        for idx in range(10):
            rank = idx + 1
            entry = scores[idx] if idx < len(scores) else None
            is_me = entry and entry.get("username") == self.player_name

            row_rect = pygame.Rect(board_rect.x + 14, row_y, board_rect.width - 28, 36)
            row_fill = (20, 44, 52) if is_me else ((20, 26, 44) if idx % 2 == 0 else (14, 18, 32))
            row_border = NEON_GREEN if is_me else (GOLD if rank == 1 else PANEL_BORDER)
            draw_panel(self.screen, row_rect, fill=row_fill, border=row_border, radius=6)

            r_col = rank_colors.get(rank, TEXT_MUTED)
            rk_surf = self.fonts["body"].render(f"#{rank:02d}", True, r_col)
            self.screen.blit(rk_surf, (row_rect.x + 14, row_rect.centery - rk_surf.get_height() // 2))

            if entry:
                uname = str(entry.get("username", "UNKNOWN"))[:16]
                achieved = str(entry.get("achieved_at", "VERIFIED"))[:10]
                s_val = int(entry.get("score", 0))

                name_surf = self.fonts["body"].render(uname, True, NEON_GREEN if is_me else WHITE)
                date_surf = self.fonts["tiny"].render(achieved, True, TEXT_MUTED)
                score_surf = self.fonts["mono"].render(f"{s_val:06d}", True, r_col if rank <= 3 else CYAN)

                self.screen.blit(name_surf, (row_rect.x + 82, row_rect.centery - name_surf.get_height() // 2))
                self.screen.blit(date_surf, (row_rect.x + 326, row_rect.centery - date_surf.get_height() // 2))
                self.screen.blit(
                    score_surf,
                    (row_rect.right - score_surf.get_width() - 18, row_rect.centery - score_surf.get_height() // 2),
                )
            else:
                empty_surf = self.fonts["tiny"].render("--- UNCLAIMED ARCADE SLOT ---", True, TEXT_DIM)
                self.screen.blit(empty_surf, (row_rect.x + 82, row_rect.centery - empty_surf.get_height() // 2))

            row_y += 39

        self.lb_back_btn.draw(self.screen, self.fonts["body"])

    def _update_profile(self, events):
        cx = self.screen_width // 2

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game_state = self.previous_state
                return

            if self.prof_save_btn.handle_event(event):
                self._save_profile_to_db()
                self.spawn_number = DIFFICULTY_SPAWN.get(self.profile_difficulty, 5)
                self.player.set_color(self.profile_ship_color)
                self.profile_notice = "LOADOUT & SYSTEM CONFIG SAVED!"
                return

            if self.prof_back_btn.handle_event(event):
                self.game_state = self.previous_state
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                for i, col_name in enumerate(SHIP_COLORS):
                    pill = pygame.Rect(cx - 295 + i * 120, 155, 110, 38)
                    if pill.collidepoint(mx, my):
                        self.profile_ship_color = col_name
                        self.player.set_color(col_name)
                        self.audio.play_ui_click()
                        self.profile_notice = ""

                for i, title in enumerate(PILOT_TITLES):
                    pill = pygame.Rect(cx - 295 + i * 120, 235, 112, 34)
                    if pill.collidepoint(mx, my):
                        self.profile_player_title = title
                        self.audio.play_ui_click()
                        self.profile_notice = ""

                for i, ctrl in enumerate(CONTROL_SCHEMES):
                    pill = pygame.Rect(cx - 295 + i * 145, 315, 135, 38)
                    if pill.collidepoint(mx, my):
                        self.profile_control = ctrl
                        self.audio.play_ui_click()
                        self.profile_notice = ""

                for i, diff in enumerate(DIFFICULTIES):
                    pill = pygame.Rect(cx + 15 + i * 95, 315, 88, 38)
                    if pill.collidepoint(mx, my):
                        self.profile_difficulty = diff
                        self.spawn_number = DIFFICULTY_SPAWN.get(diff, 5)
                        self.audio.play_ui_click()
                        self.profile_notice = ""

                vol_down_rect = pygame.Rect(cx - 295, 402, 42, 36)
                vol_up_rect = pygame.Rect(cx - 105, 402, 42, 36)
                mob_rect = pygame.Rect(cx + 15, 402, 280, 36)

                if vol_down_rect.collidepoint(mx, my):
                    self.audio.set_volume(max(0, self.audio.get_volume() - 10))
                    self.audio.play_ui_click()
                elif vol_up_rect.collidepoint(mx, my):
                    self.audio.set_volume(min(100, self.audio.get_volume() + 10))
                    self.audio.play_ui_click()
                elif mob_rect.collidepoint(mx, my):
                    cur_mob = bool(self.settings_manager.get("mobile_controls", True))
                    self.settings_manager.set("mobile_controls", not cur_mob)
                    self.audio.play_ui_click()

        self._draw_profile()

    def _draw_profile(self):
        draw_cosmic_background(self.screen, self.stars, self.tick)
        cx = self.screen_width // 2
        anim_frame = (self.tick // 22) % 2

        draw_invader_sprite(self.screen, cx - 250, 36, kind="squid", scale=3, color=CYAN, frame=anim_frame)
        draw_invader_sprite(self.screen, cx + 250, 36, kind="squid", scale=3, color=CYAN, frame=anim_frame)

        draw_glow_text(self.screen, self.fonts["title"], "PILOT LOADOUT", cx, 32, color=CYAN)
        draw_glow_text(self.screen, self.fonts["tiny"], "// CUSTOMIZE INTERCEPTOR & ARCADE SYSTEM //", cx, 62, color=NEON_GREEN)

        panel = pygame.Rect(cx - 330, 82, 660, 434)
        draw_panel(self.screen, panel, fill=PANEL_BG, border=PANEL_BORDER, radius=12, top_accent=CYAN)

        lbl1 = self.fonts["tiny"].render("// 01. INTERCEPTOR HULL TINT", True, NEON_GREEN)
        self.screen.blit(lbl1, (cx - 295, 132))
        for i, col_name in enumerate(SHIP_COLORS):
            pill = pygame.Rect(cx - 295 + i * 120, 155, 110, 38)
            sel = (self.profile_ship_color == col_name)
            rgb = SHIP_COLOR_MAP.get(col_name, NEON_GREEN)
            draw_panel(
                self.screen,
                pill,
                fill=(24, 36, 62) if sel else PANEL_BG_SUB,
                border=rgb if sel else PANEL_BORDER,
                radius=6,
                glow_color=rgb if sel else None,
            )
            pygame.draw.circle(self.screen, rgb, (pill.x + 18, pill.centery), 6)
            t_surf = self.fonts["tiny"].render(col_name.upper(), True, WHITE if sel else TEXT_MUTED)
            self.screen.blit(t_surf, (pill.x + 32, pill.centery - t_surf.get_height() // 2))

        lbl2 = self.fonts["tiny"].render("// 02. PILOT RANK DESIGNATION", True, NEON_GREEN)
        self.screen.blit(lbl2, (cx - 295, 212))
        for i, title in enumerate(PILOT_TITLES):
            pill = pygame.Rect(cx - 295 + i * 120, 235, 112, 34)
            sel = (self.profile_player_title == title)
            draw_panel(
                self.screen,
                pill,
                fill=(28, 42, 72) if sel else PANEL_BG_SUB,
                border=GOLD if sel else PANEL_BORDER,
                radius=6,
            )
            t_surf = self.fonts["tiny"].render(title[:12].upper(), True, GOLD if sel else TEXT_MUTED)
            self.screen.blit(t_surf, (pill.centerx - t_surf.get_width() // 2, pill.centery - t_surf.get_height() // 2))

        lbl3 = self.fonts["tiny"].render("// 03. FLIGHT CONTROLS", True, NEON_GREEN)
        self.screen.blit(lbl3, (cx - 295, 292))
        for i, ctrl in enumerate(CONTROL_SCHEMES):
            pill = pygame.Rect(cx - 295 + i * 145, 315, 135, 38)
            sel = (self.profile_control == ctrl)
            draw_panel(
                self.screen,
                pill,
                fill=(22, 48, 56) if sel else PANEL_BG_SUB,
                border=NEON_GREEN if sel else PANEL_BORDER,
                radius=6,
            )
            t_surf = self.fonts["body"].render(ctrl.upper(), True, NEON_GREEN if sel else TEXT_MUTED)
            self.screen.blit(t_surf, (pill.centerx - t_surf.get_width() // 2, pill.centery - t_surf.get_height() // 2))

        lbl4 = self.fonts["tiny"].render("// 04. WAVE THREAT LEVEL", True, NEON_GREEN)
        self.screen.blit(lbl4, (cx + 15, 292))
        for i, diff in enumerate(DIFFICULTIES):
            pill = pygame.Rect(cx + 15 + i * 95, 315, 88, 38)
            sel = (self.profile_difficulty == diff)
            draw_panel(
                self.screen,
                pill,
                fill=(48, 24, 58) if sel else PANEL_BG_SUB,
                border=VIOLET if sel else PANEL_BORDER,
                radius=6,
            )
            t_surf = self.fonts["tiny"].render(DIFFICULTY_LABELS[diff].upper(), True, VIOLET if sel else TEXT_MUTED)
            self.screen.blit(t_surf, (pill.centerx - t_surf.get_width() // 2, pill.centery - t_surf.get_height() // 2))

        lbl5 = self.fonts["tiny"].render("// 05. MASTER VOLUME", True, NEON_GREEN)
        self.screen.blit(lbl5, (cx - 295, 378))
        vol_down_rect = pygame.Rect(cx - 295, 402, 42, 36)
        vol_disp_rect = pygame.Rect(cx - 245, 402, 132, 36)
        vol_up_rect = pygame.Rect(cx - 105, 402, 42, 36)

        draw_panel(self.screen, vol_down_rect, fill=PANEL_BG_SUB, border=CYAN_DIM, radius=6)
        draw_panel(self.screen, vol_disp_rect, fill=(10, 14, 24), border=PANEL_BORDER, radius=6)
        draw_panel(self.screen, vol_up_rect, fill=PANEL_BG_SUB, border=CYAN_DIM, radius=6)

        minus_s = self.fonts["header"].render("-", True, CYAN)
        plus_s = self.fonts["header"].render("+", True, CYAN)
        vol_s = self.fonts["mono"].render(f"{self.audio.get_volume()}%", True, NEON_GREEN)
        self.screen.blit(minus_s, (vol_down_rect.centerx - minus_s.get_width() // 2, vol_down_rect.centery - minus_s.get_height() // 2))
        self.screen.blit(plus_s, (vol_up_rect.centerx - plus_s.get_width() // 2, vol_up_rect.centery - plus_s.get_height() // 2))
        self.screen.blit(vol_s, (vol_disp_rect.centerx - vol_s.get_width() // 2, vol_disp_rect.centery - vol_s.get_height() // 2))

        lbl6 = self.fonts["tiny"].render("// 06. ON-SCREEN TOUCH PAD", True, NEON_GREEN)
        self.screen.blit(lbl6, (cx + 15, 378))
        mob_on = bool(self.settings_manager.get("mobile_controls", True))
        mob_rect = pygame.Rect(cx + 15, 402, 280, 36)
        draw_panel(
            self.screen,
            mob_rect,
            fill=(18, 52, 44) if mob_on else PANEL_BG_SUB,
            border=NEON_GREEN if mob_on else PANEL_BORDER,
            radius=6,
        )
        mob_txt = f"TOUCH CONTROLS: {'ENABLED' if mob_on else 'HIDDEN'}"
        mob_surf = self.fonts["tiny"].render(mob_txt, True, NEON_GREEN if mob_on else TEXT_MUTED)
        self.screen.blit(mob_surf, (mob_rect.centerx - mob_surf.get_width() // 2, mob_rect.centery - mob_surf.get_height() // 2))

        prev_rect = pygame.Rect(cx - 295, 452, 590, 50)
        draw_panel(self.screen, prev_rect, fill=(10, 14, 24), border=PANEL_BORDER, radius=8)
        mini_ship = pygame.transform.smoothscale(self.player.image, (38, 38))
        self.screen.blit(mini_ship, (prev_rect.x + 18, prev_rect.centery - 19))
        summary = f"ACTIVE CONFIG: {self.player_name} ({self.profile_player_title}) • {self.profile_ship_color.upper()} HULL"
        sum_surf = self.fonts["tiny"].render(summary, True, WHITE)
        self.screen.blit(sum_surf, (prev_rect.x + 70, prev_rect.centery - sum_surf.get_height() // 2))

        if self.profile_notice:
            notice_s = self.fonts["tiny"].render(self.profile_notice, True, NEON_GREEN)
            self.screen.blit(notice_s, (cx - notice_s.get_width() // 2, 514))

        self.prof_save_btn.draw(self.screen, self.fonts["body"])
        self.prof_back_btn.draw(self.screen, self.fonts["body"])

    def _fire_player_bullet(self):
        if self.fire_cooldown <= 0 and not self.player.is_blinking:
            bx = self.player.x + self.player.width // 2 - 16
            by = self.player.y - 18
            self.bullets.append(Bullet(bx, by, direction="up", speed=7, screen_height=self.screen_height))
            self.fire_cooldown = 14
            self.audio.play_shoot()

    def _trigger_game_over(self):
        self.audio.play_game_over()
        if self.player_name:
            self.db.save_score(self.player_name, self.score)
            self._load_profile_from_db()
        self.game_state = "game_over"

    def _update_playing(self, events):
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

        for event in events:
            if self.hud_pause_btn.handle_event(event):
                self.paused_from_state = self.game_state
                self.game_state = "paused"
                return

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    self.paused_from_state = self.game_state
                    self.audio.play_ui_click()
                    self.game_state = "paused"
                    return
                elif event.key == pygame.K_SPACE:
                    self._fire_player_bullet()

        keys = pygame.key.get_pressed()
        move_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

        if move_left:
            self.player.move_left()
        if move_right:
            self.player.move_right()
        if keys[pygame.K_SPACE]:
            self._fire_player_bullet()

        if self.settings_manager.get("mobile_controls", True):
            if self.buttons.handle_mouse(self.player, events):
                self._fire_player_bullet()

        self.player.keep_inside_screen()

        if self.game_state == "blinking":
            self.player.update_blink()
            self.state_timer += 1
            if self.state_timer >= 90:
                self.player.is_blinking = False
                self.player.visible = True
                self.state_timer = 0
                if self.player_lives <= 0:
                    self._trigger_game_over()
                    return
                else:
                    self.game_state = "playing"

        for bullet in self.bullets[:]:
            bullet.update()
            if not bullet.is_active:
                self.bullets.remove(bullet)

        player_rect = self.player.get_rect().inflate(-18, -18)
        for ebullet in self.enemy_bullets[:]:
            ebullet.update()
            if not ebullet.is_active:
                self.enemy_bullets.remove(ebullet)
                continue

            if self.game_state == "playing" and ebullet.get_rect().inflate(-10, -10).colliderect(player_rect):
                self.enemy_bullets.remove(ebullet)
                self._damage_player()
                if self.game_state == "game_over":
                    return

        for enemy in self.enemies[:]:
            enemy.update()

            enemy.fire_cooldown -= 1
            if enemy.fire_cooldown <= 0 and enemy.state == "waiting":
                ebx = enemy.x + enemy.width // 2 - 16
                eby = enemy.y + enemy.height - 6
                spd = min(6, 3 + self.wave_number // 2)
                self.enemy_bullets.append(Bullet(ebx, eby, direction="down", speed=spd, screen_height=self.screen_height))
                enemy.fire_cooldown = random.randint(max(45, 130 - self.wave_number * 8), max(90, 210 - self.wave_number * 10))
                self.audio.play_enemy_shoot()

            e_rect = enemy.get_rect().inflate(-8, -8)
            for bullet in self.bullets[:]:
                if bullet.get_rect().inflate(-8, -8).colliderect(e_rect):
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    if enemy in self.enemies:
                        self.enemies.remove(enemy)

                    pts = 20 * self.wave_number
                    self.score += pts
                    if self.score > self.personal_best:
                        self.personal_best = self.score

                    self.audio.play_explosion()
                    self.explosions.append({
                        "x": enemy.x + enemy.width // 2,
                        "y": enemy.y + enemy.height // 2,
                        "timer": 18,
                    })
                    self.floating_texts.append({
                        "text": f"+{pts}",
                        "x": enemy.x + enemy.width // 2,
                        "y": enemy.y,
                        "timer": 28,
                        "color": NEON_GREEN,
                    })
                    break

            if enemy in self.enemies and self.game_state == "playing":
                if e_rect.colliderect(player_rect):
                    self.enemies.remove(enemy)
                    self._damage_player()
                    if self.game_state == "game_over":
                        return

        if not self.enemies:
            self.wave_number += 1
            base_spawn = DIFFICULTY_SPAWN.get(self.profile_difficulty, 5)
            self.spawn_number = min(10, base_spawn + (self.wave_number - 1))
            self.spawn_enemies()
            self.floating_texts.append({
                "text": f"WAVE {self.wave_number:02d} INCOMING!",
                "x": self.screen_width // 2,
                "y": self.screen_height // 2 - 40,
                "timer": 55,
                "color": CYAN,
            })

        for exp in self.explosions[:]:
            exp["timer"] -= 1
            if exp["timer"] <= 0:
                self.explosions.remove(exp)

        for ft in self.floating_texts[:]:
            ft["y"] -= 1.2
            ft["timer"] -= 1
            if ft["timer"] <= 0:
                self.floating_texts.remove(ft)

        self._draw_playing()

    def _damage_player(self):
        self.player_lives -= 1
        self.audio.play_hit()
        self.explosions.append({
            "x": self.player.x + self.player.width // 2,
            "y": self.player.y + self.player.height // 2,
            "timer": 24,
        })
        self.floating_texts.append({
            "text": "HULL BREACH!",
            "x": self.player.x + self.player.width // 2,
            "y": self.player.y - 10,
            "timer": 35,
            "color": DANGER_RED,
        })
        if self.player_lives <= 0:
            self._trigger_game_over()
        else:
            self.player.is_blinking = True
            self.player.blink_timer = 0
            self.state_timer = 0
            self.game_state = "blinking"

    def _draw_playing(self):
        draw_cosmic_background(self.screen, self.stars, self.tick, show_grid=True)

        defense_y = self.screen_height - 96
        pygame.draw.line(self.screen, (0, 243, 255, 70), (20, defense_y), (self.screen_width - 20, defense_y), 1)

        for bullet in self.bullets:
            bullet.draw(self.screen)

        for ebullet in self.enemy_bullets:
            ebullet.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        self.player.draw(self.screen)

        for exp in self.explosions:
            progress = (24 - exp["timer"]) / 24.0
            radius = int(12 + progress * 28)
            pygame.draw.circle(self.screen, GOLD, (int(exp["x"]), int(exp["y"])), radius, 2)
            pygame.draw.circle(self.screen, DANGER_RED, (int(exp["x"]), int(exp["y"])), max(4, radius // 2), 2)

        for ft in self.floating_texts:
            draw_glow_text(self.screen, self.fonts["body"], ft["text"], int(ft["x"]), int(ft["y"]), color=ft["color"])

        hud_rect = pygame.Rect(0, 0, self.screen_width, 58)
        draw_panel(self.screen, hud_rect, fill=(8, 12, 24), border=(35, 55, 92), radius=0)

        s_lbl = self.fonts["tiny"].render("SCORE <1>", True, CYAN)
        s_val = self.fonts["mono"].render(f"{self.score:06d}", True, NEON_GREEN)
        self.screen.blit(s_lbl, (20, 8))
        self.screen.blit(s_val, (20, 26))

        hi_score = max(self.score, self.personal_best)
        h_lbl = self.fonts["tiny"].render("HI-SCORE", True, GOLD)
        h_val = self.fonts["mono"].render(f"{hi_score:06d}", True, GOLD)
        self.screen.blit(h_lbl, (175, 8))
        self.screen.blit(h_val, (175, 26))

        wave_box = pygame.Rect(self.screen_width // 2 - 64, 10, 128, 38)
        draw_panel(self.screen, wave_box, fill=PANEL_BG_SUB, border=VIOLET, radius=6)
        w_txt = self.fonts["body"].render(f"WAVE {self.wave_number:02d}", True, WHITE)
        self.screen.blit(w_txt, (wave_box.centerx - w_txt.get_width() // 2, wave_box.centery - w_txt.get_height() // 2))

        w_lbl = self.fonts["tiny"].render("LASER", True, MAGENTA)
        self.screen.blit(w_lbl, (485, 10))
        bar_bg = pygame.Rect(485, 28, 86, 14)
        pygame.draw.rect(self.screen, (20, 24, 42), bar_bg, border_radius=4)
        charge_ratio = max(0.0, min(1.0, 1.0 - (self.fire_cooldown / 14.0)))
        fill_w = int((bar_bg.width - 4) * charge_ratio)
        if fill_w > 0:
            bar_col = NEON_GREEN if charge_ratio >= 0.95 else MAGENTA
            pygame.draw.rect(self.screen, bar_col, (bar_bg.x + 2, bar_bg.y + 2, fill_w, bar_bg.height - 4), border_radius=3)
        pygame.draw.rect(self.screen, PANEL_BORDER, bar_bg, 1, border_radius=4)

        l_lbl = self.fonts["tiny"].render("HULL", True, DANGER_RED)
        self.screen.blit(l_lbl, (592, 10))
        pulse = 1.0 + 0.08 * math.sin(self.tick * 0.12)
        for i in range(self.max_player_lives):
            draw_heart(
                self.screen,
                592 + i * 28,
                26,
                size=11,
                is_active=(i < self.player_lives),
                pulse=pulse if i < self.player_lives else 1.0,
            )

        self.hud_pause_btn.draw(self.screen, self.fonts["tiny"])

        if self.settings_manager.get("mobile_controls", True):
            self.buttons.draw(self.screen)

    def _update_paused(self, events):
        cur_vol = self.audio.get_volume()
        self.pause_mute_btn.text = f"AUDIO: {'MUTED' if cur_vol == 0 else f'{cur_vol}% (MUTE)'}"

        for event in events:
            if self.pause_resume_btn.handle_event(event):
                self.game_state = self.paused_from_state
                return

            if self.pause_restart_btn.handle_event(event):
                self._start_mission()
                return

            if self.pause_mute_btn.handle_event(event):
                if self.audio.get_volume() > 0:
                    self.saved_volume = self.audio.get_volume()
                    self.audio.set_volume(0)
                else:
                    self.audio.set_volume(self.saved_volume if self.saved_volume > 0 else 100)
                return

            if self.pause_hq_btn.handle_event(event):
                if self.player_name and self.score > 0:
                    self.db.save_score(self.player_name, self.score)
                    self._load_profile_from_db()
                self.game_state = "dashboard"
                return

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p, pygame.K_RETURN):
                    self.audio.play_ui_click()
                    self.game_state = self.paused_from_state
                    return
                elif event.key == pygame.K_r:
                    self._start_mission()
                    return
                elif event.key == pygame.K_q:
                    if self.player_name and self.score > 0:
                        self.db.save_score(self.player_name, self.score)
                        self._load_profile_from_db()
                    self.game_state = "dashboard"
                    return

        self._draw_paused()

    def _draw_paused(self):
        self._draw_playing()

        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((5, 8, 18, 195))
        self.screen.blit(overlay, (0, 0))

        cx = self.screen_width // 2
        anim_frame = (self.tick // 24) % 2

        card = pygame.Rect(cx - 210, 105, 420, 385)
        draw_panel(self.screen, card, fill=PANEL_BG, border=CYAN, radius=12, top_accent=NEON_GREEN, glow_color=CYAN_DIM)

        draw_invader_sprite(self.screen, cx - 155, 145, kind="crab", scale=2, color=NEON_GREEN, frame=anim_frame, glow=False)
        draw_invader_sprite(self.screen, cx + 155, 145, kind="crab", scale=2, color=NEON_GREEN, frame=anim_frame, glow=False)
        draw_glow_text(self.screen, self.fonts["header"], "MISSION PAUSED", cx, 136, color=NEON_GREEN)
        draw_glow_text(self.screen, self.fonts["tiny"], "// TACTICAL STANDBY MODE //", cx, 160, color=CYAN)

        stat_strip = pygame.Rect(cx - 175, 178, 350, 36)
        draw_panel(self.screen, stat_strip, fill=PANEL_BG_SUB, border=PANEL_BORDER, radius=6)
        tele_str = f"SCORE: {self.score:05d}   •   WAVE: {self.wave_number:02d}   •   HULL: {self.player_lives}/{self.max_player_lives}"
        tele_surf = self.fonts["tiny"].render(tele_str, True, GOLD)
        self.screen.blit(tele_surf, (cx - tele_surf.get_width() // 2, stat_strip.centery - tele_surf.get_height() // 2))

        self.pause_resume_btn.draw(self.screen, self.fonts["body"])
        self.pause_restart_btn.draw(self.screen, self.fonts["body"])
        self.pause_mute_btn.draw(self.screen, self.fonts["body"])
        self.pause_hq_btn.draw(self.screen, self.fonts["body"])

        hint = self.fonts["tiny"].render("ESC / ENTER : RESUME   •   R : RESTART   •   Q : HQ", True, TEXT_DIM)
        self.screen.blit(hint, (cx - hint.get_width() // 2, 466))

    def _update_game_over(self, events):
        for event in events:
            if self.go_play_again_btn.handle_event(event):
                self._start_mission()
                return

            if self.go_dashboard_btn.handle_event(event):
                self.game_state = "dashboard"
                return

            if self.go_view_lb_btn.handle_event(event):
                self.previous_state = "game_over"
                self.leaderboard = self.db.get_top_scores(limit=10)
                self.game_state = "leaderboard"
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self._start_mission()
                    return
                elif event.key == pygame.K_ESCAPE:
                    self.game_state = "dashboard"
                    return

        self._draw_game_over()

    def _draw_game_over(self):
        draw_cosmic_background(self.screen, self.stars, self.tick)
        cx = self.screen_width // 2
        anim_frame = (self.tick // 20) % 2

        draw_invader_sprite(self.screen, cx - 235, 78, kind="crab", scale=3, color=DANGER_RED, frame=anim_frame)
        draw_invader_sprite(self.screen, cx + 235, 78, kind="crab", scale=3, color=DANGER_RED, frame=anim_frame)

        draw_glow_text(self.screen, self.fonts["hero"], "GAME OVER", cx, 72, color=DANGER_RED)
        draw_glow_text(self.screen, self.fonts["body"], "// SECTOR DEFENSE BREACHED //", cx, 114, color=CYAN)

        card = pygame.Rect(cx - 230, 148, 460, 272)
        draw_panel(self.screen, card, fill=PANEL_BG, border=PANEL_BORDER, radius=12, top_accent=DANGER_RED)

        is_new_record = self.score > 0 and self.score >= self.personal_best
        badge_text = "* NEW PERSONAL HIGH SCORE! *" if is_new_record else "MISSION TELEMETRY REPORT"
        badge_col = GOLD if is_new_record else TEXT_MUTED
        b_surf = self.fonts["body"].render(badge_text, True, badge_col)
        self.screen.blit(b_surf, (cx - b_surf.get_width() // 2, 168))

        score_box = pygame.Rect(cx - 190, 200, 380, 74)
        draw_panel(self.screen, score_box, fill=(10, 14, 26), border=GOLD if is_new_record else CYAN_DIM, radius=8)
        sc_lbl = self.fonts["tiny"].render("FINAL MISSION SCORE", True, TEXT_MUTED)
        sc_val = self.fonts["mono_large"].render(f"{self.score:06d}", True, NEON_GREEN)
        self.screen.blit(sc_lbl, (cx - sc_lbl.get_width() // 2, 210))
        self.screen.blit(sc_val, (cx - sc_val.get_width() // 2, 230))

        pb_box = pygame.Rect(cx - 190, 288, 182, 62)
        wv_box = pygame.Rect(cx + 8, 288, 182, 62)
        draw_panel(self.screen, pb_box, fill=PANEL_BG_SUB, border=GOLD, radius=8)
        draw_panel(self.screen, wv_box, fill=PANEL_BG_SUB, border=VIOLET, radius=8)

        pb_t = self.fonts["tiny"].render("RECORD SCORE", True, GOLD)
        pb_v = self.fonts["mono"].render(f"{self.personal_best:06d}", True, WHITE)
        self.screen.blit(pb_t, (pb_box.centerx - pb_t.get_width() // 2, pb_box.y + 10))
        self.screen.blit(pb_v, (pb_box.centerx - pb_v.get_width() // 2, pb_box.y + 30))

        wv_t = self.fonts["tiny"].render("WAVE REACHED", True, VIOLET)
        wv_v = self.fonts["mono"].render(f"WAVE {self.wave_number:02d}", True, WHITE)
        self.screen.blit(wv_t, (wv_box.centerx - wv_t.get_width() // 2, wv_box.y + 10))
        self.screen.blit(wv_v, (wv_box.centerx - wv_v.get_width() // 2, wv_box.y + 30))

        pilot_line = self.fonts["tiny"].render(
            f"PILOT: {self.player_name or 'GUEST'}   •   DIFFICULTY: {self.profile_difficulty.upper()}",
            True,
            TEXT_DIM,
        )
        self.screen.blit(pilot_line, (cx - pilot_line.get_width() // 2, 388))

        self.go_play_again_btn.draw(self.screen, self.fonts["body"])
        self.go_dashboard_btn.draw(self.screen, self.fonts["body"])
        self.go_view_lb_btn.draw(self.screen, self.fonts["body"])

        hint = self.fonts["tiny"].render("ENTER : PLAY AGAIN   |   ESC : COMMAND HQ", True, TEXT_DIM)
        self.screen.blit(hint, (cx - hint.get_width() // 2, self.screen_height - 22))