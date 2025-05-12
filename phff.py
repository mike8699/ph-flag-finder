import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

import cv2
import numpy as np
from PIL import Image

from _desmume import DeSmuME, Region

PARENT_DIRECTORY = Path(f'output_{datetime.now().strftime("%Y%m%d%H%M%S")}')

SET_FLAG_FUNCTION_ADDRS: list[dict[str, dict[Region, int]]] = [
    {
        "AdventureFlags.Set": {
            Region.US: 0x209773C,
            Region.EU: 0x209779C,
        },
    },
    {
        "Course.SetFlag0": {
            Region.US: 0x207D77C,
            Region.EU: 0x207D7DC,
        },
    },
    {
        "Course.SetFlag1": {
            Region.US: 0x207D7E8,
            Region.EU: 0x207D848,
        },
    },
    {
        "MapData.SetFlag0": {
            Region.US: 0x20973AC,
            Region.EU: 0x209740C,
        },
    },
    {
        "MapData.SetFlag1": {
            Region.US: 0x2097418,
            Region.EU: 0x2097478,
        },
    },
    {
        "MapData.SetFlag2": {
            Region.US: 0x2097484,
            Region.EU: 0x20974E4,
        },
    },
    {
        "MapData.SetFlag3": {
            Region.US: 0x20974F0,
            Region.EU: 0x2097550,
        },
    },
    {
        "MapData.SetFlag4": {
            Region.US: 0x209755C,
            Region.EU: 0x20975BC,
        },
    },
]


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


def write_frames_to_video(
    frames: list[Image.Image], func_name: str, file_name: str
) -> Path:
    """Convert a list of images to a video and writes it to disk."""
    filename = PARENT_DIRECTORY / func_name / f"{file_name}.mp4"
    video = cv2.VideoWriter(
        str(filename),
        cv2.VideoWriter.fourcc(*"mp4v"),
        60,
        (256, 384),
    )
    for img in frames:
        video.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
    return filename


def main() -> None:
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = filedialog.askopenfilename()

    emu = DeSmuME()
    emu.open(file_path)

    PARENT_DIRECTORY.mkdir()

    video_frames: list[Image.Image] = []

    def set_flag_breakpoint(address, size) -> None:
        # Get the appropriate function name using the monitored address
        for func in SET_FLAG_FUNCTION_ADDRS:
            for key in func.keys():
                if func[key][emu.rom_region] == address:
                    func_name = key
                    break

        # Check if the function folder exists, and create it if it doesn't.
        if not Path.exists(PARENT_DIRECTORY / func_name):
            Path.mkdir(PARENT_DIRECTORY / func_name)

        # Get the function arguments for the set flag function
        r0 = emu.memory.register_arm9.r0
        r1 = emu.memory.register_arm9.r1
        r2 = emu.memory.register_arm9.r2

        # r0 contains the "base address" of the flags in memory
        base_address = r0
        # Calculate the offset from the base address that the flag is located at
        flag_offset_from_base = (r1 >> 5) * 4
        # Figure out what bit the flag is at
        flag_bit = 1 << (r1 & 0x1F)

        # The game code gives these values in terms of words (i.e. 4 bytes),
        # so to get it in terms of bytes, we need to do some conversion here
        while flag_bit > 0x80:
            flag_bit >>= 8
            flag_offset_from_base += 1

        flag_absolute_address = base_address + flag_offset_from_base

        # r2 is a boolean, which determines whether the flag should be set or unset
        set = bool(r2)

        # Get string timestamp to use in filenames
        timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
        # File name
        file_name = f"{timestamp}-[{hex(flag_absolute_address)}_{hex(flag_bit)}]"
        # Generate video
        video_file = str(write_frames_to_video(video_frames, func_name, file_name))
        # Generate screenshot
        screenshot_file = str(PARENT_DIRECTORY / func_name / f"{file_name}.png")
        emu.screenshot().save(screenshot_file)
        # Create save state
        emu.savestate.save_file(str(PARENT_DIRECTORY / func_name / f"{file_name}.dsv"))

        (PARENT_DIRECTORY / func_name / f"{file_name}.json").write_text(
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

    # Register a breakpoint at the beginning of all defined flag functions (of SET_FLAG_FUNCTION_ADDRS)
    # that calls the callback defined above
    for func in SET_FLAG_FUNCTION_ADDRS:
        for key in func.keys():
            emu.memory.register_exec(
                func[key][emu.rom_region],
                set_flag_breakpoint,
            )

    while not emu.has_quit:
        # Save current video frame and discard old ones
        video_frames.append(emu.screenshot())
        if len(video_frames) > 600:
            video_frames = video_frames[1:]

        emu.cycle()


if __name__ == "__main__":
    main()
