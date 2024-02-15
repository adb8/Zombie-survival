from pygame import *
from pygame import mixer
import math
import threading
import random

init()
screen = display.set_mode()

WINDOW_WIDTH, WINDOW_HEIGHT = screen.get_size()
FRAMES = 60

score = 0
time_between_spawns = 2
can_take_damage_now = True

ascent, descent = True, False
game_running, window_running = True, True
zombie_array, bullet_array = [], []
holding_w, holding_s, holding_d, holding_a, holding_click = False, False, False, False, False

display.set_caption("zombie survival")
icon = image.load("images/red.png")
icon = transform.scale(icon, (32, 32))
display.set_icon(icon)
floor_image = image.load("images/floor.jpg")

clock = time.Clock()
small_font = font.Font("freesansbold.ttf", 40)
big_font = font.Font("freesansbold.ttf", 150)

gun_sound = mixer.Sound("sounds/gunshot.mp3")
zombie_death_sound = mixer.Sound("sounds/zombiedeath.ogg")
game_over_sound = mixer.Sound("sounds/gameover.wav")
damage_sound = mixer.Sound("sounds/damage.mp3")

class Bullet():
    def __init__(self, x, y, unit_x, unit_y):
        self.x = x
        self.y = y
        self.unit_x = unit_x
        self.unit_y = unit_y
        self.color = "yellow"
        self.radius = 5

class Player:
    def __init__(self):
        self.x = WINDOW_WIDTH/2
        self.y = WINDOW_HEIGHT/2
        self.health = 100
        self.radius = 25
        self.speed = 5
        self.color = (0, 200, 0)
        self.x_to_follow = WINDOW_WIDTH/2
        self.y_to_follow = WINDOW_HEIGHT/2

class Zombie:
    def __init__(self, x, y, radius, color, perma_color, speed, health, damage, difficulty):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.color = color
        self.perma_color = perma_color
        self.health = health
        self.damage = damage
        self.animating = False
        self.difficulty = difficulty

player = Player()

def draw_player():
    draw.circle(screen, player.color, (player.x, player.y), player.radius)

def draw_map():
    for x in range(WINDOW_WIDTH+1):
        if x % 512 == 0:
            for y in range(WINDOW_HEIGHT+1):
                if y % 512 == 0:
                    screen.blit(floor_image, (x, y))

def handle_player_movement():
    if holding_a and not holding_d:
        player.x -= player.speed
    if holding_d and not holding_a:
        player.x += player.speed
    if holding_w and not holding_s:
        player.y -= player.speed
    if holding_s and not holding_w:
        player.y += player.speed

def prevent_boundary_escape():
    if player.x > WINDOW_WIDTH - player.radius:
        player.x = WINDOW_WIDTH - player.radius
    if player.x < 0 + player.radius:
        player.x = player.radius
    if player.y > WINDOW_HEIGHT - player.radius:
        player.y = WINDOW_HEIGHT - player.radius
    if player.y < 0 + player.radius:
        player.y = player.radius

def decrease_time_between_zombie_spawn():
    if not window_running:
        return
    global time_between_spawns
    time_between_spawns *= 0.95
    threading.Timer(5, decrease_time_between_zombie_spawn).start()

def spawn_zombie():
    if not window_running:
        return
    global zombie_array, time_between_spawns
    difficulty = random.choice([0, 1, 2])
    # difficulty, radius, speed, color, health, damage
    stats = [
        ["easy", 25, 1, (255, 100, 100), 50, 10],
        ["medium", 32, 2, (255, 70, 70), 100, 15],
        ["hard", 40, 3, (255, 40, 40), 150, 25]
    ]

    random_x = random.randint(0, WINDOW_WIDTH)
    random_y = random.randint(0, WINDOW_HEIGHT)

    def do_coords_collide_with_others(x, y):
        other_array = []
        for zombie in zombie_array:
            other_array.append(zombie)
        other_array.append(player)
        for zombie in other_array:
            if distance(x, y, zombie.x, zombie.y) < zombie.radius + stats[difficulty][1] + 20:
                return True
        return False

    while do_coords_collide_with_others(random_x, random_y):
        random_x = random.randint(0, WINDOW_WIDTH)
        random_y = random.randint(0, WINDOW_HEIGHT)

    zombie = Zombie(x=random_x, y=random_y, radius=stats[difficulty][1], 
                    color=stats[difficulty][3], perma_color=stats[difficulty][3],
                    speed=stats[difficulty][2], health=stats[difficulty][4], 
                    damage=stats[difficulty][5], difficulty=stats[difficulty][0])
    zombie_array.append(zombie)
    threading.Timer(time_between_spawns, spawn_zombie).start()

def distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def register_player_damage(zombie):
    if not window_running:
        return
    def change_player_color_back():
        player.color = (0, 200, 0)
        
    if can_take_damage_now:
        player.health -= zombie.damage
        damage_sound.play()
        player.color = (150, 200, 150)
        threading.Timer(0.1, change_player_color_back).start()
    handle_damage_delay()

def update_follow_point():
    if not window_running:
        return
    player.x_to_follow = player.x
    player.y_to_follow = player.y
    threading.Timer(0.25, update_follow_point).start()

def zombie_movement():
    if not window_running:
        return
    global zombie_array
    for zombie in zombie_array:
        player_damage = False
        other_array = []
        for zombie_2 in zombie_array:
            if zombie_2 != zombie:
                other_array.append(zombie_2)
        other_array.append(player)

        if zombie.x > player.x_to_follow:
            zombie.x -= zombie.speed
        elif zombie.x < player.x_to_follow:
            zombie.x += zombie.speed
        if zombie.y > player.y_to_follow:
            zombie.y -= zombie.speed
        elif zombie.y < player.y_to_follow:
            zombie.y += zombie.speed

        for others in other_array:
            dist = distance(zombie.x, zombie.y, others.x, others.y)
            if dist < zombie.radius + others.radius:
                if others == player:
                    player_damage = True
                if zombie.x > others.x:
                    zombie.x += zombie.speed
                elif zombie.x < others.x:
                    zombie.x -= zombie.speed
                if zombie.y < others.y:
                    zombie.y -= zombie.speed
                elif zombie.y > others.y:
                    zombie.y += zombie.speed
        if player_damage:
            register_player_damage(zombie)

