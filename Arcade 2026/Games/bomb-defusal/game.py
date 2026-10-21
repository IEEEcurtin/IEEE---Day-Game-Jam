import os
import sys
import pygame
import time
import random
import serial

# Arcade helpers (controller auto-detect, full screen, scores). The game still
# runs on its own if the arcade folder is missing.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "system", "pylib"))
try:
    import arcade_mode
except ImportError:
    arcade_mode = None

ARCADE = arcade_mode is not None and arcade_mode.ACTIVE

# Start Pygame
pygame.init()

# -----------------------------
# SOUND EFFECTS
# -----------------------------

pygame.mixer.init()

# Sounds are found next to this file, so the game runs from any folder
SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sounds")

click_sound = pygame.mixer.Sound(
    os.path.join(SOUND_DIR, "menu_click.mp3")
)

correct_sound = pygame.mixer.Sound(
    os.path.join(SOUND_DIR, "correct_beep.mp3")
)

wrong_sound = pygame.mixer.Sound(
    os.path.join(SOUND_DIR, "wrong_sound.mp3")
)

warning_sound = pygame.mixer.Sound(
    os.path.join(SOUND_DIR, "warning_beep.mp3")
)

win_sound = pygame.mixer.Sound(
    os.path.join(SOUND_DIR, "completion_win.mp3")
)
lose_sound = pygame.mixer.Sound(
    os.path.join(SOUND_DIR, "completion_lose.mp3")
)

# -----------------------------
# ESP32 SERIAL CONNECTION
# -----------------------------

SERIAL_BAUD = 115200

# The ESP32 is found automatically on whichever USB port it is plugged into
if arcade_mode is not None:

    ser = arcade_mode.open_controller(SERIAL_BAUD)

else:

    ser = None

if ser is None:

    print("ESP32 not connected.")
    print("Keyboard controls can still be used.")

# -----------------------------
# WINDOW
# -----------------------------

WIDTH = 900
HEIGHT = 600

if arcade_mode is not None:

    screen = arcade_mode.open_window((WIDTH, HEIGHT), "DON'T PRESS THAT!")

else:

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("DON'T PRESS THAT!")

# -----------------------------
# COLOURS
# -----------------------------

BLACK = (15, 15, 18)
DARK_GREY = (30, 30, 35)
PANEL_GREY = (45, 45, 50)
GREY = (100, 100, 100)
LIGHT_GREY = (160, 160, 160)

WHITE = (245, 245, 245)

RED = (220, 50, 50)
DARK_RED = (110, 25, 25)

BLUE = (50, 100, 220)
DARK_BLUE = (25, 50, 110)

GREEN = (50, 180, 80)
DARK_GREEN = (25, 90, 40)

YELLOW = (240, 200, 50)
ORANGE = (230, 120, 30)

# -----------------------------
# FONTS
# -----------------------------

title_font = pygame.font.Font(None, 60)
big_font = pygame.font.Font(None, 45)
font = pygame.font.Font(None, 32)
small_font = pygame.font.Font(None, 25)
hint_font = pygame.font.Font(None, 20)

# -----------------------------
# BUTTON SETTINGS
# -----------------------------

button_width = 240
button_height = 60

button_x = (WIDTH - button_width) // 2
button_y = 400

# -----------------------------
# KEYPAD SETTINGS
# -----------------------------

KEYPAD_KEYS = [
    "1", "2", "3", "A",
    "4", "5", "6", "B",
    "7", "8", "9", "C",
    "*", "0", "#", "D"
]

KEYPAD_COLS = 4
KEYPAD_ROWS = 4

# -----------------------------
# GAME SETTINGS
# -----------------------------

STARTING_LIVES = 3

LEVEL_1_TIME = 35
LEVEL_2_TIME = 25

level = 1
lives = STARTING_LIVES

game_time = LEVEL_1_TIME

start_time = time.time()

time_left = game_time

# -----------------------------
# GAME STATES
# -----------------------------

game_over = False
game_won = False

# Used for timer warning sound
last_warning_time = -1

# Used for the arcade leaderboard
tasks_cleared = 0

# -----------------------------
# MENU STATES
# -----------------------------

game_started = False
show_how_to_play = False

# -----------------------------
# COMMENTARY SETTINGS
# -----------------------------

MESSAGE_DURATION = 1.25

message = "Good luck. You're going to need it."

message_started_at = time.time()

# -----------------------------
# TASK GENERATOR
# -----------------------------

