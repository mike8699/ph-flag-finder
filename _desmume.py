import time
from tkinter import Button, Label, Tk, BOTH
from PIL import Image, ImageTk

import keyboard
import win32api
import win32gui
from desmume.controls import Keys, keymask
from desmume.emulator import SCREEN_WIDTH, SCREEN_HEIGHT_BOTH
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

class GameWindow:
    def __init__(self):
        self.root = Tk()
        self.root.title("Game Window")
        self.tk_image = None
        self.original_image = None  # Store a reference to the original image
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT_BOTH
        self.scale_factor = 2

        # Set the initial size of the window
        self.root.geometry(f"{self.width * self.scale_factor}x{self.height * self.scale_factor}")

        # Create a label to display the image
        self.image_label = Label(self.root, image=self.tk_image)
        self.image_label.pack(fill=BOTH, expand=True)

    def update_image(self, new_image: Image.Image):
        # Keep a reference to the original image
        self.original_image = new_image.resize((self.width * self.scale_factor, self.height * self.scale_factor), Image.LANCZOS)

        # Convert the new image to a PhotoImage
        self.tk_image = ImageTk.PhotoImage(self.original_image)

        # Update the label with the new image
        self.image_label.configure(image=self.tk_image)

        self.root.update()


class DeSmuME(BaseDeSmuME):
    window: GameWindow

    def __init__(self, refresh_rate: int = 0, dl_name: str = None):
        super().__init__(dl_name)
        self.window = GameWindow()

        # Starting timer to control the framerate
        self._start_time = time.monotonic()
        self._refresh_rate = refresh_rate

        self.controls_widget = Tk()

        def increase_refresh_rate():
            self._refresh_rate += 10
            L["text"] = self._refresh_rate

        def decrease_refresh_rate():
            self._refresh_rate -= 10
            if self._refresh_rate < 0:
                self._refresh_rate = 0

            if self._refresh_rate == 0:
                L["text"] = "(no limits)"
            else:
                L["text"] = self._refresh_rate

        increase_button = Button(
            self.controls_widget,
            text="Decrease speed",
            command=decrease_refresh_rate,
        )
        increase_button.pack()
        decrease_button = Button(
            self.controls_widget,
            text="Increase speed",
            command=increase_refresh_rate,
        )
        decrease_button.pack()

        L = Label(self.controls_widget, text="(no limits)")
        L.pack()

    def cycle(self, with_joystick=True) -> None:
        self.controls_widget.update()
        if self._refresh_rate > 0:
            time.sleep(
                (1 / self._refresh_rate)
                - ((time.monotonic() - self._start_time) % (1 / self._refresh_rate))
            )

        for key, emulated_button in CONTROLS.items():
            if keyboard.is_pressed(key):
                self.input.keypad_add_key(keymask(emulated_button))
            else:
                self.input.keypad_rm_key(keymask(emulated_button))

        # If mouse is clicked
        if win32api.GetKeyState(0x01) < 0:
            # Get coordinates of click relative to desmume window
            x, y = win32gui.ScreenToClient(self.window.root.winfo_id(), win32gui.GetCursorPos())
            x //= self.window.scale_factor
            y //= self.window.scale_factor
            # Adjust y coord to account for clicks on top (non-touch) screen
            y -= (self.window.height // self.window.scale_factor)

            # Process input if it's valid
            if x in range(0, self.window.width) and y in range(0, self.window.height):
                self.input.touch_set_pos(x, y)
            else:
                self.input.touch_release()
        else:
            self.input.touch_release()
        super().cycle(with_joystick)
        self.window.update_image(self.screenshot())
        