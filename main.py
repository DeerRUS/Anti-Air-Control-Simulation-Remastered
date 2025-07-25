from abc import ABC, abstractmethod
import math
import pygame as pg
from random import random, randint, choice
from pygame import Vector2

# PyGame Configuration
W, H = 600, 500
FPS = 60

# PyGame initializing
pg.init()
pg.font.init()
pg.mixer.init()

screen = pg.display.set_mode((W, H))
pg.display.set_caption("Anti-Air Control Simulator Remastered")
pg.display.set_icon(pg.image.load("thumbnail.png"))
clock = pg.time.Clock()

sound_explosion: pg.mixer.Sound = pg.mixer.Sound("explosion.wav")
sound_selection: pg.mixer.Sound = pg.mixer.Sound("selection.wav")
sound_detection: pg.mixer.Sound = pg.mixer.Sound("detection.wav")
sound_rule_changed: pg.mixer.Sound = pg.mixer.Sound("rule_changed.wav")
sound_score_change: pg.mixer.Sound = pg.mixer.Sound("score_change.wav")

sound_mainchannel: pg.mixer.Channel = pg.mixer.Channel(0)
sound_mainchannel.set_volume(0.01)

# Functions

def renderText(text: str, color: tuple[int, int, int], position: Vector2):
    content = pg.font.SysFont("Arial", 16, False, False).render(text, True, color)
    screen.blit(content, position)

def get_intersection_points(center, radius, point, direction):
    px, py = point
    cx, cy = center
    dx, dy = direction
    a = dx**2 + dy**2
    b = 2 * ((px - cx) * dx + (py - cy) * dy)
    c = (px - cx)**2 + (py - cy)**2 - radius**2
    discriminant = b**2 - 4*a*c
    if discriminant < 0:
        return None, None
    t1 = (-b + math.sqrt(discriminant)) / (2*a)
    t2 = (-b - math.sqrt(discriminant)) / (2*a)
    point1 = Vector2(int(px + t1*dx), int(py + t1*dy))
    point2 = Vector2(int(px + t2*dx), int(py + t2*dy))
    return point1, point2

def is_point_in_triangle(P, A, B, C, epsilon=1e-6):
    def triangle_area(P1, P2, P3):
        return abs((P2.x - P1.x) * (P3.y - P1.y) - (P3.x - P1.x) * (P2.y - P1.y)) / 2
    area_PBC = triangle_area(P, B, C)
    area_PCA = triangle_area(P, C, A)
    area_PAB = triangle_area(P, A, B)
    area_ABC = triangle_area(A, B, C)
    if abs(area_ABC) < epsilon:
        return False
    alpha = area_PBC / area_ABC
    beta = area_PCA / area_ABC
    gamma = area_PAB / area_ABC
    return abs(alpha + beta + gamma - 1) < epsilon and alpha >= -epsilon and beta >= -epsilon and gamma >= -epsilon

# Classes
class GameObject(ABC):
    def __init__(self, position: Vector2, draw_priorety: int):
        super().__init__()
        self.position: Vector2 = position.copy()
        self.draw_priorety = draw_priorety

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def draw(self):
        pass

class GameHandler:
    def __init__(self):
        self.gameobjects = list()

    def get(self) -> list[GameObject]:
        return self.gameobjects

    def add(self, gameobject: GameObject):
        self.gameobjects.append(gameobject)

    def remove(self, gameobject: GameObject):
        self.gameobjects.remove(gameobject)

    def update(self):
        for object in self.gameobjects:
            object.update()

    def draw(self):
        sortedgameobjects = sorted(self.gameobjects, key=lambda x: x.draw_priorety)
        for object in sortedgameobjects:
            object.draw()

    def findClosest(self, _type: type, position: Vector2):
        objects = list(filter(lambda x: type(x) is _type, self.gameobjects))
        if len(objects) == 0: return None
        closest = choice(objects)
        for object in objects:
            if (position-object.position).length() < (position-closest.position).length(): closest = object
        return closest

