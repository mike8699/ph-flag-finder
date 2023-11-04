import keyboard
import win32api
import win32gui
from desmume.controls import Keys, keymask
from desmume.emulator import SCREEN_HEIGHT, SCREEN_WIDTH
from desmume.emulator import DeSmuME as BaseDeSmuME
from desmume.emulator import DeSmuME_SDL_Window

CONTROLS = {
    "enter": Keys.KEY_START,
    "right shift": Keys.KEY_SELECT,
    "q": Keys.KEY_L,
    "w": Keys.KEY_R,
    "a": Keys.KEY_Y,
    "s": Keys.KEY_X,
    "x": Keys.KEY_A,
    "z": Keys.KEY_B,
    "up": Keys.KEY_UP,
    "down": Keys.KEY_DOWN,
    "right": Keys.KEY_RIGHT,
    "left": Keys.KEY_LEFT,
}


class DeSmuME(BaseDeSmuME):
    window: DeSmuME_SDL_Window
    window_handle: int

    def __init__(self, dl_name: str = None):
        super().__init__(dl_name)
        self.window = self.create_sdl_window()

    def cycle(self, with_joystick=True) -> None:
        for key, emulated_button in CONTROLS.items():
            if keyboard.is_pressed(key):
                self.input.keypad_add_key(keymask(emulated_button))
            else:
                self.input.keypad_rm_key(keymask(emulated_button))

        # If mouse is clicked
        if win32api.GetKeyState(0x01) < 0:
            # Get coordinates of click relative to desmume window
            x, y = win32gui.ScreenToClient(self.window_handle, win32gui.GetCursorPos())
            # Adjust y coord to account for clicks on top (non-touch) screen
            y -= SCREEN_HEIGHT

            # Process input if it's valid
            if x in range(0, SCREEN_WIDTH) and y in range(0, SCREEN_HEIGHT):
                self.input.touch_set_pos(x, y)
            else:
                self.input.touch_release()
        else:
            self.input.touch_release()
        super().cycle(with_joystick)
        self.window.draw()
        self.window_handle = win32gui.FindWindow(None, "Desmume SDL")
