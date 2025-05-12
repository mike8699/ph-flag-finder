from tkinter import Button, Label, Tk
from enum import StrEnum
import pygame
from desmume.controls import Keys, keymask
from desmume.emulator import (
    SCREEN_HEIGHT,
    SCREEN_HEIGHT_BOTH,
    SCREEN_PIXEL_SIZE,
    SCREEN_WIDTH,
)
from desmume.emulator import DeSmuME as BaseDeSmuME
from pygame.locals import QUIT, VIDEORESIZE
from ndspy.rom import NintendoDSRom


class Region(StrEnum):
    US = "E"
    EU = "P"
    JP = "J"


CONTROLS = {
    pygame.K_RETURN: Keys.KEY_START,
    pygame.K_RSHIFT: Keys.KEY_SELECT,
    pygame.K_q: Keys.KEY_L,
    pygame.K_w: Keys.KEY_R,
    pygame.K_a: Keys.KEY_Y,
    pygame.K_s: Keys.KEY_X,
    pygame.K_x: Keys.KEY_A,
    pygame.K_z: Keys.KEY_B,
    pygame.K_UP: Keys.KEY_UP,
    pygame.K_DOWN: Keys.KEY_DOWN,
    pygame.K_RIGHT: Keys.KEY_RIGHT,
    pygame.K_LEFT: Keys.KEY_LEFT,
}

FAKE_MIC_BUTTON = pygame.K_SPACE
MIC_ADDRESSES = {
    Region.US: 0x20EECCF,
    Region.EU: 0x20EED2F,
}


class DeSmuME(BaseDeSmuME):
    rom_region: Region
    has_quit: bool

    def __init__(self, refresh_rate: int = 0, dl_name: str | None = None):
        super().__init__(dl_name)

        self.has_quit = False

        self.pygame_screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT_BOTH), pygame.RESIZABLE
        )
        pygame.display.set_caption("ph-flag-finder")

        # Create another surface to draw on
        self.draw_surface = pygame.surface.Surface((SCREEN_WIDTH, SCREEN_HEIGHT_BOTH))

        # Starting timer to control the framerate
        self.clock = pygame.time.Clock()
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

    def open(self, file_name: str, auto_resume=True):
        rom = NintendoDSRom.fromFile(file_name)
        if rom.name.decode() != "ZELDA_DS:PH":
            raise ValueError("Invalid ROM!")
        self.rom_region = rom.idCode.decode()[3]
        return super().open(file_name, auto_resume)

    def _cycle_pygame_window(self) -> None:
        # Get the framebuffer from the emulator
        gpu_framebuffer = self.display_buffer_as_rgbx()

        # Create surfaces from framebuffer
        upper_surface = pygame.image.frombuffer(
            gpu_framebuffer[: SCREEN_PIXEL_SIZE * 4],
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            "RGBX",
        )

        lower_surface = pygame.image.frombuffer(
            gpu_framebuffer[SCREEN_PIXEL_SIZE * 4 :],
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            "RGBX",
        )

        # Draw the surfaces onto the draw surface
        self.draw_surface.blit(upper_surface, (0, 0))
        self.draw_surface.blit(lower_surface, (0, SCREEN_HEIGHT))

    def cycle(self, with_joystick=True) -> None:
        for event in pygame.event.get():
            if event.type == QUIT:
                self.has_quit = True
            elif event.type == VIDEORESIZE:
                self.pygame_screen = pygame.display.set_mode(
                    event.size, pygame.RESIZABLE
                )
                self._resize_pygame_window(event.size)

        if self.has_quit:
            self.controls_widget.destroy()
            return

        self._cycle_pygame_window()

        # Scale the draw surface to match the size of the screen and blit it on the screen
        self.pygame_screen.blit(
            pygame.transform.scale(
                self.draw_surface, self.pygame_screen.get_rect().size
            ),
            (0, 0),
        )
        pygame.display.flip()

        # Update control widget and handle input
        self.controls_widget.update()

        # Limit frame rate
        self.clock.tick(self._refresh_rate if self._refresh_rate > 0 else 0)

        for key, emulated_button in CONTROLS.items():
            if pygame.key.get_pressed()[key]:
                self.input.keypad_add_key(keymask(emulated_button))
            else:
                self.input.keypad_rm_key(keymask(emulated_button))

        if pygame.key.get_pressed()[FAKE_MIC_BUTTON]:
            self.memory.unsigned[MIC_ADDRESSES[self.rom_region]] = 0xFF

        # If mouse is clicked
        if pygame.mouse.get_pressed()[0]:
            window_height = self.pygame_screen.get_height()
            window_width = self.pygame_screen.get_width()

            # Get coordinates of click relative to desmume window
            x, y = pygame.mouse.get_pos()

            # Adjust y coord to account for clicks on top (non-touch) screen
            y -= window_height // 2

            # Get scale factors in case the screen has been resized
            x_scale = window_width / SCREEN_WIDTH
            y_scale = window_height / SCREEN_HEIGHT_BOTH

            # Adjust x and y coordinates based on the scale factor
            x = int(x / x_scale)
            y = int(y / y_scale)  # Adjust for the top screen height

            # Clamp the values to allow for mouse dragging outside window
            self.input.touch_set_pos(
                pygame.math.clamp(x, 0, window_width),
                pygame.math.clamp(y, 0, window_height),
            )
        else:
            self.input.touch_release()
            self.mousebtn_held = False

        super().cycle(with_joystick)

    def _resize_pygame_window(self, new_size: tuple) -> None:
        """Resize the Pygame window while maintaining the aspect ratio."""
        current_width, current_height = SCREEN_WIDTH, SCREEN_HEIGHT_BOTH
        new_width, new_height = new_size

        # Calculate new width based on the aspect ratio
        aspect_ratio = current_width / current_height
        new_width = int(new_height * aspect_ratio)

        # Adjust the Pygame screen size to maintain the aspect ratio
        self.pygame_screen = pygame.display.set_mode(
            (new_width, new_height), pygame.RESIZABLE
        )


pygame.init()
