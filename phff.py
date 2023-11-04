import json
from dataclasses import asdict, dataclass
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


@dataclass
class FlagSet:
    base_addr: int
    param2: int
    set: bool
    thumbnail: str
    video: str


def write_frames_to_video(frames: list[Image.Image], timestamp: str) -> str:
    filename = PARENT_DIRECTORY / f"{timestamp}.mp4"
    video = cv2.VideoWriter(
        str(filename),
        cv2.VideoWriter_fourcc(*"avc1"),
        60,
        (256, 384),
    )
    for img in frames:
        video.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
    return filename


def main() -> None:
    file_path = filedialog.askopenfilename()

    flags: list[FlagSet] = []

    emu = DeSmuME()
    emu.open(file_path)

    PARENT_DIRECTORY.mkdir()

    video_frames: list[Image.Image] = []

    def set_flag_breakpoint(frames: list[Image.Image]) -> None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        video_file = str(write_frames_to_video(frames, timestamp))
        screenshot_file = str(PARENT_DIRECTORY / f"{timestamp}.png")
        emu.screenshot().save(screenshot_file)
        emu.savestate.save_file(str(PARENT_DIRECTORY / f"{timestamp}.dsv"))
        (PARENT_DIRECTORY / f"{timestamp}.json").write_text(
            json.dumps(
                asdict(
                    FlagSet(
                        base_addr=emu.memory.register_arm9.r0,
                        param2=emu.memory.register_arm9.r1,
                        set=bool(emu.memory.register_arm9.r2),
                        thumbnail=screenshot_file,
                        video=video_file,
                    )
                ),
                indent=2,
            )
        )

    emu.memory.register_exec(
        0x209773C, lambda addr, size: set_flag_breakpoint(video_frames)
    )

    # Create the window for the emulator
    window = emu.create_sdl_window()

    while not window.has_quit():
        video_frames.append(emu.screenshot())
        if len(video_frames) > 600:
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
