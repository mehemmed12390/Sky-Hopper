import pygame
import sys
import random
import math
import json
import datetime
from enum import Enum
import os

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 50)
PURPLE = (180, 70, 220)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
SKY_BLUE = (135, 206, 235)
DARK_BLUE = (25, 25, 100)
NIGHT_BLUE = (10, 10, 60)

# Game states
class GameState(Enum):
    MAIN_MENU = 1
    PLAYING = 2
    GAME_OVER = 3
    MODE_SELECT = 4
    SETTINGS = 5
    SKIN_SELECTOR = 6
    HIGHSCORE = 7
    BACKGROUND_THEME = 8
    TRAIL_EFFECT = 9

# Game speeds
class GameSpeed(Enum):
    EASY = 1
    NORMAL = 2
    HARD = 3

# Background themes
class BackgroundTheme(Enum):
    DAY = {"name": "Day Mode", "color": SKY_BLUE, "icon": "☀️"}
    NIGHT = {"name": "Night Mode", "color": NIGHT_BLUE, "icon": "🌙"}
    STORM = {"name": "Storm Mode", "color": DARK_BLUE, "icon": "⛈"}

# Trail effects
class TrailEffect(Enum):
    NONE = {"name": "None", "color": None}
    SPARKLE = {"name": "Sparkle", "color": WHITE}
    FIRE = {"name": "Fire", "color": ORANGE}
    RAINBOW = {"name": "Rainbow", "color": None}

# Bird skins
class BirdSkin(Enum):
    RED = {"name": "Classic Red", "price": 30, "color": RED, "unlocked": True, "category": "Classic"}
    GREEN = {"name": "Forest Green", "price": 50, "color": GREEN, "unlocked": False, "category": "Classic"}
    YELLOW = {"name": "Sunshine Yellow", "price": 70, "color": YELLOW, "unlocked": False, "category": "Classic"}
    PURPLE = {"name": "Mystic Purple", "price": 80, "color": PURPLE, "unlocked": False, "category": "Premium"}
    BLUE = {"name": "Ocean Blue", "price": 90, "color": BLUE, "unlocked": False, "category": "Premium"}
    GOLD = {"name": "Golden King", "price": 100, "color": GOLD, "unlocked": False, "category": "Premium"}
    NEON_CYAN = {"name": "Neon Cyber", "price": 120, "color": CYAN, "unlocked": False, "category": "Special"}

class ExplosionParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = random.choice([RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, CYAN])
        self.size = random.randint(5, 15)
        self.speed_x = random.uniform(-5, 5)
        self.speed_y = random.uniform(-5, 5)
        self.lifetime = 60
        self.max_lifetime = 60
       
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.lifetime -= 1
        self.speed_x *= 0.98
        self.speed_y *= 0.98
       
    def draw(self, screen):
        if self.lifetime <= 0:
            return
           
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        particle_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, (*self.color, alpha),
                         (self.size, self.size), self.size)
        screen.blit(particle_surf, (self.x - self.size, self.y - self.size))
       
    def is_alive(self):
        return self.lifetime > 0

