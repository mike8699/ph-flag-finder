from datetime import datetime
from pathlib import Path

from tkinter import filedialog

import cv2
import keyboard
import numpy as np
from desmume.controls import Keys, keymask
from desmume.emulator import DeSmuME
from PIL import Image

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

PARENT_DIRECTORY = Path(f'output_{datetime.now().strftime("%Y%m%d%H%M%S")}')
PARENT_DIRECTORY.mkdir()


def write_frames_to_video(frames: list[Image.Image]) -> str:
    filename = PARENT_DIRECTORY / f'{datetime.now().strftime("%Y%m%d%H%M%S")}.mp4'
    video = cv2.VideoWriter(
        str(filename),
        cv2.VideoWriter_fourcc(*"avc1"),
        60,
        (256, 384),
    )
    for img in frames:
        video.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))


def main() -> None:
    file_path = filedialog.askopenfilename()

    emu = DeSmuME()
    emu.open(file_path)

    video_frames: list[Image.Image] = []

    def set_flag_breakpoint(frames: list[Image.Image]) -> None:
        write_frames_to_video(frames)

    emu.memory.register_exec(
        0x209773C, lambda addr, size: set_flag_breakpoint(video_frames)
    )

    # Create the window for the emulator
    window = emu.create_sdl_window()

    while not window.has_quit():
        video_frames.append(emu.screenshot())
        if len(video_frames) > 5000:
            video_frames = video_frames[1:]

        window.process_input()

        for key, emulated_button in CONTROLS.items():
            if keyboard.is_pressed(key):
                emu.input.keypad_add_key(keymask(emulated_button))
            else:
                emu.input.keypad_rm_key(keymask(emulated_button))

        emu.cycle()
        window.draw()


if __name__ == "__main__":
    main()
