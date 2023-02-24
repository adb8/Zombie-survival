from pygame import *
from pygame import mixer
import math
import threading
import random

init()
screen = display.set_mode()

WINDOW_WIDTH, WINDOW_HEIGHT = screen.get_size()
FPS = 60

score = 0
time_between_spawns = 2
can_take_damage_now = True

ascent, descent = True, False
game_running, window_running = True, True
zombie_array, other_array, another_other_array, bullet_array = [], [], [], []
holdw, holds, holdd, holda, holdclick = False, False, False, False, False

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

    def __init__(self, x, y, start_x, start_y, unit_x, unit_y):

        self.x = x
        self.y = y
        self.start_x = start_x
        self.start_y = start_y
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
        self.follow_x = 0
        self.follow_y = 0

class Zombie:

    def __init__(self, x, y, radius, color, speed, health, damage, difficulty):

        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.color = color
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

def player_movement_and_boundaries():

    if holda and not holdd:
        player.x -= player.speed
    if holdd and not holda:
        player.x += player.speed
    if holdw and not holds:
        player.y -= player.speed
    if holds and not holdw:
        player.y += player.speed

    if player.x > WINDOW_WIDTH - player.radius:
        player.x = WINDOW_WIDTH - player.radius
    if player.x < 0 + player.radius:
        player.x = player.radius
    if player.y > WINDOW_HEIGHT - player.radius:
        player.y = WINDOW_HEIGHT - player.radius
    if player.y < 0 + player.radius:
        player.y = player.radius

def decrease_spawn_time():

    if window_running:
        global time_between_spawns
        time_between_spawns *= 0.95
        time = threading.Timer(5, decrease_spawn_time)
        time.start()

def spawn_zombie():

    if not window_running:
        return

    global zombie_array, time_between_spawns

    def get_random_x():
        return random.randint(0, WINDOW_WIDTH)

    def get_random_y():
        return random.randint(0, WINDOW_WIDTH)

    def get_random_difficulty():
        difficulty = random.choice(["easy", "medium", "hard"])
        return difficulty

    difficulty = get_random_difficulty()

    if difficulty == "easy":

        radius = 25
        speed = 1
        color = (255, 100, 100)
        health = 50
        damage = 10
        difficulty = "easy"

    if difficulty == "medium":

        radius = 32
        speed = 2
        color = (255, 70, 70)
        health = 100
        damage = 15
        difficulty = "medium"

    if difficulty == "hard":

        radius = 40
        speed = 3
        color = (255, 40, 40)
        health = 150
        damage = 25
        difficulty = "hard"

    def do_coords_collide(x, y):

        another_other_array = []
        for i in zombie_array:
            another_other_array.append(i)
        another_other_array.append(player)

        for i in another_other_array:
            if find_distance(x, y, i.x, i.y) < i.radius + radius + 20:
                return False

    random_x = get_random_x()
    random_y = get_random_y()

    while do_coords_collide(random_x, random_y) == False:
        random_x = get_random_x()
        random_y = get_random_y()

    zombie = Zombie(x=random_x, y=random_y, radius=radius, color=color, speed=speed, health=health, damage=damage, difficulty=difficulty)
    zombie_array.append(zombie)

    time = threading.Timer(time_between_spawns, spawn_zombie)
    time.start()

def find_distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def register_player_damage(zombie):

    if window_running:

        def change_player_color_back():
            player.color = (0, 200, 0)

        if can_take_damage_now:
            player.health -= zombie.damage
            damage_sound.play()
            player.color = (150, 200, 150)
            time = threading.Timer(0.1, change_player_color_back)
            time.start()

        handle_damage_delay()

def update_follow_point():

    if window_running:

        player.follow_x = player.x
        player.follow_y = player.y

        time = threading.Timer(0.25, update_follow_point)
        time.start()

def zombie_movement():

    global zombie_array, other_array

    for i in zombie_array:

        other_array = []
        for j in zombie_array:
            if j != i:
                other_array.append(j)
        other_array.append(player)

        if i.x > player.follow_x:
            i.x -= i.speed

            for j in other_array:
                if find_distance(i.x, i.y, j.x, j.y) < i.radius + j.radius:
                    i.x += i.speed

                    if j == player:
                        register_player_damage(i)

        if i.x < player.follow_x:
            i.x += i.speed

            for j in other_array:
                if find_distance(i.x, i.y, j.x, j.y) < i.radius + j.radius:
                    i.x -= i.speed

                    if j == player:
                        register_player_damage(i)

        if i.y < player.follow_y:
            i.y += i.speed

            for j in other_array:
                if find_distance(i.x, i.y, j.x, j.y) < i.radius + j.radius:
                    i.y -= i.speed

                    if j == player:
                        register_player_damage(i)

        if i.y > player.follow_y:
            i.y -= i.speed

            for j in other_array:
                if find_distance(i.x, i.y, j.x, j.y) < i.radius + j.radius:
                    i.y += i.speed

                    if j == player:
                        register_player_damage(i)