class Button:
    def __init__(self, x, y, width, height, text, color=BLUE, hover_color=(70, 170, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.font = pygame.font.SysFont(None, 36)
        self.hovered = False
       
    def draw(self, screen):
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, self.rect, 3, border_radius=10)
       
        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
       
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        self.current_color = self.hover_color if self.hovered else self.color
        return self.hovered
   
    def is_clicked(self, mouse_pos, mouse_click):
        if self.rect.collidepoint(mouse_pos) and mouse_click:
            return True
        return False

class ToggleButton:
    def __init__(self, x, y, width, height, options, initial_index=0):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.current_index = initial_index
        self.font = pygame.font.SysFont(None, 32)
       
    def draw(self, screen):
        pygame.draw.rect(screen, DARK_BLUE, self.rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=10)
       
        text = f"{self.options[self.current_index]}"
        text_surf = self.font.render(text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
       
    def update(self, mouse_pos, mouse_click):
        if self.rect.collidepoint(mouse_pos) and mouse_click:
            self.current_index = (self.current_index + 1) % len(self.options)
            return True
        return False

class BackgroundRenderer:
    def __init__(self):
        self.theme = BackgroundTheme.DAY
        self.clouds = []
        self.stars = []
        self.rain_particles = []
        self.lightning_timer = 0
        self.lightning_alpha = 0
       
        for i in range(5):
            self.clouds.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(50, 200),
                'speed': random.uniform(0.1, 0.3),
                'size': random.randint(40, 80)
            })
           
        for i in range(50):
            self.stars.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, 400),
                'size': random.randint(1, 3),
                'brightness': random.uniform(0.3, 1.0),
                'pulse_speed': random.uniform(0.01, 0.03)
            })
   
    def set_theme(self, theme):
        self.theme = theme
       
    def update(self):
        for cloud in self.clouds:
            cloud['x'] -= cloud['speed']
            if cloud['x'] < -cloud['size'] * 2:
                cloud['x'] = SCREEN_WIDTH + cloud['size'] * 2
                cloud['y'] = random.randint(50, 200)
               
        if self.theme == BackgroundTheme.NIGHT:
            for star in self.stars:
                star['brightness'] = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * star['pulse_speed'] * 0.001)
                   
        if self.theme == BackgroundTheme.STORM:
            if self.lightning_timer > 0:
                self.lightning_timer -= 1
                self.lightning_alpha = max(0, self.lightning_alpha - 10)
            else:
                if random.random() < 0.001:
                    self.lightning_timer = 10
                    self.lightning_alpha = 150
   
    def draw(self, screen):
        if self.theme == BackgroundTheme.DAY:
            screen.fill(SKY_BLUE)
           
            pygame.draw.circle(screen, YELLOW, (100, 80), 40)
           
            for cloud in self.clouds:
                for j in range(3):
                    circle_x = cloud['x'] + j * 25
                    circle_y = cloud['y'] + (j % 2) * 15
                    cloud_surf = pygame.Surface((cloud['size'] * 2, cloud['size'] * 2), pygame.SRCALPHA)
                    pygame.draw.circle(cloud_surf, (255, 255, 255, 150),
                                     (cloud['size'], cloud['size']), cloud['size'])
                    screen.blit(cloud_surf, (circle_x - cloud['size'], circle_y - cloud['size']))
                   
        elif self.theme == BackgroundTheme.NIGHT:
            screen.fill(NIGHT_BLUE)
           
            pygame.draw.circle(screen, SILVER, (SCREEN_WIDTH - 100, 80), 35)
            pygame.draw.circle(screen, NIGHT_BLUE, (SCREEN_WIDTH - 85, 65), 25)
           
            for star in self.stars:
                brightness = int(star['brightness'] * 255)
                pygame.draw.circle(screen, (brightness, brightness, 200),
                                 (int(star['x']), int(star['y'])), star['size'])
               
            for cloud in self.clouds:
                for j in range(3):
                    circle_x = cloud['x'] + j * 25
                    circle_y = cloud['y'] + (j % 2) * 15
                    cloud_surf = pygame.Surface((cloud['size'] * 2, cloud['size'] * 2), pygame.SRCALPHA)
                    pygame.draw.circle(cloud_surf, (100, 100, 150, 80),
                                     (cloud['size'], cloud['size']), cloud['size'])
                    screen.blit(cloud_surf, (circle_x - cloud['size'], circle_y - cloud['size']))
                   
        elif self.theme == BackgroundTheme.STORM:
            screen.fill(DARK_BLUE)
           
            for cloud in self.clouds:
                for j in range(3):
                    circle_x = cloud['x'] + j * 25
                    circle_y = cloud['y'] + (j % 2) * 15
                    cloud_surf = pygame.Surface((cloud['size'] * 2, cloud['size'] * 2), pygame.SRCALPHA)
                    pygame.draw.circle(cloud_surf, (50, 50, 70, 120),
                                     (cloud['size'], cloud['size']), cloud['size'])
                    screen.blit(cloud_surf, (circle_x - cloud['size'], circle_y - cloud['size']))
           
            if self.lightning_alpha > 0:
                lightning_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                lightning_surf.fill((255, 255, 200, self.lightning_alpha))
                screen.blit(lightning_surf, (0, 0))
       
        ground_color = (100, 70, 30)
        grass_color = (80, 150, 50)
       
        pygame.draw.rect(screen, ground_color,
                        (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))
        pygame.draw.rect(screen, grass_color,
                        (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 20))

