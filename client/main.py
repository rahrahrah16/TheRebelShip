"""Pygame client: input, drawing and the main game loop."""
from __future__ import annotations

import math
import random
import sys
import pygame

from game.model import Game, RESOURCES, DRONE_COST, UPGRADES

NAVY = (7, 15, 27)
PANEL = (13, 27, 43)
LINE = (39, 62, 81)
TEXT = (218, 233, 244)
MUTED = (116, 146, 166)
CYAN = (75, 220, 238)
COLORS = {"Iron": (123, 172, 194), "Copper": (236, 148, 91), "Crystal": (135, 228, 218), "Power": (240, 190, 77)}


class Client:
    """Owns the pygame window and translates input into game actions."""
    def __init__(self) -> None:
        pygame.init()
        info = pygame.display.Info()
        self.windowed = (max(1280, min(1600, info.current_w - 80)), max(720, min(900, info.current_h - 100)))
        self.fullscreen = False
        self.screen = pygame.display.set_mode(self.windowed, pygame.RESIZABLE)
        pygame.display.set_caption("The Rebel Ship")
        self.clock = pygame.time.Clock()
        self.game = Game(*self.screen.get_size())
        self.fonts = {size: pygame.font.SysFont("dejavusansmono", size) for size in (12, 14, 16, 20, 26, 36, 48)}
        rng = random.Random(2401)
        self.stars = [(rng.random(), rng.random(), rng.choice((1, 1, 1, 2))) for _ in range(120)]
        self.tab = "Overview"
        self.selected = 0
        self.buttons: list[tuple[pygame.Rect, str]] = []
        self.running = True

    def text(self, value: str, x: int, y: int, size: int = 14, color: tuple[int, int, int] = TEXT) -> None:
        """Draw one line of text at the given screen position."""
        self.screen.blit(self.fonts[size].render(value, True, color), (int(x), int(y)))

    def button(self, label: str, rect: pygame.Rect, active: bool = False) -> None:
        """Draw one interface button with a simple highlighted state."""
        fill = (18, 50, 67) if active else PANEL
        pygame.draw.rect(self.screen, fill, rect, border_radius=5)
        pygame.draw.rect(self.screen, CYAN if active else LINE, rect, 1, border_radius=5)
        surf = self.fonts[14].render(label, True, CYAN if active else TEXT)
        self.screen.blit(surf, surf.get_rect(center=rect.center))
        self.buttons.append((rect, label))

    def handle_click(self, pos: tuple[int, int]) -> None:
        """Handle a click on the menu, game, or Control Center."""
        g = self.game
        if g.state == "menu":
            g.start_game()
            g.state = "play"
            return
        if g.state in ("lost", "won"):
            g.start_game()
            g.state = "play"
            return
        if g.state == "play":
            g.shoot(*pos)
            return
        if g.state != "control":
            return

        # Tab buttons are in the same place on every Control Center page.
        for i, tab_name in enumerate(("Overview", "Fleet", "Tech Lab")):
            if pygame.Rect(42 + i * 155, 100, 145, 40).collidepoint(pos):
                self.tab = tab_name
                return

        # Fleet page: choose a helper and give it one of the simple orders.
        if self.tab == "Fleet":
            if pygame.Rect(42, 220, 210, 40).collidepoint(pos):
                g.build_drone()
                return
            if pygame.Rect(264, 220, 155, 40).collidepoint(pos):
                g.recall_drones()
                return
            for i in range(len(g.drones)):
                column = i // 6
                row = i % 6
                if pygame.Rect(42 + column * 270, 305 + row * 47, 250, 39).collidepoint(pos):
                    self.selected = i
                    return
            for i, order in enumerate(("Mining", "Attacking", "Follow")):
                if pygame.Rect(self.screen.get_width()//2+35+i*194, 330, 180, 46).collidepoint(pos):
                    g.assign_drone(self.selected, order)
                    return

        # Tech Lab page: each row purchases its matching upgrade.
        if self.tab == "Tech Lab":
            for i, name in enumerate(UPGRADES):
                if pygame.Rect(min(590, self.screen.get_width()-180), 277+i*96, 105, 38).collidepoint(pos):
                    g.upgrade(name)
                    return

    def events(self) -> None:
        """Read pygame events and handle menu, keys, resizing and mouse clicks."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                self.screen = pygame.display.set_mode((max(800, event.w), max(600, event.h)), pygame.RESIZABLE)
                self.game.resize(*self.screen.get_size())
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.running = False
                elif event.key == pygame.K_F11:
                    self.fullscreen = not self.fullscreen
                    if self.fullscreen: self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else: self.screen = pygame.display.set_mode(self.windowed, pygame.RESIZABLE)
                    self.game.resize(*self.screen.get_size())
                elif event.key == pygame.K_RETURN and self.game.state == "menu": self.game.start_game(); self.game.state = "play"
                elif event.key == pygame.K_r and self.game.state in ("won", "lost"): self.game.start_game(); self.game.state = "play"
                elif event.key == pygame.K_p and self.game.state == "play": self.game.state = "paused"
                elif event.key == pygame.K_p and self.game.state == "paused": self.game.state = "play"
                elif event.key == pygame.K_SPACE and self.game.state == "play": self.game.state = "control"
                elif event.key == pygame.K_SPACE and self.game.state == "control": self.game.state = "play"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.game.state == "control": self.handle_click(event.pos)
                elif self.game.state == "play": self.game.shoot(*event.pos)

    def draw_world(self) -> None:
        """Draw the star field, ships, rocks, resource HUD and radar."""
        g = self.game
        self.screen.fill(NAVY)
        w, h = self.screen.get_size()
        for x, y, r in self.stars:
            pygame.draw.circle(self.screen, (44, 67, 86), (int(x * w), int(y * h)), r)
        # Header and ordered resource strip follow the concept sketch.
        self.text("THE REBEL SHIP", 28, 19, 20)
        pygame.draw.line(self.screen, LINE, (28, 50), (w - 28, 50))
        labels = RESOURCES
        width = min(150, (w - 56) // 4)
        for i, name in enumerate(labels):
            x = 28 + i * width
            pygame.draw.rect(self.screen, PANEL, (x, 62, width - 8, 54), border_radius=3)
            pygame.draw.rect(self.screen, LINE, (x, 62, width - 8, 54), 1, border_radius=3)
            pygame.draw.circle(self.screen, COLORS[name], (x + 18, 89), 7)
            self.text(f"{g.resources[name]:03d}", x + 32, 68, 20)
            self.text(name.upper(), x + 32, 91, 12, MUTED)
        self.text(f"SECTOR {int(g.elapsed // 30) + 1:02d}  /  {g.state.upper()}", w - 235, 22, 12, MUTED)
        for a in g.asteroids: self.draw_asteroid(a)
        # Mining beam is visible whenever a miner is near its assigned rock.
        for drone in g.drones:
            if drone.order == "Mining" and g.asteroids:
                rock = min(g.asteroids, key=lambda a: math.dist((drone.x, drone.y), (a.x, a.y)))
                if rock and math.dist((drone.x, drone.y), (rock.x, rock.y)) < rock.radius + 100:
                    pygame.draw.line(self.screen, (68, 191, 203), (drone.x, drone.y), (rock.x, rock.y), 1)
        for bullet in g.bullets:
            pygame.draw.circle(self.screen, CYAN if bullet.owner == "player" else (255, 91, 116), (int(bullet.x), int(bullet.y)), 4)
        for enemy in g.enemies: self.draw_ship(enemy.x, enemy.y, (255, 93, 116), 13, direction=(g.player_x-enemy.x, g.player_y-enemy.y))
        if g.boss: self.draw_ship(g.boss_x, g.boss_y, (229, 83, 111), 34, (g.boss.health, 550))
        for drone in g.drones: self.draw_ship(drone.x, drone.y, (63, 194, 207), 8)
        self.draw_ship(g.player_x, g.player_y, CYAN, 17)
        # Compact radar and status keep the play area open.
        rx, ry = 28, h - 155
        pygame.draw.rect(self.screen, PANEL, (rx, ry, 205, 125))
        pygame.draw.rect(self.screen, LINE, (rx, ry, 205, 125), 1)
        self.text("RADAR", rx + 9, ry + 6, 12, MUTED)
        for a in g.asteroids: pygame.draw.circle(self.screen, COLORS[a.resource], (rx + 102 + int((a.x-g.player_x)*.035), ry+64+int((a.y-g.player_y)*.035)), 2)
        for e in g.enemies: pygame.draw.circle(self.screen, (255, 88, 111), (rx+102+int((e.x-g.player_x)*.035), ry+64+int((e.y-g.player_y)*.035)), 3)
        pygame.draw.polygon(self.screen, CYAN, [(rx+102, ry+57),(rx+109,ry+73),(rx+102,ry+69),(rx+95,ry+73)])
        pygame.draw.rect(self.screen, (26, 42, 58), (w - 230, h - 38, 185, 8))
        pygame.draw.rect(self.screen, CYAN, (w - 230, h - 38, int(185*g.health/max(1,g.max_health)), 8))
        self.text(f"HULL {int(g.health):03d}%", w - 230, h - 59, 12, MUTED)
        self.text("SPACE  CONTROL CENTER", w//2-105, h-40, 14, MUTED)
        if g.boss:
            self.text("RIVAL COMMANDER", w-240, 130, 12, (255, 114, 132))
            pygame.draw.rect(self.screen, (49, 25, 42), (w-240, 151, 200, 7))
            pygame.draw.rect(self.screen, (235, 82, 112), (w-240, 151, int(200*g.boss.health/550), 7))
        if g.notice_wait > 0: self.text(g.notice, w//2-90, 70, 16, CYAN)

    def draw_asteroid(self, a) -> None:
        # Faceted irregular rock silhouette; no circles or floating resource numbers.
        points = []
        for i in range(10):
            angle = i * math.tau / 10
            radius = a.radius * (.78 + ((a.seed >> (i % 16)) & 7) / 35)
            points.append((a.x + math.cos(angle)*radius, a.y + math.sin(angle)*radius))
        pygame.draw.polygon(self.screen, (40, 59, 73), points)
        pygame.draw.polygon(self.screen, (92, 122, 138), points, 1)
        pygame.draw.line(self.screen, (62, 84, 101), points[1], points[4], 1)
        pygame.draw.line(self.screen, (62, 84, 101), points[5], points[8], 1)

    def draw_ship(self, x: float, y: float, color, size: int, hp=None, direction=(1, 0)) -> None:
        """Draw a simple triangular ship and, when supplied, its health bar."""
        angle = math.atan2(direction[1], direction[0])
        pts = []
        for degrees, scale in ((0, 1.25), (145, .8), (180, .38), (215, .8)):
            a = angle + math.radians(degrees)
            pts.append((x + math.cos(a)*size*scale, y + math.sin(a)*size*scale))
        pygame.draw.polygon(self.screen, color, pts)
        pygame.draw.polygon(self.screen, (183, 238, 245), pts, 1)
        if hp:
            value, maximum = hp
            pygame.draw.rect(self.screen, (45, 32, 44), (x-size, y-size-10, size*2, 3))
            pygame.draw.rect(self.screen, color, (x-size, y-size-10, size*2*max(0,value)/maximum, 3))

    def draw_control(self) -> None:
        """Draw the Control Center over the game without opening a new window."""
        g = self.game; w, h = self.screen.get_size()
        shade = pygame.Surface((w, h), pygame.SRCALPHA); shade.fill((3, 8, 16, 225)); self.screen.blit(shade, (0, 0))
        self.text("THE REBEL SHIP", 40, 24, 26)
        self.text("COMMAND INTERFACE / SECTOR 01", 42, 56, 12, MUTED)
        for i, name in enumerate(("Overview", "Fleet", "Tech Lab")):
            self.button(name.upper(), pygame.Rect(42+i*155, 100, 145, 40), self.tab == name)
        pygame.draw.line(self.screen, LINE, (40, 154), (w-40, 154))
        if self.tab == "Overview":
            self.text("FLEET DEVELOPMENT", 50, 185, 26)
            self.text("Mine asteroids, build helper ships and keep ahead of the rival faction.", 52, 226, 16, MUTED)
            self.text(f"ACTIVE DRONES  {len(g.drones)} / {6 + g.upgrades["Drone capacity"] * 2}", 52, 292, 20, CYAN)
            self.text(f"RIVAL THREAT  LEVEL {g.boss_level}   •   {len(g.enemies)} hostile ships", 52, 340, 16, (244, 132, 147))
            self.text("The commander is expected after 01:45. Prepare your fleet before engaging.", 52, 390, 14, MUTED)
            self.text("Controls: WASD / arrows move  •  J / click fire  •  P pause  •  F11 fullscreen", 52, h-105, 14, MUTED)
        elif self.tab == "Fleet":
            self.text("DRONE COMMAND", 50, 177, 26)
            self.text(f"ACTIVE DRONES  {len(g.drones)} / {6 + g.upgrades["Drone capacity"] * 2}", w-280, 186, 16, CYAN)
            self.button("BUILD HELPER SHIP", pygame.Rect(42, 220, 210, 40))
            self.button("RECALL ALL", pygame.Rect(264, 220, 155, 40))
            self.text("YOUR FLEET", 48, 278, 14, MUTED)
            for i, drone in enumerate(g.drones[:12]):
                # Two short columns keep every helper visible without scrolling.
                column = i // 6
                row = i % 6
                x, y = 42 + column * 270, 305 + row * 47
                rect = pygame.Rect(x, y, 250, 39)
                pygame.draw.rect(self.screen, (18, 45, 60) if i == self.selected else PANEL, rect, border_radius=4)
                pygame.draw.rect(self.screen, CYAN if i == self.selected else LINE, rect, 1, border_radius=4)
                self.text(f"DR-{i+1:02d}     {drone.order.upper():10s}     HULL {int(drone.health)}%", rect.x+12, y+11, 14)
            self.text("ASSIGN BEHAVIOUR", w//2+35, 280, 16)
            for i, (label, mode) in enumerate((("MINING ASTEROIDS", "Mining"), ("ATTACK ENEMIES", "Attacking"), ("FOLLOW SHIP", "Follow"))):
                self.button(label, pygame.Rect(w//2+35+i*194, 330, 180, 46), bool(g.drones and g.drones[min(self.selected,len(g.drones)-1)].order == mode))
            self.text("Selected helper returns to following you when recalled.", w//2+38, 395, 13, MUTED)
            self.text("Cost: 34 Iron  •  24 Copper  •  15 Crystal  •  18 Power", 48, h-95, 14, MUTED)
        else:
            self.text("TECH LAB", 50, 178, 26)
            self.text("Research improves your ship and helper fleet. Each level costs more.", 52, 219, 15, MUTED)
            for i, name in enumerate(UPGRADES):
                y = 260 + i*96
                pygame.draw.rect(self.screen, PANEL, (80, y, min(640,w-160), 72), border_radius=5)
                pygame.draw.rect(self.screen, LINE, (80, y, min(640,w-160), 72), 1, border_radius=5)
                self.text(name.upper(), 98, y+12, 16)
                self.text(f"LEVEL {g.upgrades[name]} / 5   •   {20*(1+g.upgrades[name])} IRON  {14*(1+g.upgrades[name])} COPPER  {10*(1+g.upgrades[name])} CRYSTAL  {8*(1+g.upgrades[name])} POWER", 98, y+39, 12, MUTED)
                self.button("UPGRADE", pygame.Rect(min(590,w-180), y+17, 105, 38))
        self.text("SPACE / ESC  CLOSE MENU", 42, h-38, 13, MUTED)
        self.buttons = [(pygame.Rect(42+i*155,100,145,40), n) for i,n in enumerate(("Overview","Fleet","Tech Lab"))]

    def run(self) -> None:
        """Run the repeated input, rules and drawing steps at about 60 FPS."""
        while self.running:
            dt = self.clock.tick(60) / 1000
            self.events()
            g = self.game
            if g.state == "play":
                # Convert held movement keys into horizontal and vertical input.
                keys = pygame.key.get_pressed()
                dx = float(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - float(keys[pygame.K_a] or keys[pygame.K_LEFT])
                dy = float(keys[pygame.K_s] or keys[pygame.K_DOWN]) - float(keys[pygame.K_w] or keys[pygame.K_UP])
                g.move_player(dx, dy, dt)
                # J fires toward the mouse pointer while the key is held.
                if keys[pygame.K_j]: g.shoot(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])
                g.update(dt)
            # Draw the common game view first, then draw a menu on top if needed.
            self.draw_world()
            if g.state == "menu":
                veil = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA); veil.fill((4,10,18,220)); self.screen.blit(veil,(0,0))
                w,h=self.screen.get_size(); self.text("THE REBEL SHIP",w//2-205,h//2-80,48)
                self.text("A RACE TO BUILD THE STRONGEST FLEET",w//2-220,h//2-18,16,CYAN)
                self.text("PRESS ENTER OR CLICK TO BEGIN",w//2-182,h//2+50,16,TEXT)
            elif g.state == "control": self.draw_control()
            elif g.state == "paused": self.text("PAUSED  •  PRESS P TO CONTINUE",self.screen.get_width()//2-170,self.screen.get_height()//2,20)
            elif g.state in ("won", "lost"):
                veil=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA); veil.fill((4,10,18,215)); self.screen.blit(veil,(0,0))
                w,h=self.screen.get_size(); title="COMMANDER DEFEATED" if g.state=="won" else "SHIP LOST"
                self.text(title,w//2-190,h//2-40,36,CYAN if g.state=="won" else (255,105,122))
                self.text(f"SCORE {g.score}  •  PRESS R TO RESTART",w//2-175,h//2+25,16)
            pygame.display.flip()
        pygame.quit()


def main() -> None:
    """Start the desktop game."""
    Client().run()


if __name__ == "__main__":
    main()
