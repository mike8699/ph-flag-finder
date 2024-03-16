import time
from tkinter import Button, Label, Tk

import cairo
import keyboard
import pygame
import win32api
import win32gui
from desmume.controls import Keys, keymask
from desmume.emulator import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_HEIGHT_BOTH,
    SCREEN_PIXEL_SIZE,
)
from desmume.emulator import DeSmuME as BaseDeSmuME
from desmume.emulator import DeSmuME_SDL_Window
from pygame.locals import QUIT

pygame.init()

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
    window_handle: int | None

    def __init__(self, refresh_rate: int = 0, dl_name: str = None):
        super().__init__(dl_name)

        self.has_quit = False
        self.window_handle = None

        self.pygame_screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT_BOTH))
        pygame.display.set_caption("ph-flag-finder")

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

    def _cycle_pygame_window(self) -> None:
        # Get the framebuffer from the emulator
        gpu_framebuffer = self.display_buffer_as_rgbx()

        # Create surfaces from framebuffer
        upper_surface = cairo.ImageSurface.create_for_data(
            gpu_framebuffer[: SCREEN_PIXEL_SIZE * 4],
            cairo.FORMAT_RGB24,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )

        lower_surface = cairo.ImageSurface.create_for_data(
            gpu_framebuffer[SCREEN_PIXEL_SIZE * 4 :],
            cairo.FORMAT_RGB24,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )

        # Convert Cairo surfaces to Pygame surfaces
        upper_image = pygame.image.frombuffer(
            upper_surface.get_data(), (SCREEN_WIDTH, SCREEN_HEIGHT), "RGBX"
        )

        lower_image = pygame.image.frombuffer(
            lower_surface.get_data(), (SCREEN_WIDTH, SCREEN_HEIGHT), "RGBX"
        )

        # Blit the surfaces onto the screen
        self.pygame_screen.blit(upper_image, (0, 0))
        self.pygame_screen.blit(
            lower_image, (0, SCREEN_HEIGHT)
        )  # Blit the lower screen below the upper screen
        pygame.display.flip()

        if not self.window_handle:
            self.window_handle = win32gui.FindWindow(None, "ph-flag-finder")
            print(self.window_handle)

    def cycle(self, with_joystick=True) -> None:
        for event in pygame.event.get():
            if event.type == QUIT:
                self.has_quit = True
        if self.has_quit:
            return

        self._cycle_pygame_window()
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
