
import curses
import random
import threading
import time
from curses import wrapper, window

Y_START_POINT = 3
INPUT_LABEL = "Your guess: "
MAX_TIMER_SECONDS = 15
timer_thread = None

STATE = {
    "current_screen": 0,
    "level": "Easy",
    "max_attempts": 5,
    "attempts": 0,
    "secret_number": 0,
    "time_left": MAX_TIMER_SECONDS,
    "quit": False,
}

WIN_CONFIG = {
    "begin_y": 0,
    "height": 0,
    "width": 100,
    "begin_x": 10,
}

def countdown(win: window, state, seconds, current_attempt):
    _, width = win.getmaxyx()
    while seconds > 0 and (current_attempt == state["attempts"]):
        minutes, secs = divmod(seconds, 60)
        time_str = f"{minutes:02d}:{secs:02d}"
        state["time_left"] = seconds
        win.addstr(1, get_center(time_str, width), time_str)
        win.refresh()
        time.sleep(1)
        seconds -= 1
    state['time_left'] = 0
    return

def get_center(text, width):
    mid = width // 2
    return mid - (len(text) // 2)

def draw_controls(controls, win, width, start=13):
    for index, text in enumerate(controls, start=start):
        win.addstr(index, get_center(text, width), text)

def draw_descriptions(descriptions, win, width, row=None):
    base_row = row if row is not None else Y_START_POINT
    for i, text in enumerate(descriptions):
        win.addstr(base_row + (i * 2), get_center(text, width), text)
    return

def draw_attempts(win: window, attempts, max_attempts):
    row = 5
    _, width = win.getmaxyx()
    attempt_info = f"Attempts: {attempts}/{max_attempts}"
    win.addstr(row, max(0, width - len(attempt_info) - 4), " " * (len(attempt_info) + 1))
    win.addstr(row, max(0, width - len(attempt_info) - 4), attempt_info)
    return

def draw_game_screen_descr(win, width, level):
    time_info = "Time Left"
    guess_info = "I am thinking of a number between 1 and 100"

    row = Y_START_POINT + 2
    left_margin = 3

    win.addstr(row, left_margin, f"Difficulty: {level}")

    row += 2
    win.addstr(row, get_center(time_info, width), time_info.upper())

    row += 4
    win.addstr(row, get_center(guess_info, width), guess_info)
    return

def create_window(height, width, begin_y, begin_x, border=True):
    win = curses.newwin(height, width, begin_y, begin_x)
    win.keypad(True)
    if border:
        win.border("|", "|")
    return win

def create_title_window(width, begin_y, begin_x):
    title = "Number guessing game"
    win = create_window(3, width, begin_y, begin_x)
    win.addstr(1, get_center(title, width - 4), title.upper())
    return win

def create_timer_window(begin_y, begin_x, state):
    elapsed_time = "00:00"
    width = len(elapsed_time) + 4
    return create_window(3, width, begin_y, begin_x + len(elapsed_time) + 1)

def create_input_window(width, begin_y, begin_x):
    win = create_window(3, width, begin_y, begin_x, False)
    win.addstr(0, 0, INPUT_LABEL)
    win.move(0, len(INPUT_LABEL))
    return win

def navigate_ingame_screens(win, state):
    submitted = False
    while not submitted:
        key = win.getch()
        if key in (curses.KEY_ENTER, 10, 13):
            state["current_screen"] = 2
            submitted = True
        elif key == ord("q"):
            state["current_screen"] = 1
            submitted = True
    return

def get_user_guess(win: window, main: window, timer_win: window, state):
    row = 0
    left_margin = len(INPUT_LABEL)
    guess: list = []
    hint_info = ""
    _, width = win.getmaxyx()
    win.timeout(15 * 1000)
    while True:
        key = win.getch()

        win.addstr(row, len(INPUT_LABEL), " " * max(1, len(guess)))

        if state['time_left'] == 0 and (state['max_attempts'] == state["attempts"]):
            state['current_screen'] = 5
            return
        elif state['time_left'] == 0:
            state["attempts"] += 1
            timer_thread = threading.Thread(target=countdown, args=(timer_win, STATE, MAX_TIMER_SECONDS, STATE["attempts"]), daemon=True)
            draw_attempts(main, state["attempts"], state["max_attempts"])
            main.refresh()
            left_margin = len(INPUT_LABEL)
            timer_thread.start()
            continue

        if key in (curses.KEY_ENTER, 10, 13):
            value = "".join(guess).strip()
            win.addstr(2, 0, " " * (width - 2))

            if not value:
                hint_info = "Type a number first."
                your_guess = -1
            else:
                try:
                    your_guess = int(value)
                except ValueError:
                    hint_info = "You had to provide a number 🙄"
                    your_guess = -1

            guess.clear()

            if your_guess > 0 and int(state["secret_number"]) < your_guess:
                hint_info = f"The number is lesser than {your_guess}"
            elif your_guess > 0 and int(state["secret_number"]) > your_guess:
                hint_info = f"The number is greater than {your_guess}"
            elif int(state["secret_number"]) == your_guess:
                state["current_screen"] = 3
                return

            if your_guess > 0:
                state["attempts"] += 1
                if state["attempts"] > state["max_attempts"]:
                    state["current_screen"] = 4
                    return

                timer_thread = threading.Thread(target=countdown, args=(timer_win, STATE, MAX_TIMER_SECONDS, STATE["attempts"]), daemon=True)
                timer_thread.start()

            win.addstr(2, 0, hint_info)
            win.move(row, len(INPUT_LABEL))
            draw_attempts(main, state["attempts"], state["max_attempts"])
            main.refresh()
            left_margin = len(INPUT_LABEL)

        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if len(guess) >= 1:
                left_margin -= 1
                guess.pop()
                win.addch(row, left_margin, " ")
                win.move(row, left_margin)

        elif key in (ord("q"), ord("Q")):
            state["attempts"] = 0
            state["current_screen"] = 1
            return

        elif 48 <= key <= 57:
            guess.append(chr(key))
            win.addch(row, left_margin, guess[-1])
            left_margin += 1

def game_screen(state, height, width, begin_y, begin_x):
    state["secret_number"] = random.randrange(1, 100)
    controls = [
        f"{'ENTER':<12}{'Submit':<6}",
        f"{'BACKSPACE':<12}{'Delete':<6}",
        f"{'Q':<12}{'Quit':<6}",
    ]

    main = create_window(height, width, begin_y, begin_x)
    title_win = create_title_window(width - 4, begin_y + 1, begin_x + 2)
    input_win = create_input_window(width - 4, begin_y + 13, begin_x + 2)

    row = Y_START_POINT + 5
    timer_win = create_timer_window(row, (width // 2), state)

    draw_game_screen_descr(main, width, state["level"])
    draw_attempts(main, state["attempts"], state["max_attempts"])

    row += 10
    draw_controls(controls, main, width, row)

    return main, title_win, timer_win, input_win

def win_screen(height, width, begin_y, begin_x, state):
    descriptions = [
        "YOU WON",
        "🎉",
        f"The number was {state['secret_number']}",
    ]

    results = [
        f"You made {state['attempts']}/{state['max_attempts']} attempts",
        "00:14",
    ]

    controls = [
        f"{'ENTER':<8}{'Play Again':<12}",
        f"{'Q':<8}{'Quit':<12}",
    ]

    state['attempts'] = 0
    win = create_window(height, width, begin_y, begin_x)
    draw_descriptions(descriptions, win, width)
    for i, text in enumerate(results, start=10):
        win.addstr(i, get_center(text, width), text)
    draw_controls(controls, win, width)

    return win

def lose_screen(height, width, begin_y, begin_x, state):
    descriptions = [
        "GAME OVER",
        "You ran out of chances.",
        f"The number was {state['secret_number']}",
    ]
    controls = [
        f"{'ENTER':<8}{'Play Again':<12}",
        f"{'Q':<8}{'Quit':<12}",
    ]
    state['attempts'] = 0
    win = create_window(height, width, begin_y, begin_x)
    draw_descriptions(descriptions, win, width)
    draw_controls(controls, win, width)

    return win

def time_out_screen(height, width, begin_y, begin_x, state):
    descriptions = [
        "TIME'S UP!",
        "You ran out of time.",
        "⌛",
        f"The number was {state['secret_number']}",
    ]

    controls = [
        f"{'ENTER':<8}{'Play Again':<12}",
        f"{'Q':<8}{'Quit':<12}",
    ]

    state['attempts'] = 0
    win = create_window(height, width, begin_y, begin_x)
    draw_descriptions(descriptions, win, width)
    draw_controls(controls, win, width)

    return win

def difficulty_screen(state, height=0, width=0, begin_y=0, begin_x=0):
    title = "SELECT DIFFICULTY"
    screen_description = "How confident are you?"

    options = [
        ("EASY", 10),
        ("MEDIUM", 5),
        ("HARD", 3),
    ]

    controls = [
        f"{'↑ ↓':<8}{'Select':<8}",
        f"{'ENTER':<8}{'Confirm':<8}",
        f"{'Q':<8}{'Quit':<8}",
    ]

    win = create_window(height, width, begin_y, begin_x)

    row = Y_START_POINT
    win.addstr(row, get_center(title, width), title)

    row += 2
    win.addstr(row, get_center(screen_description, width), screen_description)

    option_start_row = Y_START_POINT + 4

    for index, (level, chances) in enumerate(options):
        text = f"{level:<8} {chances} chances"
        y = option_start_row + index
        win.addstr(y, get_center(text, width), text)

    draw_controls(controls, win, width)

    selected = 0
    cursor = ">"

    def draw_cursor():
        level, chances = options[selected]
        text = f"{level:<8} {chances} chances"
        x = get_center(text, width) - 2
        y = option_start_row + selected
        win.addch(y, x, cursor)

    draw_cursor()

    while True:
        key = win.getch()

        level, chances = options[selected]
        text = f"{level:<8} {chances} chances"
        x = get_center(text, width) - 2
        y = option_start_row + selected
        win.addch(y, x, " ")

        if key == curses.KEY_UP:
            selected = (selected - 1) % len(options)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(options)
        elif key in (curses.KEY_ENTER, 10, 13):
            level, chances = options[selected]
            state["level"] = level.title()
            state["max_attempts"] = chances
            state["current_screen"] += 1
            return
        elif key in (ord("q"), ord("Q")):
            state["quit"] = True
            return

        draw_cursor()

def welcome_screen(state, height=0, width=0, begin_y=0, begin_x=0):
    title = "NUMBER GUESSING GAME"
    instructions = [
        "I'm thinking of a number between 1 and 100.",
        "Can you guess it?",
    ]
    controls = [
        "[ START GAME ]",
        f"{'ENTER':<8}{'Start':<6}",
        f"{'Q':<8}{'Quit':<6}",
    ]

    win = create_window(height, width, begin_y, begin_x)
    row = Y_START_POINT

    win.addstr(row, get_center(title, width), title)
    row += 2
    draw_descriptions(instructions, win, width, row)
    draw_controls(controls, win, width)

    while True:
        key = win.getch()
        if key in (curses.KEY_ENTER, 10, 13):
            state["current_screen"] += 1
            return win
        if key in (ord("q"), ord("Q")):
            state["quit"] = True
            return win

def refresh_windows(win, title_win, timer_win, input_win):
    global timer_thread

    if win:
        win.noutrefresh()
        if title_win:
            title_win.noutrefresh()
        if timer_win:
            timer_win.noutrefresh()
        if input_win:
            input_win.noutrefresh()

    curses.doupdate()

    if timer_win:
        timer_thread = threading.Thread(target=countdown, args=(timer_win, STATE, MAX_TIMER_SECONDS, STATE["attempts"]), daemon=True)
        timer_thread.start()

def select_screen(state, height=0, width=0, begin_y=0, begin_x=0):
    win = None
    title_win = None
    timer_win = None
    input_win = None
    ingame = False

    match state["current_screen"]:
        case 0:
            win = welcome_screen(state, height, width, begin_y, begin_x)
        case 1:
            win = difficulty_screen(state, height, width, begin_y, begin_x)
        case 2:
            win, title_win, timer_win, input_win = game_screen(state, height, width, begin_y, begin_x)
        case 3:
            win = win_screen(height, width, begin_y, begin_x, state)
            ingame = True
        case 4:
            win = lose_screen(height, width, begin_y, begin_x, state)
            ingame = True
        case 5:
            win = time_out_screen(height, width, begin_y, begin_x, state)
            ingame = True
        case _:
            state["quit"] = True

    refresh_windows(win, title_win, timer_win, input_win)

    if (input_win and timer_win and win):
        get_user_guess(input_win, win, timer_win, state)
    if ingame:
        navigate_ingame_screens(win, state)

def main(stdscr: window):
    stdscr.clear()
    curses.curs_set(0)
    curses.use_default_colors()
    WIN_CONFIG["height"] = curses.LINES

    while not STATE["quit"]:
        select_screen(STATE, **WIN_CONFIG)

    return

if __name__ == "__main__":
    wrapper(main)