def draw_zombies():
    global zombie_array
    for zombie in zombie_array:
        draw.circle(screen, zombie.color, (zombie.x, zombie.y), zombie.radius)

def handle_damage_delay():
    global can_take_damage_now
    if can_take_damage_now and window_running:
        def toggle_damage_on():
            global can_take_damage_now
            can_take_damage_now = True
        def toggle_damage_off():
            global can_take_damage_now
            can_take_damage_now = False
            threading.Timer(1, toggle_damage_on).start()
        toggle_damage_off()

def handle_health():
    global game_running
    if player.health < 0:
        player.health = 0
    if player.health == 0:
        game_running = False
        game_over_sound.play()
        
    health = str(player.health)
    healthboard = small_font.render("health: "+health, True, "white")
    screen.blit(healthboard, (30, 30))

def handle_score():
    global score
    scoreboard = small_font.render("score: "+str(score), True, "white")
    screen.blit(scoreboard, (30, 90))

def turn_zombie_damage_animation_off(zombie):
    zombie.animating = False

def fire_bullet_and_handle_damage():
    if not(holding_click and window_running):
        return
    global zombie_array, bullet_array
    mouse_x, mouse_y = mouse.get_pos()
    multiplier = 50000

    dist = distance(player.x, player.y, mouse_x, mouse_y)
    unit_x = (mouse_x - player.x) / dist
    unit_y = (mouse_y - player.y) / dist

    bullet = Bullet(player.x, player.y, unit_x, unit_y)
    bullet_array.append(bullet)
    gun_sound.play()

    for zombie in zombie_array:
        zombie_rect_x = zombie.x - zombie.radius
        zombie_rect_y = zombie.y - zombie.radius
        zombie_rect_length = zombie.radius*2
        zombie_rect = Rect(zombie_rect_x, zombie_rect_y, zombie_rect_length, zombie_rect_length)

        if zombie_rect.clipline((player.x, player.y), (unit_x * multiplier, unit_y * multiplier)):
            zombie.health -= 30
            if not zombie.animating:
                zombie.animating = True
                threading.Timer(0.1, turn_zombie_damage_animation_off, [zombie]).start()

    threading.Timer(0.2, fire_bullet_and_handle_damage).start()

def show_game_over_message():
    if not window_running:
        return
    game_over_message = big_font.render("game over", True, "white")
    MESSAGE_WIDTH, MESSAGE_HEIGHT = game_over_message.get_size()
    center_x_coordinate = WINDOW_WIDTH/2 - MESSAGE_WIDTH/2
    center_y_coordinate = WINDOW_HEIGHT/2 - MESSAGE_HEIGHT/2
    screen.blit(game_over_message, (center_x_coordinate, center_y_coordinate))

def handle_zombie_death():
    global zombie_array, score
    temp_array = []
    for zombie in zombie_array:
        if zombie.health <= 0:
            zombie_death_sound.play()
            score += zombie.speed
        if zombie.health > 0:
            temp_array.append(zombie)

    zombie_array = []
    for zombie in temp_array:
        zombie_array.append(zombie)

def animate_damage():
    for zombie in zombie_array:
        if zombie.animating:
            zombie.color = (255, 200, 200)
        else:
            zombie.color = zombie.perma_color

def draw_bullets():
    global bullet_array
    for bullet in bullet_array:
        draw.circle(screen, bullet.color, (bullet.x, bullet.y), bullet.radius)
        bullet.x += bullet.unit_x * 100
        bullet.y += bullet.unit_y * 100

def walking_animation():
    if not game_running:
        return
    walking_right = holding_d and not holding_a
    walking_left = holding_a and not holding_d
    walking_up = holding_w and not holding_s
    walking_down = holding_s and not holding_w

    if walking_right or walking_left or walking_up or walking_down:
        if ascent:
            player.y -= 1
        if descent:
            player.y += 1

def flip_walking_animation():
    if not window_running:
        return
    global ascent, descent
    ascent, descent = not ascent, not descent
    threading.Timer(0.1, flip_walking_animation).start()

decrease_time_between_zombie_spawn()
spawn_zombie()
flip_walking_animation()
update_follow_point()

while window_running:
    for e in event.get():
        if e.type == QUIT:
            window_running = False
        if e.type == KEYDOWN:
            if e.key == K_w:
                holding_w = True
            if e.key == K_s:
                holding_s = True
            if e.key == K_d:
                holding_d = True
            if e.key == K_a:
                holding_a = True
        if e.type == KEYUP:
            if e.key == K_w:
                holding_w = False
            if e.key == K_s:
                holding_s = False
            if e.key == K_d:
                holding_d = False
            if e.key == K_a:
                holding_a = False
        if e.type == MOUSEBUTTONDOWN:
            holding_click = True
            fire_bullet_and_handle_damage()
        if e.type == MOUSEBUTTONUP:
            holding_click = False

    draw_map()
    if game_running:
        handle_player_movement()
        prevent_boundary_escape()
        walking_animation()
        draw_bullets()
        draw_player()
        zombie_movement()
        draw_zombies()
        handle_zombie_death()
        animate_damage()
        handle_health()
        handle_score()
    if not game_running:
        show_game_over_message()

    clock.tick(FRAMES)
    display.update()