class Plane(GameObject):
    def __init__(self):
        super().__init__(Vector2((W-100)*random(), randint(0,1)*H), 3)
        self.direction = (Vector2((W-100)*random(), H if self.position.y == 0 else 0) - self.position).normalize()
        self.speed = random()/6
        self.selected = False
        self.default_color = (0, 255, 0)
        self.selected_color = (255, 255, 255)
        self.country = choice(FlyRuler.countryes_get())
        self.purpose = "CIVIL" if random() <= 0.8 else "ARMY"
        self.number = f"{randint(1,99999):05d}"
        self.spotted: bool = False
        self.allow_takedown: bool = False
        self.allow_control: bool = False

    def update(self):
        self.position += self.direction*self.speed
        if (self.position.y < 0 or self.position.y > H or self.position.x < 0 or self.position.x > W*0.85):
            if (not self.allow_takedown): score.add(10)
            gamehandler.remove(self)
        if (not self.spotted):
            spotted = is_point_in_triangle(
            self.position, 
            window_center, 
            window_center+Vector2(math.cos(pg.time.get_ticks()/radar_speed_tick), math.sin(pg.time.get_ticks()/radar_speed_tick))*245,
            window_center+Vector2(math.cos((pg.time.get_ticks()-200)/radar_speed_tick), math.sin((pg.time.get_ticks()-200)/radar_speed_tick))*245)
            if (spotted): 
                sound_mainchannel.play(sound_detection)
                gamehandler.add(Detection(self.position))
            self.spotted = spotted
        planes = list(filter(lambda x: type(x) is Plane, gamehandler.get().copy()))
        if self in planes: planes.remove(self)
        for i in planes:
            if (i.position-self.position).length() <= 5:
                gamehandler.add(Explosion(self.position))

    def draw(self):
        if ((window_center-self.position).length() > 250 or ((window_center-self.position).length() <= 250 and not self.spotted)): return
        if self.selected:
            out1, out2 = get_intersection_points(window_center, (W-100)/2, self.position, self.direction)
            in1, in2 = get_intersection_points(window_center, (W-100)/4, self.position, self.direction)
            if (in1 is None or in2 is None):
                pg.draw.line(screen, (0, 200, 0), out1, out2)
            else:
                pg.draw.line(screen, (0, 200, 0), out1, in1)
                pg.draw.line(screen, (200, 0, 0), in1, in2)
                pg.draw.line(screen, (0, 200, 0), in2, out2)
        else:
            pg.draw.line(screen, (0, 200, 0), self.position, self.position+self.direction*20)
        pg.draw.circle(screen, self.selected_color if self.selected else self.default_color, self.position, 2.5)
        if (self.allow_takedown): pg.draw.circle(screen, (255, 0, 0), self.position, 6+abs(math.sin(pg.time.get_ticks()/250)*4), 1)
    
    def takedown(self):
        if (self.position-window_center).length() <= 250 and self.spotted:
            if self.allow_takedown: score.add(10 if self.purpose == "CIVIL" else 25)
            else: score.sub(25 if self.purpose == "CIVIL" else 60)
        gamehandler.remove(self)