def create_tasks(current_level):

    normal_tasks = [
        {
            "type": "PRESS",
            "input": "RED",
            "text": "PRESS RED"
        },
        {
            "type": "PRESS",
            "input": "BLUE",
            "text": "PRESS BLUE"
        },
        {
            "type": "PRESS",
            "input": "GREEN",
            "text": "PRESS GREEN"
        },
        {
            "type": "KEYPAD",
            "input": "KEY_" + random.choice(KEYPAD_KEYS),
            "text": ""
        },
        {
            "type": "KEYPAD",
            "input": "KEY_" + random.choice(KEYPAD_KEYS),
            "text": ""
        }
    ]

    selected_normal_tasks = random.sample(
        normal_tasks,
        5
    )

    for task in selected_normal_tasks:

        if task["type"] == "KEYPAD":

            task["text"] = (
                "PRESS KEYPAD "
                + task["input"].replace("KEY_", "")
            )

    # -----------------------------
    # DON'T PRESS TASK
    # -----------------------------

    wait_task = {
        "type": "WAIT",
        "duration": 3,
        "text": "DON'T PRESS ANYTHING!"
    }

    # -----------------------------
    # POSSIBLE COLOUR INPUTS
    # -----------------------------

    possible_inputs = [
        "RED",
        "BLUE",
        "GREEN"
    ]

    # -----------------------------
    # SEQUENCE TASK
    # -----------------------------

    sequence_length = 3

    if current_level == 2:
        sequence_length = 4

    sequence = []

    for i in range(sequence_length):

        sequence.append(
            random.choice(possible_inputs)
        )

    sequence_task = {
        "type": "SEQUENCE",
        "sequence": sequence,
        "text": " -> ".join(sequence)
    }

    # -----------------------------
    # MISDIRECTION TASKS
    # -----------------------------

    misdirection_tasks = [
        {
            "type": "MISDIRECTION",
            "input": None,
            "duration": 4,
            "text": "PRESS RED OR ACTUALLY DON'T :)"
        },
        {
            "type": "MISDIRECTION",
            "input": "GREEN",
            "duration": 4,
            "text": "PRESS BLUE. WAIT. NO. PRESS GREEN."
        },
        {
            "type": "MISDIRECTION",
            "input": "RED",
            "duration": 4,
            "text": "DO NOT PRESS GREEN. PRESS RED."
        },
        {
            "type": "MISDIRECTION",
            "input": "KEY_7",
            "duration": 4,
            "text": "PRESS 2. NO. PRESS 7."
        },
        {
            "type": "MISDIRECTION",
            "input": "KEY_A",
            "duration": 4,
            "text": "DO NOT PRESS A. ACTUALLY... PRESS A."
        },
        {
            "type": "MISDIRECTION",
            "input": "BLUE",
            "duration": 4,
            "text": "PRESS BLUE IF YOU ACTUALLY READ THIS."
        }
    ]

    misdirection_task = random.choice(
        misdirection_tasks
    )

    # -----------------------------
    # BUILD LEVEL 1
    # -----------------------------

    if current_level == 1:

        new_tasks = selected_normal_tasks + [
            wait_task,
            sequence_task,
            misdirection_task
        ]

    # -----------------------------
    # BUILD LEVEL 2
    # -----------------------------

    else:

        second_wait_task = {
            "type": "WAIT",
            "duration": 2,
            "text": "DON'T PRESS ANYTHING!"
        }

        sequence_2 = []

        for i in range(4):

            sequence_2.append(
                random.choice(possible_inputs)
            )

        sequence_task_2 = {
            "type": "SEQUENCE",
            "sequence": sequence_2,
            "text": " -> ".join(sequence_2)
        }

        misdirection_task_2 = random.choice(
            misdirection_tasks
        )

        new_tasks = selected_normal_tasks + [
            wait_task,
            second_wait_task,
            sequence_task,
            sequence_task_2,
            misdirection_task,
            misdirection_task_2
        ]

    # -----------------------------
    # RANDOMIZE TASK ORDER
    # -----------------------------

    random.shuffle(new_tasks)

    return new_tasks


# -----------------------------
# CREATE FIRST LEVEL
# -----------------------------

tasks = create_tasks(level)

task_number = 0

task_started_at = time.time()

sequence_position = 0


# -----------------------------
# FUNCTIONS
# -----------------------------

def draw_text(text, font_used, colour, x, y):

    surface = font_used.render(
        text,
        True,
        colour
    )

    screen.blit(
        surface,
        (x, y)
    )


