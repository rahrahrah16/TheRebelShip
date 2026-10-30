"""Simple game rules for The Rebel Ship. This file does not use pygame."""

import math
import random


# Use the same four resources everywhere in the game and HUD.
RESOURCES = ["Iron", "Copper", "Crystal", "Power"]
DRONE_COST = {"Iron": 34, "Copper": 24, "Crystal": 15, "Power": 18}
UPGRADES = ["Weapons", "Mining", "Drone capacity", "Ship health"]


class Asteroid:
    """A rock that gives one resource each time it is mined."""
    def __init__(self, x, y, resource, seed):
        self.x = x
        self.y = y
        self.resource = resource
        self.amount = 6
        self.radius = random.randint(24, 40)
        self.seed = seed


class Ship:
    """A helper or enemy ship with health and a simple order."""
    def __init__(self, x, y, health=40):
        self.x = x
        self.y = y
        self.health = health
        self.order = "Follow"
        self.cooldown = 0
        self.target = None


class Bullet:
    """A projectile moving in a straight line."""
    def __init__(self, x, y, dx, dy, owner, damage):
        self.x, self.y = x, y
        self.dx, self.dy = dx, dy
        self.owner = owner
        self.damage = damage


class Game:
    """Stores the game and updates its simple rules."""
    def __init__(self, width=1600, height=900):
        self.width, self.height = width, height
        self.start_game()
        self.state = "menu"

    def start_game(self):
        """Set up a new game with starter resources and one helper."""
        self.player_x, self.player_y = self.width / 2, self.height / 2
        self.health, self.max_health = 100, 100
        self.resources = {"Iron": 50, "Copper": 35, "Crystal": 20, "Power": 25}
        self.upgrades = {name: 0 for name in UPGRADES}
        self.drones = [Ship(self.player_x - 40, self.player_y)]
        self.enemies, self.asteroids, self.bullets = [], [], []
        self.boss = None
        self.boss_health = 0
        self.boss_level = 1
        self.rival_resources = 0
        self.elapsed = self.shot_wait = self.enemy_wait = self.level_wait = 0
        self.score = 0
        self.notice = ""
        self.notice_wait = 0
        self.selected_drone = 0
        self.make_asteroids(26)

    def make_asteroids(self, amount):
        """Add rocks at random places in the play area."""
        for number in range(amount):
            x = random.randint(70, self.width - 70)
            y = random.randint(120, self.height - 60)
            resource = random.choice(RESOURCES)
            self.asteroids.append(Asteroid(x, y, resource, random.randint(1, 999999)))

    def move_player(self, dx, dy, seconds):
        """Move the ship; normalize diagonal input so it is not faster."""
        length = math.hypot(dx, dy)
        if length > 0:
            self.player_x += dx / length * 300 * seconds
            self.player_y += dy / length * 300 * seconds
        self.player_x = max(24, min(self.width - 24, self.player_x))
        self.player_y = max(90, min(self.height - 24, self.player_y))

    def shoot(self, target_x, target_y):
        """Shoot one bullet toward the mouse when the gun is ready."""
        if self.state != "play" or self.shot_wait > 0:
            return
        dx, dy = target_x - self.player_x, target_y - self.player_y
        length = max(1, math.hypot(dx, dy))
        speed = 600
        damage = 24 + self.upgrades["Weapons"] * 8
        self.bullets.append(Bullet(self.player_x, self.player_y,
                                   dx / length * speed, dy / length * speed,
                                   "player", damage))
        self.shot_wait = 0.28

    def assign_drone(self, number, order):
        """Give one helper the Mining, Attacking or Follow order."""
        if 0 <= number < len(self.drones) and order in ("Mining", "Attacking", "Follow"):
            self.drones[number].order = order
            self.drones[number].target = None

    def recall_drones(self):
        """Send every helper back to follow the player."""
        for drone in self.drones:
            drone.order = "Follow"
            drone.target = None

    def build_drone(self):
        """Spend resources to build a helper, if there is room."""
        capacity = 6 + self.upgrades["Drone capacity"] * 2
        if len(self.drones) >= capacity:
            self.show_notice("Fleet is full")
            return
        for resource in RESOURCES:
            if self.resources[resource] < DRONE_COST[resource]:
                self.show_notice("Not enough resources")
                return
        for resource in RESOURCES:
            self.resources[resource] -= DRONE_COST[resource]
        self.drones.append(Ship(self.player_x, self.player_y))
        self.show_notice("Helper ship built")

    def upgrade(self, name):
        """Buy one upgrade. Each next level costs more resources."""
        if name not in self.upgrades or self.upgrades[name] >= 5:
            return
        level = self.upgrades[name] + 1
        # Keeping one small cost formula makes the price easy to explain.
        cost = {"Iron": 20 * level, "Copper": 14 * level,
                "Crystal": 10 * level, "Power": 8 * level}
        for resource in RESOURCES:
            if self.resources[resource] < cost[resource]:
                self.show_notice("Not enough resources")
                return
        for resource in RESOURCES:
            self.resources[resource] -= cost[resource]
        self.upgrades[name] = level
        if name == "Ship health":
            self.max_health += 20
            self.health = min(self.max_health, self.health + 20)
        self.show_notice(name + " upgraded")

    def show_notice(self, message):
        """Show a short message in the game window."""
        self.notice, self.notice_wait = message, 2

    def update(self, seconds):
        """Advance time and update shots, enemies, asteroids and helpers."""
        if self.state != "play":
            return
        seconds = min(seconds, 0.05)
        self.elapsed += seconds
        # The rival gathers resources steadily, just like the player.
        self.rival_resources += seconds * 2
        self.shot_wait = max(0, self.shot_wait - seconds)
        self.notice_wait = max(0, self.notice_wait - seconds)
        self.enemy_wait += seconds
        self.level_wait += seconds

        # The rival grows over time and sends more fighters as its level rises.
        if self.elapsed > 105 and self.boss is None:
            self.boss = Ship(self.width - 90, self.height / 2, 550)
            self.show_notice("Rival commander located")
        if self.level_wait >= 20:
            self.level_wait = 0
            self.boss_level += 1
        # The rival spends 40 resources to add another ship to its fleet.
        if self.rival_resources >= 40 and len(self.enemies) < min(10, self.boss_level + 1):
            self.rival_resources -= 40
            side = random.choice([20, self.width - 20])
            self.enemies.append(Ship(side, random.randint(120, self.height - 30), 40 + self.boss_level * 4))
        # New rocks slowly appear so the map does not become empty.
        if self.enemy_wait > 12:
            self.enemy_wait = 0
            if len(self.asteroids) < 30:
                self.make_asteroids(1)

        self.move_bullets(seconds)
        self.move_enemies(seconds)
        self.move_drones(seconds)

    def move_bullets(self, seconds):
        """Move bullets and check what each bullet hits."""
        for bullet in self.bullets[:]:
            bullet.x += bullet.dx * seconds
            bullet.y += bullet.dy * seconds
            if not (0 <= bullet.x <= self.width and 80 <= bullet.y <= self.height):
                self.bullets.remove(bullet)
                continue
            if bullet.owner == "player":
                # Player shots mine rocks and can damage enemy ships.
                rock = self.find_hit(bullet, self.asteroids)
                if rock:
                    rock.amount -= 1
                    self.resources[rock.resource] += 1
                    self.score += 1
                    self.bullets.remove(bullet)
                    if rock.amount <= 0:
                        self.asteroids.remove(rock)
                    continue
                enemies = self.enemies[:]
                if self.boss:
                    enemies.append(self.boss)
                ship = self.find_hit(bullet, enemies)
                if ship:
                    ship.health -= bullet.damage
                    self.bullets.remove(bullet)
                    if self.boss and ship is self.boss and ship.health <= 0:
                        self.state = "won"
                    elif ship in self.enemies and ship.health <= 0:
                        self.enemies.remove(ship)
                        self.score += 20
            elif math.hypot(bullet.x-self.player_x, bullet.y-self.player_y) < 18:
                self.health -= bullet.damage
                self.bullets.remove(bullet)
                if self.health <= 0:
                    self.health, self.state = 0, "lost"

    @staticmethod
    def find_hit(bullet, objects):
        """Return the first asteroid or ship touched by a bullet."""
        for obj in objects:
            radius = getattr(obj, "radius", 20)
            if math.hypot(bullet.x-obj.x, bullet.y-obj.y) < radius:
                return obj
        return None

    def move_enemies(self, seconds):
        """Move enemy ships toward the player and occasionally fire."""
        for enemy in self.enemies:
            self.move_toward(enemy, self.player_x, self.player_y, 95, seconds)
            enemy.cooldown -= seconds
            close = math.hypot(enemy.x-self.player_x, enemy.y-self.player_y) < 650
            if close and enemy.cooldown <= 0:
                self.fire_enemy(enemy.x, enemy.y, self.player_x, self.player_y, 12)
                enemy.cooldown = 1.5
        if self.boss:
            self.boss_x = self.width - 90
            self.boss_y = self.height / 2 + math.sin(self.elapsed) * 150
            self.boss.x, self.boss.y = self.boss_x, self.boss_y
            self.enemy_wait += 0  # The boss position changes gently as time passes.
            if not hasattr(self, "boss_cooldown"):
                self.boss_cooldown = 1
            self.boss_cooldown -= seconds
            if self.boss_cooldown <= 0:
                self.fire_enemy(self.boss_x, self.boss_y, self.player_x, self.player_y, 18)
                self.boss_cooldown = 1

    def move_drones(self, seconds):
        """Mine rocks, attack nearby enemies, or follow the player."""
        for number, drone in enumerate(self.drones):
            drone.cooldown -= seconds
            if drone.order == "Mining":
                # Pick the closest rock and fly toward it.
                rock = self.closest(drone, self.asteroids)
                if rock:
                    self.move_toward(drone, rock.x, rock.y, 170, seconds)
                    if math.hypot(drone.x-rock.x, drone.y-rock.y) < rock.radius + 12 and drone.cooldown <= 0:
                        rock.amount -= 1
                        self.resources[rock.resource] += 1
                        drone.cooldown = max(0.35, 0.8 - self.upgrades["Mining"] * 0.08)
                        if rock.amount <= 0:
                            self.asteroids.remove(rock)
                else:
                    # There is no work left, so this helper comes home.
                    drone.order = "Follow"
            elif drone.order == "Attacking":
                targets = self.enemies[:]
                if self.boss:
                    targets.append(self.boss)
                enemy = self.closest(drone, targets)
                if enemy:
                    self.move_toward(drone, enemy.x, enemy.y, 150, seconds)
                    if math.hypot(drone.x-enemy.x, drone.y-enemy.y) < 300 and drone.cooldown <= 0:
                        self.fire_enemy(drone.x, drone.y, enemy.x, enemy.y, 8, "player")
                        drone.cooldown = 1
                else:
                    # Return to the player when every hostile ship is gone.
                    drone.order = "Follow"
            else:
                # Different offsets make the helpers orbit loosely behind the ship.
                angle = number * 2.3 + self.elapsed
                x = self.player_x + math.cos(angle) * 48
                y = self.player_y + math.sin(angle) * 38
                self.move_toward(drone, x, y, 200, seconds)

    @staticmethod
    def closest(ship, objects):
        """Find the nearest object in a list, or return None."""
        if not objects:
            return None
        return min(objects, key=lambda obj: math.hypot(ship.x-obj.x, ship.y-obj.y))

    @staticmethod
    def move_toward(ship, x, y, speed, seconds):
        """Move a ship toward a point at a steady speed."""
        dx, dy = x-ship.x, y-ship.y
        length = math.hypot(dx, dy)
        if length > 1:
            ship.x += dx / length * speed * seconds
            ship.y += dy / length * speed * seconds

    def fire_enemy(self, x, y, target_x, target_y, damage, owner="enemy"):
        """Fire a bullet; enemy bullets hurt the player, helper bullets hurt foes."""
        dx, dy = target_x-x, target_y-y
        length = max(1, math.hypot(dx, dy))
        self.bullets.append(Bullet(x, y, dx/length*340, dy/length*340, owner, damage))

    def resize(self, width, height):
        """Update the play area's size after the window is resized."""
        self.width, self.height = width, height
        self.player_x = min(max(24, self.player_x), width-24)
        self.player_y = min(max(90, self.player_y), height-24)