class Rocket(GameObject):
    def __init__(self, target: Plane):
        super().__init__(window_center, 4)
        self.target: Plane = target
        self.direction: Vector2
        self.target_speed: float = 0
        self.speed: float = 0
        self.launch_tick: float = pg.time.get_ticks()
        self.time_since_smoke: float = pg.time.get_ticks()
        self.calculateDirection()
        self.stage = 0

    def update(self):
        if ((self.speed <= 0.05 and self.stage >= 2) or (self.target is None) or ((self.target.position-self.position).length() <= 5)):
            self.explode()
        else:
            self.calculateDirection()
            self.speed = pg.math.lerp(self.speed, self.target_speed, 0.04 if self.stage == 1 else 0.0035)
            self.position += self.direction*self.speed

        if (self.time_since_smoke + 50 <= pg.time.get_ticks() and not self.stage == 3):
            self.time_since_smoke = pg.time.get_ticks()
            gamehandler.add(Smoke(self.position - self.direction*5, random()*(3 if self.stage <= 2 else 1), randint(2000,5000)))
            
        if (self.launch_tick + 1000*2 <= pg.time.get_ticks() and self.stage == 0):
            self.stage = 1
            self.target_speed = 1/2
        elif (self.launch_tick + 2000*2 <= pg.time.get_ticks() and self.stage == 1):
            self.stage = 2
            self.target_speed = 0.35/2
        elif (self.launch_tick + 4000*2 <= pg.time.get_ticks() and self.stage == 2):
            self.stage = 3
            self.target_speed = 0


    def draw(self):
        pg.draw.line(screen, (160, 160, 160), self.position - self.direction*5, self.position + self.direction*5, 2)

    def explode(self):
        gamehandler.add(Explosion(self.position))
        gamehandler.remove(self)

    def calculateDirection(self):
        self.direction = (self.target.position - self.position).normalize()

class Explosion(GameObject):
    def __init__(self, position):
        super().__init__(position, 2)
        sound_mainchannel.play(sound_explosion)
        self.radius = 10
        targets = list(filter(lambda x: type(x) is Plane, gamehandler.get()))
        for target in targets:
            if (target.position - self.position).length() <= self.radius:
                target.takedown()
        for i in range(25):
            gamehandler.add(Smoke(self.position+Vector2((random()-0.5)*20, (random()-0.5)*20), randint(2,5), randint(3500, 6000)))
    
    def update(self):
        self.radius /= 1.1
        if (self.radius <= 0.1): gamehandler.remove(self)

    def draw(self):
        pg.draw.circle(screen, (255, 165, 0), self.position, self.radius)

class Smoke(GameObject):
    def __init__(self, position: Vector2, radius: float, lifetime: float):
        super().__init__(position, 1)
        self.radius = radius
        self.lifetime = lifetime
        self.spawntick = pg.time.get_ticks()
        K = randint(140,240)
        self.color = (K, K, K)

    def update(self):
        if (self.spawntick+self.lifetime <= pg.time.get_ticks()):
            gamehandler.remove(self)
        else:
            self.position += Vector2(random()-0.5, random()-0.5)/4

    def draw(self):
        pg.draw.circle(screen, self.color, self.position, self.radius)

class Detection(GameObject):
    def __init__(self, position):
        super().__init__(position, 1)
        self.radius = 15
        self.color = (0, 255, 0)

    def update(self):
        self.radius -= 0.35
        if (self.radius <= 1): gamehandler.remove(self)

    def draw(self):
        pg.draw.circle(screen, self.color, self.position, self.radius)

class Rule:
    def __init__(self, country: str, purpose: str, zone: str):
        self.country: str = country
        self.purpose: str = purpose
        self.zone: str = zone

    def check(self, plane: Plane):
        dist = (window_center-plane.position).length()
        if (self.country == plane.country and (H/2 if self.zone == "ALL" else H/4) >= dist and (self.purpose == plane.purpose or self.purpose == "ALL")):
            plane.allow_takedown = True
        else:
            plane.allow_takedown = False
        if (self.country == plane.country and (self.purpose == plane.purpose or self.purpose == "ALL")):
            plane.allow_control = False
        else:
            plane.allow_control = True

