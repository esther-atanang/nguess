
import curses
import random
import threading
import time
from curses import wrapper, window
from typing import Any, TypedDict

class GameState(TypedDict):
    current_screen: int
    level:str
    max_attempts:int
    attempts:int
    secret_number: int
    time_left:int
    quit:bool

Y_START_POINT = 3
INPUT_LABEL = "Your guess: "
MAX_TIMER_SECONDS = 15
timer_thread = None

STATE: GameState = {
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

def countdown(win: window, state:GameState, seconds:int, current_attempt:int):
    """Creates a countdown timer and draws the remaining seconds on the screen.

    Args:
        win (window): Screen to be drawn to
        state (dict[str, Any]): The current game state
        seconds (int): The amount of seconds to countdown
        current_attempt (int): The current guess attempt 
    """
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

def get_center(text:str, width:int) -> int:
    """Gets the center of a window to place a text.

    Args:
        text (str): The text to place at the center
        width (int): The width of the window

    Returns:
        int: The windows center
    """
    mid = width // 2
    return mid - (len(text) // 2)

def draw_controls(controls:list[str], win:window, width:int, start:int=13):
    """Draws a list of windows controls to the sceen.

    Args:
        controls (list[str]): The controls.
        win (window): The screen to be drawn to.
        width (int): The total width of the window.
        start (int, optional): The row to start from. Defaults to 13.
    """
    for index, text in enumerate(controls, start=start):
        win.addstr(index, get_center(text, width), text)

def draw_descriptions(descriptions:list[str], win: window, width:int, row:int | None =None):
    """Draws a descriptions to a window's screen.

    Args:
        descriptions (list[str]): The descriptions 
        win (window): The curses screen
        width (int): The total width of the window
        row (int | None, optional): The row to start from. Defaults to None.
    """
    
    base_row = row if row is not None else Y_START_POINT
    for i, text in enumerate(descriptions):
        win.addstr(base_row + (i * 2), get_center(text, width), text)
        
    return

def draw_attempts(win: window, attempts:int, max_attempts:int):
    """Draws the amount of attempts onto the window.

    Args:
        win (window): The current screen
        attempts (int): The number of attempts a player has made.
        max_attempts (int): The total attempts the player can make.
    """
    row = 5
    _, width = win.getmaxyx()
    attempt_info = f"Attempts: {attempts}/{max_attempts}"
    win.addstr(row, max(0, width - len(attempt_info) - 4), " " * (len(attempt_info) + 1))
    win.addstr(row, max(0, width - len(attempt_info) - 4), attempt_info)
    return

def draw_game_screen_descr(win:window, width:int, level:str):
    """Draws descriptions onto the game screen.

    Args:
        win (window): The current screen.
        width (int): The width of the current window
        level (str): The current level being played
    """
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

def create_window(height:int, width:int, begin_y:int, begin_x:int, border:bool=True):
    """Creates a curses window.

    Args:
        height (int): The height of the window
        width (int): The size of the window
        begin_y (int): The vertical start of the window in relation to the main window
        begin_x (int): The Horizontal start of the window in relation to the main window
        border (bool, optional): Determines if the user will have a window or not. Defaults to 

    Returns:
        window: A Screen 
    """
    win = curses.newwin(height, width, begin_y, begin_x)
    win.keypad(True)
    if border:
        win.border("|", "|")
    return win

def create_title_window(width:int, begin_y:int, begin_x:int):
    """Creates the in game title window.

    Args:
        width (int): The total size of the window
        begin_y (int): The vertical start of the window in relation to the main window 
        begin_x (int): The Horizontal start of the window in relation to the main window

    Returns:
        window : The screen
    """
    title = "Number guessing game"
    win = create_window(3, width, begin_y, begin_x)
    win.addstr(1, get_center(title, width - 4), title.upper())
    return win

def create_timer_window(begin_y:int, begin_x:int):
    """Creates the ingame timer window.

    Args:
        begin_y (int): The vertical start in relative to the main window
        begin_x (int): The horizontal start, relative to the main window

    Returns:
        window: The Title screen
    """
    width = 9
    return create_window(3, width, begin_y, begin_x + 6)

def create_input_window(width:int, begin_y:int, begin_x:int):
    """Creates the in game input window.

    Args:
        width (int): The total size of the current window
        begin_y (int): The vertical start, relative to the main window 
        begin_x (int): The horizontal start, relative to the main window 

    Returns:
        window: The Input Screen
    """
    win = create_window(3, width, begin_y, begin_x, False)
    win.addstr(0, 0, INPUT_LABEL)
    win.move(0, len(INPUT_LABEL))
    return win

def navigate_ingame_screens(win: window, state: GameState):
    """Navigates between screens during the game session.

    Args:
        win (window): current screen 
        state (GameState): The current game state
    """
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

def get_user_guess(win: window, main: window, timer_win: window, state: GameState):
    """Gets the user typed guess.

    Args:
        win (window): The current screen
        main (window): The main screen the current screen is drawn on
        timer_win (window): The timer screen
        state (GameState): The current game state
    """
    row = 0
    left_margin = len(INPUT_LABEL)
    guess: list = []
    hint_info = ""
    _, width = win.getmaxyx()
    win.timeout(15 * 1000)
    while True:
        key = win.getch()

        

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
            win.addstr(row, len(INPUT_LABEL), " " * max(1, len(guess)))
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

def game_screen(state: GameState, height:int, width:int, begin_y:int, begin_x:int):
    """The game screen.

    Args:
        height (int): The screen's height
        width (int): The screen's width
        begin_y (int): The vertical start point, relative to the main screen
        begin_x (int): The horizontal start point, relative to the main screen
        state (GameState): The current game's state

    Returns:
        window: The drawn game screen
    """
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
    timer_win = create_timer_window(row, (width // 2))

    draw_game_screen_descr(main, width, state["level"])
    draw_attempts(main, state["attempts"], state["max_attempts"])

    row += 10
    draw_controls(controls, main, width, row)

    return main, title_win, timer_win, input_win

def win_screen(height:int, width:int, begin_y:int, begin_x:int, state: GameState):
    """The screen shown to the user when they guess correctly.

    Args:
        height (int): The screen's height
        width (int): The screen's width
        begin_y (int): The vertical start point, relative to the main screen
        begin_x (int): The horizontal start point, relative to the main screen
        state (GameState): The current game's state

    Returns:
        window: The winning screen
    """
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

def lose_screen(height: int, width: int, begin_y: int, begin_x: int, state: GameState):
    """The screen shown to the user when they guess wrongly.

    Args:
        height (int): The screen's height
        width (int): The screen's width
        begin_y (int): The vertical start point, relative to the main screen
        begin_x (int): The horizontal start point, relative to the main screen
        state (GameState): The current game's state

    Returns:
        window: The losing screen
    """
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

def time_out_screen(height: int, width: int, begin_y: int, begin_x: int, state: GameState):
    """The screen shown to the user when run out of time.

    Args:
        height (int): The screen's height
        width (int): The screen's width
        begin_y (int): The vertical start point, relative to the main screen
        begin_x (int): The horizontal start point, relative to the main screen
        state (GameState): The current game's state

    Returns:
        window: The timeout losing screen
    """
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

def difficulty_screen(state: GameState, height: int=0, width: int=0, begin_y: int=0, begin_x: int=0):
    """Choose a level screen.

    Args:
        height (int): The screen's height
        width (int): The screen's width
        begin_y (int): The vertical start point, relative to the main screen
        begin_x (int): The horizontal start point, relative to the main screen
        state (GameState): The current game's state

    Returns:
        window: The pick a level screen
    """
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

def welcome_screen(state: GameState, height: int=0, width: int=0, begin_y: int=0, begin_x: int=0):
    """The first screen shown to the user

    Args:
        height (int): The screen's height
        width (int): The screen's width
        begin_y (int): The vertical start point, relative to the main screen
        begin_x (int): The horizontal start point, relative to the main screen
        state (GameState): The current game's state

    Returns:
        window: The welcome screen
    """
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

def refresh_windows(win: window | None, title_win:window | None, timer_win: window | None, input_win: window|None):
    """Refreshes the curses windows

    Args:
        win (window | None): The main window
        title_win (window | None): The title in-game window
        timer_win (window | None): The timer in-game window
        input_win (window | None): The input in-game window
    """
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

def select_screen(state: GameState, height: int=0, width: int=0, begin_y: int=0, begin_x: int=0):
    """Displays a particular screen

    Args:
        height (int): The screen's height
        width (int): The screen's width
        begin_y (int): The vertical start point, relative to the main screen
        begin_x (int): The horizontal start point, relative to the main screen
        state (GameState): The current game's state
    """
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
    if ingame and win:
        navigate_ingame_screens(win, state)

def main(stdscr: window):
    """Creates the standard screen

    Args:
        stdscr (window): The main screen
    """
    stdscr.clear()
    curses.curs_set(0)
    curses.use_default_colors()
    WIN_CONFIG["height"] = curses.LINES

    while not STATE["quit"]:
        select_screen(STATE, **WIN_CONFIG)

    return

if __name__ == "__main__":
    wrapper(main)