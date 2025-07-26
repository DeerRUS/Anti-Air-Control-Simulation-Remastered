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
pg.display.set_icon(pg.image.load("assets/thumbnail.png"))
clock = pg.time.Clock()

sound_explosion: pg.mixer.Sound = pg.mixer.Sound("assets/explosion.wav")
sound_selection: pg.mixer.Sound = pg.mixer.Sound("assets/selection.wav")
sound_detection: pg.mixer.Sound = pg.mixer.Sound("assets/detection.wav")
sound_rule_changed: pg.mixer.Sound = pg.mixer.Sound("assets/rule_changed.wav")
sound_score_change: pg.mixer.Sound = pg.mixer.Sound("assets/score_change.wav")

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
        self.start_side: int = randint(0,1)*H
        self.return_point: Vector2 = Vector2(randint(0, W*0.85), self.start_side)
        super().__init__(Vector2((W-100)*random(), self.start_side), 3)
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

        self.get_back: bool = False
        self.allow_back: bool = True if random() <= 0.65 else False

    def update(self):
        self.position += self.direction*self.speed
        if (self.position.y < 0 or self.position.y > H or self.position.x < 0 or self.position.x > W*0.85):
            if (self.get_back):
                score.add(30)
            else:
                score.add(10) if not self.allow_takedown else score.sub(25)
            gamehandler.remove(self)
        if (not self.spotted):
            spotted = is_point_in_triangle(
            self.position, 
            window_center, 
            window_center+Vector2(math.cos(radar.radar_tick/Radar.radar_speed_tick), math.sin(radar.radar_tick/Radar.radar_speed_tick))*245,
            window_center+Vector2(math.cos((radar.radar_tick-200)/Radar.radar_speed_tick), math.sin((radar.radar_tick-200)/Radar.radar_speed_tick))*245)
            if (spotted): 
                sound_mainchannel.play(sound_detection)
                gamehandler.add(Detection(self.position))
            self.spotted = spotted
        if (not self.allow_takedown and (self.position-window_center).length()<=H/4): flyRuler.check_plane(self)
        if (self.get_back): 
            pg.draw.line(screen, (0, 255, 0), self.position, self.return_point)
            target = (self.return_point-self.position).normalize()
            self.direction = Vector2(pg.math.lerp(self.direction.x, target.x, 0.001), pg.math.lerp(self.direction.y, target.y, 0.001)) 

    def draw(self):
        if ((window_center-self.position).length() > 245 or ((window_center-self.position).length() <= 245 and not self.spotted)): return
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
        if (self.allow_takedown): pg.draw.circle(screen, (255, 0, 0), self.position, 10, 2)
    
    def takedown(self):
        if (self.position-window_center).length() <= 250 and self.spotted:
            if self.allow_takedown: score.add(10 if self.purpose == "CIVIL" else 25)
            else: score.sub(25 if self.purpose == "CIVIL" else 60)
        gamehandler.remove(self)

    def on_message(self):
        if (self.purpose == "CIVIL" and self.allow_back and self.allow_takedown and not self.get_back): self.get_back = True

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
        if (self.country == plane.country and (True if self.zone == "ALL" else (H/4 >= dist)) and (self.purpose == plane.purpose or self.purpose == "ALL")):
            plane.allow_takedown = True

class FlyRuler:
    countryes: list[str] = "DE IT PT SI FR CZ RF UK BY TY AZ KZ".split()
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
        self.draw()
        self.check_planes()

    def rule_remove_random(self):
        if (self.rules.__len__() == 0): return
        self.rules.remove(choice(self.rules))
        self.draw()
        self.check_planes()

    def check_planes(self):
        planes = list(filter(lambda x: type(x) is Plane, gamehandler.get()))
        for rule in self.rules:
            map(rule.check, planes)

    def check_plane(self, plane: Plane):
        for rule in self.rules:
            rule.check(plane)

    
    def draw(self):
        pg.draw.rect(screen, (0,0,0), (self.draw_point.x, self.draw_point.y, W, H))
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