class FlyRuler:
    countryes: list[str] = "AT BE HU DE DK ES IT LV LT LU NL PL PT SI FI FR HR CZ SE EE RF UK BY TY AZ".split()
    purposes: list[str] = "CIVIL ARMY".split()

    def __init__(self):
        self.rules: list[Rule] = list()
        self.draw_point: Vector2 = Vector2(W*0.85, 120)

    @staticmethod
    def countryes_get() -> list[str]:
        return FlyRuler.countryes
    
    def rule_add_random(self):
        rule = Rule(choice(self.countryes), choice(self.purposes) if random() <= 0.65 else "ALL", choice("ALL CNR".split()))
        if(self.rules.__len__() > 0):
            for i in self.rules:
                if ( (i.country == rule.country and i.purpose == rule.purpose and (i.zone == rule.zone or (rule.zone == "ALL" and i.zone == "CNR") ) ) ): return self.rule_add_random
        self.rules.append(rule)

    def rule_remove_random(self):
        if (self.rules.__len__() == 0): return
        self.rules.remove(choice(self.rules))

    def check_plane(self, plane: Plane):
        for rule in self.rules:
            rule.check(plane)

    def draw(self):
        renderText(" NO-FLY LIST", (255, 255, 255), self.draw_point)
        i = 0
        for rule in self.rules:
            i += 1
            renderText(f"{rule.country}.{rule.purpose}.{rule.zone}", (255, 255, 255), self.draw_point+Vector2(0, 24*i))

class Score:
    def __init__(self):
        self.score = 0
    
    def add(self, value: int):
        self.score += abs(value)
        sound_mainchannel.play(sound_score_change)

    def sub(self, value: int):
        self.score -= abs(value)
        sound_mainchannel.play(sound_score_change)

    def get(self) -> int:
        return self.score
    


# Game Configuration
window_center: Vector2 = Vector2(W/2-50, H/2)
selected_plane: Plane = None

gamehandler: GameHandler = GameHandler()
gamehandler.add(Plane())

flyRuler: FlyRuler = FlyRuler()

radar_speed_tick = 1200

last_plane = 0
last_rule_change = 2500

score: Score = Score()