def draw_zombies():

    global zombie_array
    for i in zombie_array:
        draw.circle(screen, i.color, (i.x, i.y), i.radius)

def handle_damage_delay():

    global can_take_damage_now
    if can_take_damage_now and window_running:

        def toggle_damage_on():
            global can_take_damage_now
            can_take_damage_now = True

        def toggle_damage_off():
            global can_take_damage_now
            can_take_damage_now = False
            time = threading.Timer(1, toggle_damage_on)
            time.start()

        toggle_damage_off()

def handle_health():

    global game_running

    if player.health < 0:
        player.health = 0

    if player.health == 0:
        game_running = False
        game_over_sound.play()

    healthboard = small_font.render("health: "+str(player.health), True, "white")
    screen.blit(healthboard, (30, 30))

def handle_score():

    global score
    scoreboard = small_font.render("score: "+str(score), True, "white")
    screen.blit(scoreboard, (30, 90))

def fire_gun():

    if holdclick and window_running:

        global zombie_array, bullet_array
        mouse_x, mouse_y = mouse.get_pos()

        distance = find_distance(player.x, player.y, mouse_x, mouse_y)
        unit_x = (mouse_x - player.x) / distance
        unit_y = (mouse_y - player.y) / distance

        bullet = Bullet(player.x, player.y, player.x, player.y, unit_x, unit_y)
        bullet_array.append(bullet)
        gun_sound.play()

        for i in zombie_array:

            zombie_rect = Rect(i.x - i.radius, i.y - i.radius, i.radius*2, i.radius*2)
            if zombie_rect.clipline((player.x, player.y), (unit_x * 50000, unit_y * 50000)):
                i.health -= 30

                if not i.animating:

                    i.animating = True
                    def animate_damage_off(zombie):
                        zombie.animating = False

                    time = threading.Timer(0.1, animate_damage_off, [i])
                    time.start()

        time = threading.Timer(0.2, fire_gun)
        time.start()

def show_game_over():

    if window_running:
        game_over_message = big_font.render("game over", True, "white")
        MESSAGE_WIDTH, MESSAGE_HEIGHT = game_over_message.get_size()
        screen.blit(game_over_message, (WINDOW_WIDTH/2 - MESSAGE_WIDTH/2, WINDOW_HEIGHT/2 - MESSAGE_HEIGHT/2))

def handle_zombie_death():

    global zombie_array, score
    temp_array = []

    for i in zombie_array:

        if i.health <= 0:

            zombie_death_sound.play()
            if i.difficulty == "easy":
                score += 1
            if i.difficulty == "medium":
                score += 2
            if i.difficulty == "hard":
                score += 3

        if i.health > 0:
            temp_array.append(i)

    zombie_array = []
    for i in temp_array:
        zombie_array.append(i)

def animate_damage():

    for i in zombie_array:

        if i.animating:
            i.color = (255, 200, 200)

        else:
            if i.difficulty == "easy":
                i.color = (255, 130, 130)
            elif i.difficulty == "medium":
                i.color = (255, 100, 100)
            elif i.difficulty == "hard":
                i.color = (255, 70, 70)

def draw_bullets():

    global bullet_array
    for i in bullet_array:
        draw.circle(screen, i.color, (i.x, i.y), i.radius)
        i.x += i.unit_x * 100
        i.y += i.unit_y * 100

def walking_animation():

    if game_running:

        walking_right = holdd and not holda
        walking_left = holda and not holdd
        walking_up = holdw and not holds
        walking_down = holds and not holdw

        if walking_right or walking_left or walking_up or walking_down:

            if ascent:
                player.y -= 1
            if descent:
                player.y += 1

def walking_animation_flip():

    global ascent, descent
    ascent = not ascent
    descent = not descent

    if window_running:

        time = threading.Timer(0.1, walking_animation_flip)
        time.start()

decrease_spawn_time()
spawn_zombie()
walking_animation_flip()
update_follow_point()

while window_running:

    for e in event.get():

        if e.type == QUIT:
            window_running = False

        if e.type == KEYDOWN:
            if e.key == K_w:
                holdw = True
            if e.key == K_s:
                holds = True
            if e.key == K_d:
                holdd = True
            if e.key == K_a:
                holda = True

        if e.type == KEYUP:
            if e.key == K_w:
                holdw = False
            if e.key == K_s:
                holds = False
            if e.key == K_d:
                holdd = False
            if e.key == K_a:
                holda = False

        if e.type == MOUSEBUTTONDOWN:
            holdclick = True
            if game_running:
                fire_gun()
        if e.type == MOUSEBUTTONUP:
            holdclick = False

    draw_map()

    if game_running:

        player_movement_and_boundaries()

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

        show_game_over()

    clock.tick(FPS)
    display.update()