class Radar:
    radar_speed_tick: int = 1200

    def __init__(self):
        self.draw_priorety = 5
        self.selected_plane: Plane = None
        self.radar_tick: int = 0

    def update(self):
        self.radar_tick += 1000/FPS

    def select_plane(self, position: Vector2):
        if (not radar.selected_plane is None): 
            radar.selected_plane.selected = False
            radar.selected_plane = None
        plane = gamehandler.findClosest(Plane, position)
        if (not (plane is None) and (plane.position - position).length() <= 10):
            radar.selected_plane = plane
            plane.selected = True
            sound_mainchannel.play(sound_selection)

    def launch_rocket(self):
        gamehandler.add(Rocket(self.selected_plane))
        self.selected_plane.selected = False
        self.selected_plane = None

    def destroy_rocket(self, position: Vector2):
        rocket = gamehandler.findClosest(Rocket, event.pos)
        if (not (rocket is None) and (rocket.position - event.pos).length() <= 10):
            rocket.explode()

    def send_message(self):
        self.selected_plane.on_message()

    def draw(self):
        pg.draw.circle(screen, (0, 150, 0), window_center, 3)
        if (not self.selected_plane is None):
            renderText(f"{self.selected_plane.country}-{self.selected_plane.number}", (255, 255, 255), Vector2(W*0.85, 40))
            renderText(f"P:[{int(self.selected_plane.position.x):3d}, {int(self.selected_plane.position.y):03d}]", (255, 255, 255), Vector2(W*0.85, 56))
            renderText(f"V:[{int(self.selected_plane.direction.x*self.selected_plane.speed*100):04d}, {int(self.selected_plane.direction.y*self.selected_plane.speed*100):04d}]", (255, 255, 255), Vector2(W*0.85, 72))
            renderText(f"C:{self.selected_plane.purpose}", (255, 255, 255), Vector2(W*0.85, 88))
            norm: Vector2 = (self.selected_plane.position-window_center).normalize()
            dist: Vector2 = (self.selected_plane.position-window_center).length()+math.sin(pg.time.get_ticks()/100)*10
            pg.draw.lines(screen, (0, 150, 0), True, [window_center, norm*250+window_center+norm.rotate(90)*5, norm*250+window_center-norm.rotate(90)*5])
            pg.draw.line(screen, (0, 150, 0), window_center+norm*dist+norm.rotate(90)*dist*0.02, window_center+norm*dist-norm.rotate(90)*dist*0.02)
        elif not (mouse_position-window_center).length() == 0:
            norm: Vector2 = (mouse_position-window_center).normalize()
            dist: Vector2 = abs(math.sin(pg.time.get_ticks()/200))*250
            pg.draw.lines(screen, (0, 150, 0), True, [window_center, norm*250+window_center+norm.rotate(90)*5, norm*250+window_center-norm.rotate(90)*5])
            pg.draw.line(screen, (0, 150, 0), window_center+norm*dist+norm.rotate(90)*dist*0.02, window_center+norm*dist-norm.rotate(90)*dist*0.02)
        pg.draw.circle(screen, (0, 150, 0), window_center, H/2, 5)
        pg.draw.circle(screen, (0, 150, 0), window_center, H/4, 2)
        pg.draw.line(screen, (0, 150, 0), window_center, window_center+Vector2(math.cos(self.radar_tick/Radar.radar_speed_tick), math.sin(self.radar_tick/Radar.radar_speed_tick))*245)
        pg.draw.line(screen, (0, 50, 0), window_center, window_center+Vector2(math.cos((self.radar_tick-200)/Radar.radar_speed_tick), math.sin((self.radar_tick-200)/Radar.radar_speed_tick))*245)
    


# Game Configuration
window_center: Vector2 = Vector2(W/2-50, H/2)
radar: Radar = Radar()

gamehandler: GameHandler = GameHandler()
gamehandler.add(Plane())

flyRuler: FlyRuler = FlyRuler()

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
    
    pg.draw.rect(screen, (0,0,0), (0, 0, 500, 500))
    pg.draw.rect(screen, (0,0,0), (500, 0, W, 110))
    # Update
    mouse_position = Vector2(pg.mouse.get_pos())

    radar.update()
    # Plane Spawn
    if (last_plane <= pg.time.get_ticks()):
        last_plane = pg.time.get_ticks() + randint(5000, 15000)
        plane = Plane()
        gamehandler.add(plane)
        flyRuler.check_plane(plane)

    # Rule Assign
    if (last_rule_change <= pg.time.get_ticks()):
        last_rule_change = pg.time.get_ticks() + randint(30000, 60000)
        if (flyRuler.rules.__len__() < 10):
            if (flyRuler.rules.__len__()>5): flyRuler.rule_add_random() if random() <= 0.70 else flyRuler.rule_remove_random()
            else: flyRuler.rule_add_random()
        else: 
            flyRuler.rule_remove_random()
        sound_mainchannel.play(sound_rule_changed)

    gamehandler.update()

    for event in pg.event.get():
        if event.type == pg.QUIT:
            play = False
        if event.type == pg.MOUSEBUTTONDOWN:
            if (event.button == 1):
                radar.select_plane(event.pos)
            if (event.button == 3):
                radar.destroy_rocket(event.pos)
        if event.type == pg.KEYDOWN:
            if (not radar.selected_plane is None):
                if (event.key == pg.K_SPACE):
                    radar.launch_rocket()
                if (event.key == pg.K_LALT or event.key == pg.K_RALT):
                    radar.send_message()
            if (event.key == pg.K_ESCAPE):
                paused = True
                paused_time = pg.time.get_ticks()
            if (event.key == pg.K_r):
                flyRuler.rule_add_random()
            elif (event.key == pg.K_d):
                flyRuler.rule_remove_random()
            if (event.key == pg.K_s):
                plane = Plane()
                gamehandler.add(plane)
                flyRuler.check_plane(plane)

    # Draw

    pg.draw.line(screen, (0, 150, 0), (W-100, 0), (W-100, H), 4)
    renderText(f"S:{score.get():010d}", (255,255,255), Vector2(W*0.85, 8))
    pg.draw.line(screen, (0, 150, 0), (W-100, 32), (W, 32), 4)
    pg.draw.line(screen, (0, 150, 0), (W-100, 112), (W, 112), 4)

    radar.draw()
    gamehandler.draw()
    
    clock.tick(FPS)
    pg.display.flip()

pg.quit()