def draw_centered_text(text, font_used, colour, y):

    surface = font_used.render(
        text,
        True,
        colour
    )

    text_rect = surface.get_rect(
        center=(WIDTH // 2, y)
    )

    screen.blit(
        surface,
        text_rect
    )


def draw_button(text, x, y, width, height):

    mouse_position = pygame.mouse.get_pos()

    button_rect = pygame.Rect(
        x,
        y,
        width,
        height
    )

    if button_rect.collidepoint(mouse_position):

        button_colour = BLUE

    else:

        button_colour = GREY

    pygame.draw.rect(
        screen,
        button_colour,
        button_rect
    )

    pygame.draw.rect(
        screen,
        WHITE,
        button_rect,
        2
    )

    text_surface = small_font.render(
        text,
        True,
        WHITE
    )

    text_rect = text_surface.get_rect(
        center=button_rect.center
    )

    screen.blit(
        text_surface,
        text_rect
    )

    return button_rect


def draw_start_screen():

    screen.fill(BLACK)

    pygame.draw.rect(
        screen,
        DARK_GREY,
        (20, 20, 860, 560)
    )

    pygame.draw.rect(
        screen,
        LIGHT_GREY,
        (20, 20, 860, 560),
        2
    )

    draw_warning_stripes(
        20,
        20,
        860,
        12
    )

    draw_centered_text(
        "DON'T PRESS THAT!",
        title_font,
        WHITE,
        90
    )

    draw_centered_text(
        "A COMPLETELY UNNECESSARY TEST OF YOUR ABILITY",
        small_font,
        LIGHT_GREY,
        145
    )

    draw_centered_text(
        "TO FOLLOW INSTRUCTIONS.",
        small_font,
        LIGHT_GREY,
        170
    )

    draw_panel(
        180,
        205,
        540,
        95
    )

    draw_warning_light(
        205,
        220
    )

    draw_warning_light(
        695,
        220
    )

    draw_centered_text(
        "SYSTEM STATUS: EXTREMELY CONCERNING",
        font,
        RED,
        255
    )

    draw_button(
        "START GAME",
        330,
        330,
        240,
        60
    )

    draw_button(
        "HOW TO PLAY",
        330,
        405,
        240,
        60
    )

    draw_centered_text(
        "WARNING: FOLLOW THE INSTRUCTIONS. PROBABLY.",
        small_font,
        YELLOW,
        525
    )


def draw_how_to_play_screen():

    screen.fill(BLACK)

    pygame.draw.rect(
        screen,
        DARK_GREY,
        (20, 20, 860, 560)
    )

    pygame.draw.rect(
        screen,
        LIGHT_GREY,
        (20, 20, 860, 560),
        2
    )

    draw_warning_stripes(
        20,
        20,
        860,
        12
    )

    draw_centered_text(
        "HOW TO PLAY",
        title_font,
        WHITE,
        75
    )

    draw_panel(
        100,
        125,
        700,
        275
    )

    draw_centered_text(
        "READ THE INSTRUCTION.",
        font,
        WHITE,
        160
    )

    draw_centered_text(
        "USE THE PHYSICAL CONTROL PANEL.",
        font,
        WHITE,
        205
    )

    draw_centered_text(
        "PRESS THE CORRECT BUTTON OR KEYPAD KEY.",
        small_font,
        LIGHT_GREY,
        245
    )

    draw_centered_text(
        "SOMETIMES YOU MUST WAIT.",
        small_font,
        YELLOW,
        280
    )

    draw_centered_text(
        "SOMETIMES THE INSTRUCTION LIES.",
        small_font,
        RED,
        315
    )

    draw_centered_text(
        "SOMETIMES YOU MUST FOLLOW A SEQUENCE.",
        small_font,
        GREEN,
        350
    )

    draw_centered_text(
        "YOU HAVE 3 LIVES.",
        font,
        WHITE,
        430
    )

    draw_centered_text(
        "DON'T PANIC.",
        big_font,
        RED,
        465
    )

    draw_button(
        "BACK",
        210,
        500,
        220,
        50
    )

    draw_button(
        "START GAME",
        470,
        500,
        220,
        50
    )


def draw_panel(x, y, width, height):

    pygame.draw.rect(
        screen,
        PANEL_GREY,
        (x, y, width, height)
    )

    pygame.draw.rect(
        screen,
        LIGHT_GREY,
        (x, y, width, height),
        2
    )

    screw_positions = [
        (x + 10, y + 10),
        (x + width - 10, y + 10),
        (x + 10, y + height - 10),
        (x + width - 10, y + height - 10)
    ]

    for screw_x, screw_y in screw_positions:

        pygame.draw.circle(
            screen,
            GREY,
            (screw_x, screw_y),
            4
        )

        pygame.draw.circle(
            screen,
            DARK_GREY,
            (screw_x, screw_y),
            2
        )


def draw_warning_stripes(x, y, width, height):

    stripe_width = 16

    for stripe_x in range(
        x - height,
        x + width,
        stripe_width * 2
    ):

        points = [
            (stripe_x, y),
            (stripe_x + stripe_width, y),
            (stripe_x + stripe_width + height, y + height),
            (stripe_x + height, y + height)
        ]

        pygame.draw.polygon(
            screen,
            YELLOW,
            points
        )


def draw_warning_light(x, y, active=True):

    if active:

        pygame.draw.circle(
            screen,
            RED,
            (x, y),
            9
        )

        pygame.draw.circle(
            screen,
            (255, 100, 100),
            (x - 3, y - 3),
            3
        )

    else:

        pygame.draw.circle(
            screen,
            DARK_RED,
            (x, y),
            9
        )


def draw_control_button(x, y, colour, label):

    pygame.draw.circle(
        screen,
        DARK_GREY,
        (x, y),
        32
    )

    pygame.draw.circle(
        screen,
        colour,
        (x, y),
        25
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (x - 7, y - 7),
        5
    )

    draw_text(
        label,
        small_font,
        WHITE,
        x - 20,
        y + 43
    )


def draw_keypad(x, y):

    key_size = 28
    gap = 7

    keypad_width = (key_size * 4) + (gap * 3)
    keypad_height = (key_size * 4) + (gap * 3)

    pygame.draw.rect(
        screen,
        DARK_GREY,
        (
            x - 10,
            y - 10,
            keypad_width + 20,
            keypad_height + 20
        )
    )

    pygame.draw.rect(
        screen,
        LIGHT_GREY,
        (
            x - 10,
            y - 10,
            keypad_width + 20,
            keypad_height + 20
        ),
        2
    )

    for row in range(4):

        for col in range(4):

            index = row * 4 + col

            key = KEYPAD_KEYS[index]

            key_x = x + col * (key_size + gap)
            key_y = y + row * (key_size + gap)

            key_rect = pygame.Rect(
                key_x,
                key_y,
                key_size,
                key_size
            )

            pygame.draw.rect(
                screen,
                PANEL_GREY,
                key_rect
            )

            pygame.draw.rect(
                screen,
                WHITE,
                key_rect,
                1
            )

            text_surface = small_font.render(
                key,
                True,
                WHITE
            )

            text_rect = text_surface.get_rect(
                center=key_rect.center
            )

            screen.blit(
                text_surface,
                text_rect
            )


def draw_status_panel():

    draw_panel(
        50,
        90,
        800,
        90
    )

    draw_warning_light(65, 115)
    draw_warning_light(65, 150)

    draw_text(
        "SYSTEM STATUS",
        small_font,
        LIGHT_GREY,
        100,
        105
    )

    if level == 1:

        status_text = "UNSTABLE"

    else:

        status_text = "CRITICAL"

    draw_text(
        status_text,
        big_font,
        RED,
        100,
        125
    )

    draw_text(
        "LIVES: " + str(lives),
        font,
        RED,
        650,
        115
    )

    draw_text(
        "LEVEL " + str(level),
        font,
        YELLOW,
        650,
        145
    )


def draw_control_panel():

    draw_panel(
        50,
        195,
        800,
        250
    )

    pygame.draw.rect(
        screen,
        DARK_GREY,
        (50, 425, 800, 20)
    )

    draw_warning_stripes(
        50,
        425,
        800,
        20
    )

    draw_control_button(
        155,
        425,
        RED,
        "RED"
    )

    draw_control_button(
        285,
        425,
        BLUE,
        "BLUE"
    )

    draw_control_button(
        415,
        425,
        GREEN,
        "GREEN"
    )

    draw_keypad(
        640,
        360
    )

    draw_text(
        "KEYPAD",
        small_font,
        WHITE,
        555,
        420
    )


def read_esp32_input():

    if ser is None:

        return None

    if ser.in_waiting > 0:

        input_data = ser.readline().decode(
            errors="ignore"
        ).strip().upper()

        valid_inputs = [
            "RED",
            "BLUE",
            "GREEN"
        ]

        if input_data in valid_inputs:

            return input_data

        if input_data.startswith("KEY_"):

            keypad_key = input_data[4:]

            if keypad_key in KEYPAD_KEYS:

                return input_data

    return None


def show_message(new_message):

    global message
    global message_started_at

    message = new_message
    message_started_at = time.time()


def start_level_2():

    global level
    global lives
    global game_time
    global start_time
    global time_left
    global tasks
    global task_number
    global task_started_at
    global sequence_position
    global message
    global last_warning_time

    level = 2

    lives = STARTING_LIVES

    game_time = LEVEL_2_TIME

    start_time = time.time()

    time_left = game_time

    # Reset warning sound timer
    last_warning_time = -1

    tasks = create_tasks(level)

    task_number = 0

    task_started_at = time.time()

    sequence_position = 0

    show_message(
        "THE TIMER IS TICKING FASTER. GOOD LUCK."
    )


def reset_game():

    global level
    global lives
    global game_time
    global start_time
    global time_left
    global game_over
    global game_won
    global tasks
    global task_number
    global task_started_at
    global sequence_position
    global message
    global last_warning_time
    global tasks_cleared

    level = 1

    tasks_cleared = 0

    lives = STARTING_LIVES

    game_time = LEVEL_1_TIME

    start_time = time.time()

    time_left = game_time

    # Reset warning sound timer
    last_warning_time = -1

    tasks = create_tasks(level)

    task_number = 0

    task_started_at = time.time()

    sequence_position = 0

    game_over = False
    game_won = False

    show_message(
        "Good luck. You're going to need it."
    )


def advance_task():

    global task_number
    global task_started_at
    global sequence_position
    global game_won
    global message
    global tasks_cleared

    tasks_cleared += 1

    task_number += 1

    sequence_position = 0

    task_started_at = time.time()

    if task_number >= len(tasks):

        if level == 1:

            start_level_2()

        else:

            game_won = True

            win_sound.play()

            message = "YOU ACTUALLY DEFUSED IT."


def final_score():

    # 100 points per instruction cleared. Defusing the bomb adds
    # 10 points per second left and 100 per life left.
    score = tasks_cleared * 100

    if game_won:

        score += time_left * 10 + lives * 100

    return score


def handle_input(player_input):

    global lives
    global game_over
    global message
    global sequence_position

    # Every button/key press makes a click sound
    click_sound.play()

    current_task = tasks[task_number]

    # -----------------------------
    # WAIT TASK
    # -----------------------------

    if current_task["type"] == "WAIT":

        wrong_sound.play()

        lives -= 1

        show_message(
            "WRONG! I SAID DO NOTHING!"
        )

        if lives <= 0:

            game_over = True

            show_message(
                "YOU PRESSED SOMETHING. MISSION FAILED."
            )

        return

    # -----------------------------
    # MISDIRECTION TASK
    # -----------------------------

    if current_task["type"] == "MISDIRECTION":

        required_input = current_task["input"]

        if required_input is None:

            wrong_sound.play()

            lives -= 1

            show_message(
                "HAHA. YOU FELL FOR IT."
            )

            if lives <= 0:

                game_over = True

                lose_sound.play()

                show_message(
                    "TOO MANY MISTAKES."
                )

            return

        if player_input == required_input:

            correct_sound.play()

            show_message(
                "YOU ACTUALLY READ IT."
            )

            advance_task()

        else:

            wrong_sound.play()

            lives -= 1

            show_message(
                "WRONG! READ THE WHOLE THING!"
            )

            if lives <= 0:

                game_over = True

                show_message(
                    "TOO MANY MISTAKES."
                )

        return

    # -----------------------------
    # SEQUENCE TASK
    # -----------------------------

    if current_task["type"] == "SEQUENCE":

        sequence = current_task["sequence"]

        required_input = sequence[sequence_position]

        if player_input == required_input:

            sequence_position += 1

            if sequence_position >= len(sequence):

                correct_sound.play()

                show_message(
                    "SEQUENCE COMPLETE!"
                )

                advance_task()

            else:

                correct_sound.play()

                show_message(
                    "GOOD! NOW PRESS "
                    + sequence[sequence_position]
                )

        else:

            wrong_sound.play()

            lives -= 1

            sequence_position = 0

            show_message(
                "WRONG ORDER! SEQUENCE RESET!"
            )

            if lives <= 0:

                game_over = True

                show_message(
                    "TOO MANY MISTAKES."
                )

        return

    # -----------------------------
    # NORMAL PRESS TASK
    # -----------------------------

    required_input = current_task["input"]

    if player_input == required_input:

        correct_sound.play()

        show_message(
            "CORRECT! SURPRISINGLY COMPETENT."
        )

        advance_task()

    else:

        wrong_sound.play()

        lives -= 1

        show_message(
            "WRONG! WHY WOULD YOU PRESS THAT?!"
        )

        if lives <= 0:

            game_over = True

            show_message(
                "TOO MANY MISTAKES."
            )


# -----------------------------
# MAIN GAME LOOP
# -----------------------------

play_again_button = pygame.Rect(
    button_x,
    button_y,
    button_width,
    button_height
)

start_button = pygame.Rect(
    330,
    330,
    240,
    60
)

how_to_play_button = pygame.Rect(
    330,
    405,
    240,
    60
)

back_button = pygame.Rect(
    330,
    470,
    240,
    60
)

running = True

clock = pygame.time.Clock()

# In the arcade the How to Play screen is shown before the game opens,
# so skip the menu and go straight into the bomb
if ARCADE:

    session = arcade_mode.Session()

    reset_game()
    game_started = True

ended_at = None

while running:

    clock.tick(60)

    # -----------------------------
    # ESP32 INPUT
    # -----------------------------

    esp32_input = read_esp32_input()

    if esp32_input is not None:

        if ARCADE:

            session.note_input()

        if game_started and not game_over and not game_won:

            handle_input(esp32_input)

    # -----------------------------
    # EVENTS
    # -----------------------------

    for event in pygame.event.get():

        if ARCADE:

            session.handle_event(event)

            # Esc is handled by holding it (see arcade_mode), and the arcade
            # decides when to play again, so these do nothing here
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):

                continue

            if event.type == pygame.MOUSEBUTTONDOWN:

                continue

        if event.type == pygame.QUIT:

            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                if not game_started and not show_how_to_play:

                    if start_button.collidepoint(event.pos):

                        reset_game()
                        game_started = True

                    elif how_to_play_button.collidepoint(event.pos):

                        show_how_to_play = True

                elif show_how_to_play:

                    if back_button.collidepoint(event.pos):

                        show_how_to_play = False

                    elif start_button.collidepoint(event.pos):

                        reset_game()
                        game_started = True
                        show_how_to_play = False

                elif game_over or game_won:

                    if play_again_button.collidepoint(event.pos):

                        reset_game()
                        game_started = True

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                running = False

            elif event.key == pygame.K_RETURN:

                if game_over or game_won:

                    reset_game()
                    game_started = True

            elif game_started and not game_over and not game_won:

                if event.key == pygame.K_r:

                    handle_input("RED")

                elif event.key == pygame.K_b:

                    handle_input("BLUE")

                elif event.key == pygame.K_g:

                    handle_input("GREEN")

                elif event.key == pygame.K_0:

                    handle_input("KEY_0")

                elif event.key == pygame.K_1:

                    handle_input("KEY_1")

                elif event.key == pygame.K_2:

                    handle_input("KEY_2")

                elif event.key == pygame.K_3:

                    handle_input("KEY_3")

                elif event.key == pygame.K_4:

                    handle_input("KEY_4")

                elif event.key == pygame.K_5:

                    handle_input("KEY_5")

                elif event.key == pygame.K_6:

                    handle_input("KEY_6")

                elif event.key == pygame.K_7:

                    handle_input("KEY_7")

                elif event.key == pygame.K_8:

                    handle_input("KEY_8")

                elif event.key == pygame.K_9:

                    handle_input("KEY_9")

                elif event.key == pygame.K_a:

                    handle_input("KEY_A")

                elif event.key == pygame.K_v:

                    handle_input("KEY_B")

                elif event.key == pygame.K_c:

                    handle_input("KEY_C")

                elif event.key == pygame.K_d:

                    handle_input("KEY_D")

                elif event.key == pygame.K_s:

                    handle_input("KEY_*")

                elif event.key == pygame.K_h:

                    handle_input("KEY_#")

    # -----------------------------
    # GAME TIMER
    # -----------------------------

    if game_started and not game_over and not game_won:

        elapsed_time = time.time() - start_time

        time_left = game_time - int(elapsed_time)

        if time_left <= 0:

            time_left = 0

            game_over = True

            lose_sound.play()

            show_message(
                "TIME'S UP! HR WOULD LIKE A WORD...IF THEY SURVIVED."
            )

        # -----------------------------
        # TIMER WARNING SOUND
        # -----------------------------

        if time_left <= 5 and time_left > 0:

            if time_left != last_warning_time:

                warning_sound.play()

                last_warning_time = time_left

    # -----------------------------
    # WAIT / MISDIRECTION TASKS
    # -----------------------------

    if not game_over and not game_won:

        current_task = tasks[task_number]

        if current_task["type"] == "WAIT":

            wait_time = time.time() - task_started_at

            if wait_time >= current_task["duration"]:

                show_message(
                    "YOU DID NOTHING. AMAZING."
                )

                advance_task()

        elif current_task["type"] == "MISDIRECTION":

            wait_time = time.time() - task_started_at

            if (
                current_task["input"] is None
                and wait_time >= current_task["duration"]
            ):

                show_message(
                    "YOU READ THE WHOLE THING. IMPRESSIVE."
                )

                advance_task()

    # -----------------------------
    # DRAW SCREEN
    # -----------------------------

    if not game_started:

        if show_how_to_play:

            draw_how_to_play_screen()

        else:

            draw_start_screen()

    else:

        screen.fill(BLACK)

        pygame.draw.rect(
            screen,
            DARK_GREY,
            (20, 20, 860, 560)
        )

        pygame.draw.rect(
            screen,
            LIGHT_GREY,
            (20, 20, 860, 560),
            2
        )

        # -----------------------------
        # TOP WARNING STRIPE
        # -----------------------------

        draw_warning_stripes(
            20,
            20,
            860,
            10
        )

        # -----------------------------
        # TITLE
        # -----------------------------

        if level == 1:

            draw_centered_text(
                "DON'T PRESS THAT!",
                title_font,
                WHITE,
                55
            )

        else:

            draw_centered_text(
                "DON'T PRESS THAT!!!",
                title_font,
                RED,
                55
            )

        # -----------------------------
        # STATUS PANEL
        # -----------------------------

        draw_panel(
            50,
            90,
            800,
            75
        )

        draw_warning_light(
            70,
            115
        )

        draw_warning_light(
            70,
            145
        )

        draw_text(
            "SYSTEM STATUS",
            small_font,
            LIGHT_GREY,
            100,
            96
        )

        if level == 1:

            status_text = "UNSTABLE"

        else:

            status_text = "CRITICAL"

        draw_text(
            status_text,
            font,
            RED,
            100,
            121
        )

        # -----------------------------
        # TIMER
        # -----------------------------

        draw_text(
            "TIME",
            small_font,
            LIGHT_GREY,
            390,
            98
        )

        if time_left <= 5:

            timer_colour = RED

        else:

            timer_colour = YELLOW

        draw_text(
            str(time_left),
            big_font,
            timer_colour,
            390,
            115
        )

        # -----------------------------
        # LEVEL / TASK
        # -----------------------------

        draw_text(
            "LEVEL " + str(level),
            small_font,
            LIGHT_GREY,
            500,
            98
        )

        draw_text(
            "TASK "
            + str(task_number + 1)
            + "/"
            + str(len(tasks)),
            font,
            YELLOW,
            500,
            120
        )

        # -----------------------------
        # LIVES
        # -----------------------------

        draw_text(
            "LIVES",
            small_font,
            LIGHT_GREY,
            690,
            98
        )

        for i in range(STARTING_LIVES):

            life_x = 720 + (i * 35)

            if i < lives:

                pygame.draw.circle(
                    screen,
                    RED,
                    (life_x, 130),
                    10
                )

            else:

                pygame.draw.circle(
                    screen,
                    DARK_RED,
                    (life_x, 130),
                    10
                )

        # -----------------------------
        # CURRENT TASK PANEL
        # -----------------------------

        draw_panel(
            50,
            180,
            800,
            155
        )

        draw_centered_text(
            "CURRENT INSTRUCTION",
            small_font,
            LIGHT_GREY,
            205
        )

        if not game_over and not game_won:

            current_task = tasks[task_number]

            if current_task["type"] == "WAIT":

                wait_time = (
                    time.time()
                    - task_started_at
                )

                remaining = (
                    current_task["duration"]
                    - wait_time
                )

                if remaining < 0:

                    remaining = 0

                draw_centered_text(
                    "DON'T PRESS ANYTHING!",
                    big_font,
                    RED,
                    250
                )

                draw_centered_text(
                    "WAIT "
                    + str(round(remaining, 1))
                    + " SECONDS",
                    font,
                    WHITE,
                    295
                )

            elif current_task["type"] == "MISDIRECTION":

                draw_centered_text(
                    current_task["text"],
                    font,
                    WHITE,
                    250
                )

                draw_centered_text(
                    "READ EVERYTHING BEFORE YOU PRESS.",
                    small_font,
                    RED,
                    295
                )

            elif current_task["type"] == "SEQUENCE":

                draw_centered_text(
                    "PRESS IN THIS ORDER:",
                    font,
                    WHITE,
                    245
                )

                draw_centered_text(
                    current_task["text"],
                    big_font,
                    YELLOW,
                    275
                )

                draw_centered_text(
                    "NEXT: "
                    + current_task["sequence"][sequence_position],
                    small_font,
                    GREEN,
                    310
                )

            elif current_task["type"] == "KEYPAD":

                draw_centered_text(
                    "PRESS KEYPAD KEY",
                    small_font,
                    LIGHT_GREY,
                    245
                )

                draw_centered_text(
                    current_task["input"].replace(
                        "KEY_",
                        ""
                    ),
                    title_font,
                    YELLOW,
                    280
                )

            else:

                draw_centered_text(
                    current_task["text"],
                    big_font,
                    WHITE,
                    265
                )

        # -----------------------------
        # PHYSICAL CONTROL PANEL
        # -----------------------------

        draw_panel(
            50,
            350,
            800,
            155
        )

        draw_centered_text(
            "CONTROL PANEL",
            small_font,
            LIGHT_GREY,
            370
        )

        draw_control_button(
            160,
            430,
            RED,
            "RED"
        )

        draw_control_button(
            290,
            430,
            BLUE,
            "BLUE"
        )

        draw_control_button(
            420,
            430,
            GREEN,
            "GREEN"
        )

        draw_keypad(
            640,
            360
        )

        draw_text(
            "KEYPAD",
            small_font,
            WHITE,
            555,
            420
        )

        # -----------------------------
        # BOTTOM HAZARD STRIPE
        # -----------------------------

        pygame.draw.rect(
            screen,
            DARK_GREY,
            (50, 515, 800, 15)
        )

        draw_warning_stripes(
            50,
            515,
            800,
            15
        )

        # -----------------------------
        # COMMENTARY MESSAGE
        # -----------------------------

        if not game_over and not game_won:

            message_age = (
                time.time()
                - message_started_at
            )

            if message_age < MESSAGE_DURATION:

                draw_centered_text(
                    message,
                    small_font,
                    WHITE,
                    540
                )

        # -----------------------------
        # WIN SCREEN
        # -----------------------------

        elif game_won:

            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0, 0, 0, 190)
            )

            screen.blit(
                overlay,
                (0, 0)
            )

            draw_centered_text(
                "MISSION COMPLETE!",
                title_font,
                GREEN,
                250
            )

            draw_centered_text(
                "YOU ACTUALLY DEFUSED IT.",
                font,
                WHITE,
                315
            )

            draw_button(
                "PLAY AGAIN",
                button_x,
                button_y,
                button_width,
                button_height
            )

        # -----------------------------
        # GAME OVER SCREEN
        # -----------------------------

        elif game_over:

            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0, 0, 0, 190)
            )

            screen.blit(
                overlay,
                (0, 0)
            )

            draw_centered_text(
                "MISSION FAILED!",
                title_font,
                RED,
                250
            )

            draw_centered_text(
                message,
                font,
                WHITE,
                315
            )

            draw_button(
                "PLAY AGAIN",
                button_x,
                button_y,
                button_width,
                button_height
            )

        # -----------------------------
        # KEYBOARD CONTROLS
        # -----------------------------

        draw_centered_text(
            "R/B/G = COLOUR    0-9/A/C/D = KEYPAD    V = B    S = *    H = #",
            small_font,
            GREY,
            565
        )

    # -----------------------------
    # ARCADE: ONE ROUND, THEN BACK TO THE MENU
    # -----------------------------

    if ARCADE:

        session.draw_exit_hint(screen)

        # Holding a button is not an input event, so count active play as input
        if not game_over and not game_won:

            session.note_input()

        reason = session.exit_reason()

        if reason:

            arcade_mode.finish(final_score(), reason)

        if game_over or game_won:

            if ended_at is None:

                ended_at = time.time()

            elif time.time() - ended_at >= arcade_mode.END_SCREEN_SECONDS:

                arcade_mode.finish(final_score(), "over", won=game_won)

    # -----------------------------
    # UPDATE SCREEN
    # -----------------------------

    pygame.display.flip()


# Close Pygame
pygame.quit()