class Bird:
    def __init__(self, x, y, skin=BirdSkin.RED):
        self.x = x
        self.y = y
        self.velocity = 0
        self.gravity = 0.5
        self.jump_strength = -10
        self.radius = 20
        self.alive = True
        self.skin = skin
        self.flap_frame = 0
        self.flap_speed = 0.2
        self.angle = 0
       
    def update(self):
        self.velocity += self.gravity
        self.y += self.velocity
       
        self.angle = min(max(self.velocity * 3, -30), 90)
       
        self.flap_frame += self.flap_speed
        if self.flap_frame >= 3:
            self.flap_frame = 0
           
        if self.y < 0:
            self.y = 0
            self.velocity = 0
           
    def jump(self):
        self.velocity = self.jump_strength
       
    def draw(self, screen):
        bird_color = self.skin.value["color"]
       
        pygame.draw.circle(screen, bird_color, (int(self.x), int(self.y)), int(self.radius))
       
        pygame.draw.circle(screen, WHITE, (int(self.x + self.radius * 0.5), int(self.y - self.radius * 0.3)), int(self.radius * 0.3))
        pygame.draw.circle(screen, BLACK, (int(self.x + self.radius * 0.5), int(self.y - self.radius * 0.3)), int(self.radius * 0.15))
       
        beak_points = [
            (self.x + self.radius * 0.8, self.y),
            (self.x + self.radius * 1.5, self.y),
            (self.x + self.radius * 0.8, self.y + self.radius * 0.5)
        ]
        pygame.draw.polygon(screen, ORANGE, beak_points)
       
        wing_y_offset = math.sin(self.flap_frame) * 5
        wing_points = [
            (self.x - self.radius * 0.5, self.y),
            (self.x - self.radius * 0.8, self.y + self.radius * 0.5 + wing_y_offset),
            (self.x, self.y + self.radius * 0.3)
        ]
        pygame.draw.polygon(screen, (bird_color[0]//2, bird_color[1]//2, bird_color[2]//2), wing_points)
               
    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                          self.radius * 2, self.radius * 2)

class Pipe:
    def __init__(self, x, gap_y, game_speed):
        self.x = x
        self.gap_y = gap_y
        self.gap_height = 150
        self.width = 80
        self.speed = 3 if game_speed == GameSpeed.NORMAL else 2 if game_speed == GameSpeed.EASY else 4
        self.passed = False
        self.color = random.choice([GREEN, BLUE, RED, PURPLE])
       
    def update(self):
        self.x -= self.speed
               
    def draw(self, screen):
        top_pipe_height = self.gap_y
        bottom_pipe_y = self.gap_y + self.gap_height
       
        top_rect = pygame.Rect(self.x, 0, self.width, top_pipe_height)
        pygame.draw.rect(screen, self.color, top_rect)
        pygame.draw.rect(screen, (self.color[0]//2, self.color[1]//2, self.color[2]//2),
                        top_rect, 3)
       
        cap_rect = pygame.Rect(self.x - 5, top_pipe_height - 20,
                              self.width + 10, 20)
        pygame.draw.rect(screen, (self.color[0]//2, self.color[1]//2, self.color[2]//2), cap_rect)
       
        bottom_rect = pygame.Rect(self.x, bottom_pipe_y,
                                 self.width, SCREEN_HEIGHT - bottom_pipe_y)
        pygame.draw.rect(screen, self.color, bottom_rect)
        pygame.draw.rect(screen, (self.color[0]//2, self.color[1]//2, self.color[2]//2),
                        bottom_rect, 3)
       
        cap_rect = pygame.Rect(self.x - 5, bottom_pipe_y,
                              self.width + 10, 20)
        pygame.draw.rect(screen, (self.color[0]//2, self.color[1]//2, self.color[2]//2), cap_rect)
   
    def get_top_rect(self):
        return pygame.Rect(self.x, 0, self.width, self.gap_y)
   
    def get_bottom_rect(self):
        return pygame.Rect(self.x, self.gap_y + self.gap_height,
                          self.width, SCREEN_HEIGHT)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flippy Bird")
        self.clock = pygame.time.Clock()
       
        self.state = GameState.MAIN_MENU
        self.game_speed = GameSpeed.NORMAL
       
        self.background = BackgroundRenderer()
        self.current_theme = BackgroundTheme.DAY
       
        self.trail_effect = TrailEffect.SPARKLE
       
        self.bird = None
        self.pipes = []
        self.pipe_timer = 0
        self.pipe_interval = 1500
       
        self.score = 0
        self.highscore = 0
        self.coins = 100
        self.explosion_particles = []
        self.game_over_alpha = 0
       
        self.create_ui_elements()
        self.load_data()
       
        self.current_bird_skin = BirdSkin.RED
        for skin in BirdSkin:
            if skin.value["name"] == self.saved_data.get("equipped_skin", "Classic Red"):
                self.current_bird_skin = skin
                break
               
        self.title_bounce = 0
        self.title_bounce_dir = 1
       
    def create_ui_elements(self):
        button_width, button_height = 200, 50
        center_x = SCREEN_WIDTH // 2 - button_width // 2
       
        self.play_button = Button(center_x, 200, button_width, button_height, "PLAY")
        self.modes_button = Button(center_x, 270, button_width, button_height, "MODES")
        self.highscore_button = Button(center_x, 340, button_width, button_height, "HIGHSCORE")
        self.settings_button = Button(center_x, 410, button_width, button_height, "SETTINGS")
        self.skin_button = Button(center_x, 480, button_width, button_height, "BIRD SKIN")
       
        self.background_button = Button(50, 500, 180, 60, "BACKGROUND")
        self.trail_button = Button(SCREEN_WIDTH - 230, 500, 180, 60, "TRAIL")
       
        self.speed_button = ToggleButton(center_x, 300, 250, 50, ["SPEED: EASY", "SPEED: NORMAL", "SPEED: HARD"])
        self.reset_score_button = Button(center_x, 380, 250, 50, "RESET HIGHSCORE", RED, (200, 50, 50))
       
        self.retry_button = Button(center_x, 400, button_width, button_height, "RETRY (R)", GREEN, (70, 200, 70))
        self.menu_button = Button(center_x, 480, button_width, button_height, "MENU (ESC)", BLUE, (70, 170, 255))
       
        self.day_button = Button(center_x, 200, 250, 80, "Day Mode ☀️", SKY_BLUE, (100, 200, 255))
        self.night_button = Button(center_x, 300, 250, 80, "Night Mode 🌙", NIGHT_BLUE, (50, 50, 150))
        self.storm_button = Button(center_x, 400, 250, 80, "Storm Mode ⛈", DARK_BLUE, (100, 100, 150))
       
        self.sparkle_button = Button(center_x, 200, 250, 80, "Sparkle ✨", PURPLE, (180, 70, 220))
        self.fire_button = Button(center_x, 300, 250, 80, "Fire 🔥", RED, (255, 100, 100))
        self.rainbow_button = Button(center_x, 400, 250, 80, "Rainbow 🌈", BLUE, (150, 150, 255))
       
        # MODE_SELECT ekranı için butonlar
        self.easy_mode_button = Button(center_x, 200, 250, 80, "EASY MODE", GREEN, (70, 200, 70))
        self.normal_mode_button = Button(center_x, 300, 250, 80, "NORMAL MODE", BLUE, (70, 170, 255))
        self.hard_mode_button = Button(center_x, 400, 250, 80, "HARD MODE", RED, (200, 50, 50))
       
    def load_data(self):
        self.saved_data = {
            "highscore": 0,
            "coins": 100,
            "unlocked_skins": ["Classic Red"],
            "equipped_skin": "Classic Red",
            "background_theme": "DAY",
            "trail_effect": "SPARKLE",
            "game_speed": "NORMAL"
        }
       
        try:
            if os.path.exists("flappy_bird_save.json"):
                with open("flappy_bird_save.json", "r") as f:
                    loaded_data = json.load(f)
                    self.saved_data.update(loaded_data)
        except:
            pass
           
        self.highscore = self.saved_data["highscore"]
        self.coins = self.saved_data["coins"]
       
        for skin in BirdSkin:
            if skin.value["name"] in self.saved_data["unlocked_skins"]:
                skin.value["unlocked"] = True
               
        theme_str = self.saved_data.get("background_theme", "DAY")
        if theme_str == "DAY":
            self.current_theme = BackgroundTheme.DAY
        elif theme_str == "NIGHT":
            self.current_theme = BackgroundTheme.NIGHT
        elif theme_str == "STORM":
            self.current_theme = BackgroundTheme.STORM
        self.background.set_theme(self.current_theme)
       
        trail_str = self.saved_data.get("trail_effect", "SPARKLE")
        if trail_str == "SPARKLE":
            self.trail_effect = TrailEffect.SPARKLE
        elif trail_str == "FIRE":
            self.trail_effect = TrailEffect.FIRE
        elif trail_str == "RAINBOW":
            self.trail_effect = TrailEffect.RAINBOW
           
        speed_str = self.saved_data.get("game_speed", "NORMAL")
        if speed_str == "EASY":
            self.game_speed = GameSpeed.EASY
            self.speed_button.current_index = 0
        elif speed_str == "NORMAL":
            self.game_speed = GameSpeed.NORMAL
            self.speed_button.current_index = 1
        elif speed_str == "HARD":
            self.game_speed = GameSpeed.HARD
            self.speed_button.current_index = 2
           
    def save_data(self):
        self.saved_data["highscore"] = self.highscore
        self.saved_data["coins"] = self.coins
        self.saved_data["equipped_skin"] = self.current_bird_skin.value["name"]
       
        unlocked_skins = []
        for skin in BirdSkin:
            if skin.value["unlocked"]:
                unlocked_skins.append(skin.value["name"])
        self.saved_data["unlocked_skins"] = unlocked_skins
       
        self.saved_data["background_theme"] = self.current_theme.name
        self.saved_data["trail_effect"] = self.trail_effect.name
        self.saved_data["game_speed"] = ["EASY", "NORMAL", "HARD"][self.speed_button.current_index]
       
        try:
            with open("flappy_bird_save.json", "w") as f:
                json.dump(self.saved_data, f)
        except:
            pass
           
    def reset_game(self):
        self.bird = Bird(SCREEN_WIDTH // 3, SCREEN_HEIGHT // 2, self.current_bird_skin)
        self.pipes = []
        self.pipe_timer = 0
        self.score = 0
        self.explosion_particles = []
        self.game_over_alpha = 0
       
    def create_explosion(self, x, y):
        for _ in range(30):
            self.explosion_particles.append(ExplosionParticle(x, y))
       
    def draw_background_theme_popup(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
       
        popup_width, popup_height = 600, 500
        popup_x, popup_y = SCREEN_WIDTH // 2 - popup_width // 2, SCREEN_HEIGHT // 2 - popup_height // 2
        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        pygame.draw.rect(self.screen, DARK_BLUE, popup_rect, border_radius=20)
        pygame.draw.rect(self.screen, WHITE, popup_rect, 3, border_radius=20)
       
        title_font = pygame.font.SysFont(None, 50)
        title_text = title_font.render("Background Theme", True, WHITE)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, popup_y + 30))
       
        self.day_button.draw(self.screen)
        self.night_button.draw(self.screen)
        self.storm_button.draw(self.screen)
       
        if self.current_theme == BackgroundTheme.DAY:
            pygame.draw.rect(self.screen, YELLOW, self.day_button.rect, 4, border_radius=15)
        elif self.current_theme == BackgroundTheme.NIGHT:
            pygame.draw.rect(self.screen, CYAN, self.night_button.rect, 4, border_radius=15)
        elif self.current_theme == BackgroundTheme.STORM:
            pygame.draw.rect(self.screen, YELLOW, self.storm_button.rect, 4, border_radius=15)
       
        esc_font = pygame.font.SysFont(None, 30)
        esc_text = esc_font.render("Press ESC to go back", True, LIGHT_GRAY)
        self.screen.blit(esc_text, (SCREEN_WIDTH // 2 - esc_text.get_width() // 2, popup_y + 450))
       
    def draw_trail_effect_popup(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
       
        popup_width, popup_height = 600, 500
        popup_x, popup_y = SCREEN_WIDTH // 2 - popup_width // 2, SCREEN_HEIGHT // 2 - popup_height // 2
        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        pygame.draw.rect(self.screen, DARK_BLUE, popup_rect, border_radius=20)
        pygame.draw.rect(self.screen, WHITE, popup_rect, 3, border_radius=20)
       
        title_font = pygame.font.SysFont(None, 50)
        title_text = title_font.render("Trail Effect", True, WHITE)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, popup_y + 30))
       
        self.sparkle_button.draw(self.screen)
        self.fire_button.draw(self.screen)
        self.rainbow_button.draw(self.screen)
       
        if self.trail_effect == TrailEffect.SPARKLE:
            pygame.draw.rect(self.screen, PURPLE, self.sparkle_button.rect, 4, border_radius=15)
        elif self.trail_effect == TrailEffect.FIRE:
            pygame.draw.rect(self.screen, RED, self.fire_button.rect, 4, border_radius=15)
        elif self.trail_effect == TrailEffect.RAINBOW:
            pygame.draw.rect(self.screen, CYAN, self.rainbow_button.rect, 4, border_radius=15)
       
        esc_font = pygame.font.SysFont(None, 30)
        esc_text = esc_font.render("Press ESC to go back", True, LIGHT_GRAY)
        self.screen.blit(esc_text, (SCREEN_WIDTH // 2 - esc_text.get_width() // 2, popup_y + 450))

    def draw_mode_select_popup(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
       
        popup_width, popup_height = 600, 500
        popup_x, popup_y = SCREEN_WIDTH // 2 - popup_width // 2, SCREEN_HEIGHT // 2 - popup_height // 2
        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        pygame.draw.rect(self.screen, DARK_BLUE, popup_rect, border_radius=20)
        pygame.draw.rect(self.screen, WHITE, popup_rect, 3, border_radius=20)
       
        title_font = pygame.font.SysFont(None, 50)
        title_text = title_font.render("Select Game Mode", True, WHITE)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, popup_y + 30))
       
        self.easy_mode_button.draw(self.screen)
        self.normal_mode_button.draw(self.screen)
        self.hard_mode_button.draw(self.screen)
       
        current_mode_color = YELLOW
        if self.game_speed == GameSpeed.EASY:
            pygame.draw.rect(self.screen, current_mode_color, self.easy_mode_button.rect, 4, border_radius=15)
        elif self.game_speed == GameSpeed.NORMAL:
            pygame.draw.rect(self.screen, current_mode_color, self.normal_mode_button.rect, 4, border_radius=15)
        elif self.game_speed == GameSpeed.HARD:
            pygame.draw.rect(self.screen, current_mode_color, self.hard_mode_button.rect, 4, border_radius=15)
       
        desc_font = pygame.font.SysFont(None, 24)
        easy_desc = desc_font.render("Pipe Speed: Slow, Gravity: Low", True, GREEN)
        normal_desc = desc_font.render("Pipe Speed: Normal, Gravity: Normal", True, BLUE)
        hard_desc = desc_font.render("Pipe Speed: Fast, Gravity: High", True, RED)
        
        self.screen.blit(easy_desc, (SCREEN_WIDTH // 2 - easy_desc.get_width() // 2, 320))
        self.screen.blit(normal_desc, (SCREEN_WIDTH // 2 - normal_desc.get_width() // 2, 380))
        self.screen.blit(hard_desc, (SCREEN_WIDTH // 2 - hard_desc.get_width() // 2, 440))
       
        esc_font = pygame.font.SysFont(None, 30)
        esc_text = esc_font.render("Press ESC to go back", True, LIGHT_GRAY)
        self.screen.blit(esc_text, (SCREEN_WIDTH // 2 - esc_text.get_width() // 2, popup_y + 450))
       
    def draw_skin_selector_popup(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
       
        popup_width, popup_height = 700, 550
        popup_x, popup_y = SCREEN_WIDTH // 2 - popup_width // 2, SCREEN_HEIGHT // 2 - popup_height // 2
        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        pygame.draw.rect(self.screen, DARK_BLUE, popup_rect, border_radius=20)
        pygame.draw.rect(self.screen, WHITE, popup_rect, 3, border_radius=20)
       
        title_font = pygame.font.SysFont(None, 50)
        title_text = title_font.render("Select Bird Skin", True, WHITE)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, popup_y + 30))
       
        coin_font = pygame.font.SysFont(None, 35)
        coin_text = coin_font.render(f"Coins: {self.coins}", True, GOLD)
        self.screen.blit(coin_text, (popup_x + popup_width - coin_text.get_width() - 30, popup_y + 30))
       
        skin_list = list(BirdSkin)
        categories = {}
        for skin in skin_list:
            category = skin.value["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(skin)
       
        y_offset = popup_y + 90
        for category, skins in categories.items():
            cat_font = pygame.font.SysFont(None, 28)
            cat_color = CYAN if category == "Special" else GOLD if category == "Premium" else GREEN
            cat_text = cat_font.render(f"{category} Skins", True, cat_color)
            self.screen.blit(cat_text, (popup_x + 30, y_offset))
            y_offset += 35
           
            for i, skin in enumerate(skins):
                row = i // 3
                col = i % 3
               
                card_x = popup_x + 30 + col * 200
                card_y = y_offset + row * 140
               
                card_radius = 50
                card_center = (card_x + 70, card_y + 70)
               
                if skin == self.current_bird_skin:
                    for r in range(card_radius, card_radius + 8):
                        pygame.draw.circle(self.screen, GOLD, card_center, r, 2)
                    pygame.draw.circle(self.screen, DARK_GRAY, card_center, card_radius)
                elif skin.value["unlocked"]:
                    pygame.draw.circle(self.screen, GREEN, card_center, card_radius + 4, 3)
                    pygame.draw.circle(self.screen, DARK_GRAY, card_center, card_radius)
                else:
                    pygame.draw.circle(self.screen, GRAY, card_center, card_radius + 4, 3)
                    pygame.draw.circle(self.screen, DARK_GRAY, card_center, card_radius)
                   
                    lock_surf = pygame.Surface((card_radius * 2, card_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(lock_surf, (0, 0, 0, 150), (card_radius, card_radius), card_radius)
                    self.screen.blit(lock_surf, (card_x + 20, card_y + 20))
                   
                    lock_font = pygame.font.SysFont(None, 40)
                    lock_text = lock_font.render("🔒", True, WHITE)
                    self.screen.blit(lock_text, (card_x + 55, card_y + 55))
               
                self.draw_bird_preview(skin, card_center[0], card_center[1], 30)
               
                name_font = pygame.font.SysFont(None, 18)
                name_text = name_font.render(skin.value["name"], True, WHITE)
                self.screen.blit(name_text, (card_x + 70 - name_text.get_width() // 2, card_y + 110))
               
                status_font = pygame.font.SysFont(None, 16)
                if skin.value["unlocked"]:
                    if skin == self.current_bird_skin:
                        status_text = status_font.render("EQUIPPED", True, GREEN)
                    else:
                        status_text = status_font.render("OWNED", True, CYAN)
                else:
                    status_text = status_font.render(f"{skin.value['price']} coins", True, YELLOW)
                self.screen.blit(status_text, (card_x + 70 - status_text.get_width() // 2, card_y + 125))
           
            y_offset += (len(skins) // 3 + 1) * 140
           
            if list(categories.keys()).index(category) < len(categories) - 1:
                pygame.draw.line(self.screen, GRAY,
                               (popup_x + 30, y_offset - 20),
                               (popup_x + popup_width - 30, y_offset - 20), 2)
       
        esc_font = pygame.font.SysFont(None, 30)
        esc_text = esc_font.render("Press ESC to go back", True, LIGHT_GRAY)
        self.screen.blit(esc_text, (SCREEN_WIDTH // 2 - esc_text.get_width() // 2, popup_y + 520))
       
    def draw_bird_preview(self, skin, x, y, size):
        flap_offset = math.sin(pygame.time.get_ticks() * 0.005) * 3
        color = skin.value["color"]
       
        pygame.draw.circle(self.screen, color, (int(x), int(y)), size)
        pygame.draw.circle(self.screen, WHITE, (int(x + size * 0.4), int(y - size * 0.3)), int(size * 0.3))
        pygame.draw.circle(self.screen, BLACK, (int(x + size * 0.4), int(y - size * 0.3)), int(size * 0.15))
       
        wing_points = [
            (x - size * 0.5, y),
            (x - size * 0.7, y + size * 0.5 + flap_offset),
            (x, y + size * 0.3)
        ]
        wing_color = (color[0]//2, color[1]//2, color[2]//2)
        pygame.draw.polygon(self.screen, wing_color, wing_points)
       
        beak_points = [
            (x + size * 0.8, y),
            (x + size * 1.2, y),
            (x + size * 0.8, y + size * 0.4)
        ]
        pygame.draw.polygon(self.screen, ORANGE, beak_points)
       
    def draw_main_menu(self):
        self.background.draw(self.screen)
        self.background.update()
       
        self.title_bounce += 0.1 * self.title_bounce_dir
        if self.title_bounce > 5 or self.title_bounce < -5:
            self.title_bounce_dir *= -1
           
        title_font = pygame.font.SysFont(None, 80)
        title_text = title_font.render("FLIPPY BIRD", True, WHITE)
        title_shadow = title_font.render("FLIPPY BIRD", True, (50, 50, 50, 150))
       
        title_x = SCREEN_WIDTH // 2
        title_y = 100 + self.title_bounce
       
        self.screen.blit(title_shadow, (title_x - title_shadow.get_width()//2 + 3,
                                       title_y - title_shadow.get_height()//2 + 3))
        self.screen.blit(title_text, (title_x - title_text.get_width()//2,
                                     title_y - title_text.get_height()//2))
       
        self.play_button.draw(self.screen)
        self.modes_button.draw(self.screen)
        self.highscore_button.draw(self.screen)
        self.settings_button.draw(self.screen)
        self.skin_button.draw(self.screen)
       
        self.background_button.draw(self.screen)
        self.trail_button.draw(self.screen)
       
        version_font = pygame.font.SysFont(None, 24)
        version_text = version_font.render("v1.0", True, WHITE)
        self.screen.blit(version_text, (10, SCREEN_HEIGHT - 30))
       
        highscore_font = pygame.font.SysFont(None, 30)
        highscore_text = highscore_font.render(f"Highscore: {self.highscore}", True, YELLOW)
        self.screen.blit(highscore_text, (SCREEN_WIDTH - highscore_text.get_width() - 10, 10))
       
        coins_font = pygame.font.SysFont(None, 30)
        coins_text = coins_font.render(f"Coins: {self.coins}", True, GOLD)
        self.screen.blit(coins_text, (10, 10))
       
    def draw_game(self):
        self.background.draw(self.screen)
        self.background.update()
       
        for particle in self.explosion_particles[:]:
            particle.update()
            particle.draw(self.screen)
            if not particle.is_alive():
                self.explosion_particles.remove(particle)
           
        for pipe in self.pipes:
            pipe.draw(self.screen)
           
        if self.bird:
            self.bird.draw(self.screen)
           
        score_font = pygame.font.SysFont(None, 50)
        score_text = score_font.render(f"{self.score}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 30))
       
        coin_font = pygame.font.SysFont(None, 30)
        coin_text = coin_font.render(f"Coins: {self.coins}", True, GOLD)
        self.screen.blit(coin_text, (10, 70))
       
    def draw_game_over(self):
        self.draw_game()
       
        if self.game_over_alpha < 180:
            self.game_over_alpha += 5
       
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(self.game_over_alpha)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
       
        title_font = pygame.font.SysFont(None, 80)
        title_text = title_font.render("GAME OVER", True, RED)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150))
       
        score_font = pygame.font.SysFont(None, 50)
        score_text = score_font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 250))
       
        highscore_text = score_font.render(f"Highscore: {self.highscore}", True, YELLOW)
        self.screen.blit(highscore_text, (SCREEN_WIDTH // 2 - highscore_text.get_width() // 2, 320))
       
        if self.score > self.highscore:
            new_record_font = pygame.font.SysFont(None, 40)
            new_record_text = new_record_font.render("NEW RECORD!", True, GOLD)
            self.screen.blit(new_record_text, (SCREEN_WIDTH // 2 - new_record_text.get_width() // 2, 380))
       
        self.retry_button.draw(self.screen)
        self.menu_button.draw(self.screen)
       
        controls_font = pygame.font.SysFont(None, 25)
        controls_text = controls_font.render("Press R to retry or ESC for menu", True, LIGHT_GRAY)
        self.screen.blit(controls_text, (SCREEN_WIDTH // 2 - controls_text.get_width() // 2, 500))
       
    def draw_settings(self):
        self.background.draw(self.screen)
       
        title_font = pygame.font.SysFont(None, 60)
        title_text = title_font.render("SETTINGS", True, WHITE)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100))
       
        speed_font = pygame.font.SysFont(None, 40)
        speed_label = speed_font.render("Game Speed:", True, WHITE)
        self.screen.blit(speed_label, (SCREEN_WIDTH // 2 - 300, 200))
       
        self.speed_button.draw(self.screen)
       
        self.reset_score_button.draw(self.screen)
       
        esc_font = pygame.font.SysFont(None, 30)
        esc_text = esc_font.render("Press ESC to go back", True, LIGHT_GRAY)
        self.screen.blit(esc_text, (SCREEN_WIDTH // 2 - esc_text.get_width() // 2, 500))
       
    def draw_highscore(self):
        self.background.draw(self.screen)
       
        title_font = pygame.font.SysFont(None, 60)
        title_text = title_font.render("HIGHSCORE", True, WHITE)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
       
        score_font = pygame.font.SysFont(None, 80)
        score_text = score_font.render(f"{self.highscore}", True, GOLD)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 200))
       
        esc_font = pygame.font.SysFont(None, 30)
        esc_text = esc_font.render("Press ESC to go back", True, LIGHT_GRAY)
        self.screen.blit(esc_text, (SCREEN_WIDTH // 2 - esc_text.get_width() // 2, 500))
       
    def spawn_pipe(self):
        gap_y = random.randint(100, SCREEN_HEIGHT - 200)
        pipe = Pipe(SCREEN_WIDTH, gap_y, self.game_speed)
        self.pipes.append(pipe)
       
    def handle_skin_card_click(self, mouse_pos):
        popup_width, popup_height = 700, 550
        popup_x, popup_y = SCREEN_WIDTH // 2 - popup_width // 2, SCREEN_HEIGHT // 2 - popup_height // 2
       
        skin_list = list(BirdSkin)
        categories = {}
        for skin in skin_list:
            category = skin.value["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(skin)
       
        y_offset = popup_y + 90
        for category, skins in categories.items():
            y_offset += 35
           
            for i, skin in enumerate(skins):
                row = i // 3
                col = i % 3
               
                card_x = popup_x + 30 + col * 200
                card_y = y_offset + row * 140
               
                card_center = (card_x + 70, card_y + 70)
                distance = math.sqrt((mouse_pos[0] - card_center[0])**2 + (mouse_pos[1] - card_center[1])**2)
               
                if distance < 50:
                    if skin.value["unlocked"]:
                        self.current_bird_skin = skin
                        if self.bird:
                            self.bird.skin = skin
                    else:
                        if self.coins >= skin.value["price"]:
                            self.coins -= skin.value["price"]
                            skin.value["unlocked"] = True
                            self.current_bird_skin = skin
                            if self.bird:
                                self.bird.skin = skin
                    return
                   
            y_offset += (len(skins) // 3 + 1) * 140
           
    def run(self):
        running = True
        mouse_click = False
       
        while running:
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = False
           
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    self.save_data()
                   
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state in [GameState.BACKGROUND_THEME, GameState.TRAIL_EFFECT,
                                        GameState.SKIN_SELECTOR, GameState.SETTINGS,
                                        GameState.HIGHSCORE, GameState.MODE_SELECT]:
                            self.state = GameState.MAIN_MENU
                            self.save_data()
                        elif self.state == GameState.GAME_OVER:
                            self.state = GameState.MAIN_MENU
                            self.save_data()
                           
                    if self.state == GameState.PLAYING:
                        if event.key == pygame.K_SPACE:
                            if self.bird and self.bird.alive:
                                self.bird.jump()
                    elif self.state == GameState.GAME_OVER:
                        if event.key == pygame.K_r:
                            self.state = GameState.PLAYING
                            self.reset_game()
                    elif self.state == GameState.MAIN_MENU:
                        if event.key == pygame.K_RETURN:
                            self.state = GameState.PLAYING
                            self.reset_game()
                           
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_click = True
                   
                    if self.state == GameState.PLAYING:
                        if self.bird and self.bird.alive:
                            self.bird.jump()
                           
            if self.state == GameState.MAIN_MENU:
                self.play_button.update(mouse_pos)
                self.modes_button.update(mouse_pos)
                self.highscore_button.update(mouse_pos)
                self.settings_button.update(mouse_pos)
                self.skin_button.update(mouse_pos)
                self.background_button.update(mouse_pos)
                self.trail_button.update(mouse_pos)
               
                if mouse_click:
                    if self.play_button.is_clicked(mouse_pos, True):
                        self.state = GameState.PLAYING
                        self.reset_game()
                    elif self.modes_button.is_clicked(mouse_pos, True):
                        self.state = GameState.MODE_SELECT
                    elif self.highscore_button.is_clicked(mouse_pos, True):
                        self.state = GameState.HIGHSCORE
                    elif self.settings_button.is_clicked(mouse_pos, True):
                        self.state = GameState.SETTINGS
                    elif self.skin_button.is_clicked(mouse_pos, True):
                        self.state = GameState.SKIN_SELECTOR
                    elif self.background_button.is_clicked(mouse_pos, True):
                        self.state = GameState.BACKGROUND_THEME
                    elif self.trail_button.is_clicked(mouse_pos, True):
                        self.state = GameState.TRAIL_EFFECT
                       
            elif self.state == GameState.BACKGROUND_THEME:
                self.day_button.update(mouse_pos)
                self.night_button.update(mouse_pos)
                self.storm_button.update(mouse_pos)
               
                if mouse_click:
                    if self.day_button.is_clicked(mouse_pos, True):
                        self.current_theme = BackgroundTheme.DAY
                        self.background.set_theme(self.current_theme)
                    elif self.night_button.is_clicked(mouse_pos, True):
                        self.current_theme = BackgroundTheme.NIGHT
                        self.background.set_theme(self.current_theme)
                    elif self.storm_button.is_clicked(mouse_pos, True):
                        self.current_theme = BackgroundTheme.STORM
                        self.background.set_theme(self.current_theme)
                       
            elif self.state == GameState.TRAIL_EFFECT:
                self.sparkle_button.update(mouse_pos)
                self.fire_button.update(mouse_pos)
                self.rainbow_button.update(mouse_pos)
               
                if mouse_click:
                    if self.sparkle_button.is_clicked(mouse_pos, True):
                        self.trail_effect = TrailEffect.SPARKLE
                    elif self.fire_button.is_clicked(mouse_pos, True):
                        self.trail_effect = TrailEffect.FIRE
                    elif self.rainbow_button.is_clicked(mouse_pos, True):
                        self.trail_effect = TrailEffect.RAINBOW
                       
            elif self.state == GameState.MODE_SELECT:
                self.easy_mode_button.update(mouse_pos)
                self.normal_mode_button.update(mouse_pos)
                self.hard_mode_button.update(mouse_pos)
               
                if mouse_click:
                    if self.easy_mode_button.is_clicked(mouse_pos, True):
                        self.game_speed = GameSpeed.EASY
                        self.speed_button.current_index = 0
                        self.state = GameState.MAIN_MENU
                        self.save_data()
                    elif self.normal_mode_button.is_clicked(mouse_pos, True):
                        self.game_speed = GameSpeed.NORMAL
                        self.speed_button.current_index = 1
                        self.state = GameState.MAIN_MENU
                        self.save_data()
                    elif self.hard_mode_button.is_clicked(mouse_pos, True):
                        self.game_speed = GameSpeed.HARD
                        self.speed_button.current_index = 2
                        self.state = GameState.MAIN_MENU
                        self.save_data()
                       
            elif self.state == GameState.SKIN_SELECTOR:
                if mouse_click:
                    self.handle_skin_card_click(mouse_pos)
                   
            elif self.state == GameState.SETTINGS:
                self.speed_button.update(mouse_pos, mouse_click)
                self.reset_score_button.update(mouse_pos)
               
                if mouse_click:
                    if self.speed_button.update(mouse_pos, mouse_click):
                        if self.speed_button.current_index == 0:
                            self.game_speed = GameSpeed.EASY
                        elif self.speed_button.current_index == 1:
                            self.game_speed = GameSpeed.NORMAL
                        else:
                            self.game_speed = GameSpeed.HARD
                   
                    if self.reset_score_button.is_clicked(mouse_pos, True):
                        self.highscore = 0
                           
            elif self.state == GameState.PLAYING:
                if self.bird and self.bird.alive:
                    self.bird.update()
                   
                    current_time = pygame.time.get_ticks()
                    if current_time - self.pipe_timer > self.pipe_interval:
                        self.spawn_pipe()
                        self.pipe_timer = current_time
                       
                    pipes_to_remove = []
                    for pipe in self.pipes:
                        pipe.update()
                       
                        if pipe.x < -pipe.width:
                            pipes_to_remove.append(pipe)
                           
                        if not pipe.passed and pipe.x < self.bird.x:
                            pipe.passed = True
                            self.score += 1
                            self.coins += 1
                           
                        if (self.bird.get_rect().colliderect(pipe.get_top_rect()) or
                            self.bird.get_rect().colliderect(pipe.get_bottom_rect())):
                            self.create_explosion(self.bird.x, self.bird.y)
                            self.bird.alive = False
                               
                    for pipe in pipes_to_remove:
                        self.pipes.remove(pipe)
                           
                    if self.bird.y > SCREEN_HEIGHT - 100 - self.bird.radius:
                        self.create_explosion(self.bird.x, self.bird.y)
                        self.bird.alive = False
                           
                    if not self.bird.alive:
                        if self.score > self.highscore:
                            self.highscore = self.score
                        self.state = GameState.GAME_OVER
                       
            elif self.state == GameState.GAME_OVER:
                self.retry_button.update(mouse_pos)
                self.menu_button.update(mouse_pos)
               
                if mouse_click:
                    if self.retry_button.is_clicked(mouse_pos, True):
                        self.state = GameState.PLAYING
                        self.reset_game()
                    elif self.menu_button.is_clicked(mouse_pos, True):
                        self.state = GameState.MAIN_MENU
                        self.save_data()
                       
            if self.state == GameState.MAIN_MENU:
                self.draw_main_menu()
            elif self.state == GameState.BACKGROUND_THEME:
                self.draw_background_theme_popup()
            elif self.state == GameState.TRAIL_EFFECT:
                self.draw_trail_effect_popup()
            elif self.state == GameState.MODE_SELECT:
                self.draw_mode_select_popup()
            elif self.state == GameState.SKIN_SELECTOR:
                self.draw_skin_selector_popup()
            elif self.state == GameState.PLAYING:
                self.draw_game()
            elif self.state == GameState.GAME_OVER:
                self.draw_game_over()
            elif self.state == GameState.SETTINGS:
                self.draw_settings()
            elif self.state == GameState.HIGHSCORE:
                self.draw_highscore()
               
            pygame.display.flip()
            self.clock.tick(FPS)
           
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()