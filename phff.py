import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

import cv2
import numpy as np
from PIL import Image

from _desmume import DeSmuME

PARENT_DIRECTORY = Path(f'output_{datetime.now().strftime("%Y%m%d%H%M%S")}')


@dataclass
class FlagSet:
    param0: int
    param1: int
    param2: int
    base_address: str  # str so we can store hex form
    offset_from_base: str  # str so we can store hex form
    flag_absolute_address: str  # str so we can store hex form
    flag_bit: str  # str so we can store hex form
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

        r0 = emu.memory.register_arm9.r0
        r1 = emu.memory.register_arm9.r1
        r2 = emu.memory.register_arm9.r2

        base_address = r0
        flag_offset_from_base = (r1 >> 5) * 4
        flag_bit = 1 << (r1 & 0x1F)
        while flag_bit > 0x80:
            flag_bit >>= 8
            flag_offset_from_base += 1

        flag_absolute_address = base_address + flag_offset_from_base

        set = bool(r2)

        (PARENT_DIRECTORY / f"{timestamp}.json").write_text(
            json.dumps(
                asdict(
                    FlagSet(
                        param0=r0,
                        param1=r1,
                        param2=r2,
                        base_address=hex(r0),
                        offset_from_base=hex(flag_offset_from_base),
                        flag_absolute_address=hex(flag_absolute_address),
                        flag_bit=hex(flag_bit),
                        set=set,
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

    while not emu.window.has_quit():
        video_frames.append(emu.screenshot())
        if len(video_frames) > 600:
            video_frames = video_frames[1:]

        emu.cycle()


if __name__ == "__main__":
    main()