paused: bool = False
paused_time: float = False
# Game Cycle
play = True
while play:
    # Pause
    while paused:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                paused = False
                play = False
            if event.type == pg.KEYDOWN:
                if (event.key == pg.K_ESCAPE):
                    paused_time -= abs(pg.time.get_ticks())
                    last_plane += paused_time
                    last_rule_change += paused_time
                    paused = False
        
        renderText("PAUSED", (255, 255, 255), (W/2, H/2))
        clock.tick(FPS)
        pg.display.flip()
    
    screen.fill((0, 0, 0))
    # Update
    mouse_position = Vector2(pg.mouse.get_pos())

    # Plane Spawn
    if (last_plane <= pg.time.get_ticks()):
        last_plane = pg.time.get_ticks() + randint(5000, 15000)
        gamehandler.add(Plane())

    # Rule Assign
    if (last_rule_change <= pg.time.get_ticks()):
        last_rule_change = pg.time.get_ticks() + randint(45000, 75000)
        if (flyRuler.rules.__len__() < 15):
            if (flyRuler.rules.__len__()>=3): flyRuler.rule_add_random() if random() >= 0.5 else flyRuler.rule_remove_random()
            else: flyRuler.rule_add_random()
        else: 
            flyRuler.rule_remove_random()
        sound_mainchannel.play(sound_rule_changed)

    # Rule Check
    if (not selected_plane is None):
        flyRuler.check_plane(selected_plane)

    gamehandler.update()

    for event in pg.event.get():
        if event.type == pg.QUIT:
            play = False
        if event.type == pg.MOUSEBUTTONDOWN:
            if (event.button == 1):
                # Select Plane
                if (not selected_plane is None): 
                        selected_plane.selected = False
                        selected_plane = None
                plane = gamehandler.findClosest(Plane, event.pos)
                if (not (plane is None) and (plane.position - event.pos).length() <= 10):
                    selected_plane = plane
                    plane.selected = True
                    sound_mainchannel.play(sound_selection)
            if (event.button == 3):
                rocket = gamehandler.findClosest(Rocket, event.pos)
                if (not (rocket is None) and (rocket.position - event.pos).length() <= 10):
                    rocket.explode()
        if event.type == pg.KEYDOWN:
            if (not selected_plane is None):
                if (selected_plane.allow_control):
                    if (event.key == pg.K_LEFT):
                        selected_plane.direction = selected_plane.direction.rotate(-1)
                    if (event.key == pg.K_RIGHT):
                        selected_plane.direction = selected_plane.direction.rotate(1)
                if (event.key == pg.K_SPACE):
                    # Launch Rocket
                    gamehandler.add(Rocket(selected_plane))
                    selected_plane.selected = False
                    selected_plane = None
            if (event.key == pg.K_ESCAPE):
                paused = True
                paused_time = pg.time.get_ticks()

    # Draw

    pg.draw.line(screen, (0, 150, 0), (W-100, 0), (W-100, H), 4)
    renderText(f"S:{score.get():010d}", (255,255,255), Vector2(W*0.85, 8))
    pg.draw.line(screen, (0, 150, 0), (W-100, 32), (W, 32), 4)
    if (not selected_plane is None):
        renderText(f"{selected_plane.country}-{selected_plane.number}", (255, 255, 255), Vector2(W*0.85, 40))
        renderText(f"P:[{int(selected_plane.position.x):3d}, {int(selected_plane.position.y):03d}]", (255, 255, 255), Vector2(W*0.85, 56))
        renderText(f"V:[{int(selected_plane.direction.x*selected_plane.speed*100):04d}, {int(selected_plane.direction.y*selected_plane.speed*100):04d}]", (255, 255, 255), Vector2(W*0.85, 72))
        renderText(f"C:{selected_plane.purpose}", (255, 255, 255), Vector2(W*0.85, 88))
        norm: Vector2 = (selected_plane.position-window_center).normalize()
        dist: Vector2 = (selected_plane.position-window_center).length()+math.sin(pg.time.get_ticks()/100)*10
        pg.draw.lines(screen, (0, 150, 0), True, [window_center, norm*250+window_center+norm.rotate(90)*5, norm*250+window_center-norm.rotate(90)*5])
        pg.draw.line(screen, (0, 150, 0), window_center+norm*dist+norm.rotate(90)*dist*0.02, window_center+norm*dist-norm.rotate(90)*dist*0.02)
    elif not (mouse_position-window_center).length() == 0:
        norm: Vector2 = (mouse_position-window_center).normalize()
        dist: Vector2 = abs(math.sin(pg.time.get_ticks()/200))*250
        pg.draw.lines(screen, (0, 150, 0), True, [window_center, norm*250+window_center+norm.rotate(90)*5, norm*250+window_center-norm.rotate(90)*5])
        pg.draw.line(screen, (0, 150, 0), window_center+norm*dist+norm.rotate(90)*dist*0.02, window_center+norm*dist-norm.rotate(90)*dist*0.02)
    pg.draw.line(screen, (0, 150, 0), (W-100, 112), (W, 112), 4)
    flyRuler.draw()

    pg.draw.circle(screen, (0, 150, 0), window_center, 3)
    gamehandler.draw()
    pg.draw.circle(screen, (0, 150, 0), window_center, H/2, 5)
    pg.draw.circle(screen, (0, 150, 0), window_center, H/4, 2)
    pg.draw.line(screen, (0, 150, 0), window_center, window_center+Vector2(math.cos(pg.time.get_ticks()/radar_speed_tick), math.sin(pg.time.get_ticks()/radar_speed_tick))*245)
    pg.draw.line(screen, (0, 50, 0), window_center, window_center+Vector2(math.cos((pg.time.get_ticks()-200)/radar_speed_tick), math.sin((pg.time.get_ticks()-200)/radar_speed_tick))*245)
    
    clock.tick(FPS)
    pg.display.flip()

pg.quit()
quit()