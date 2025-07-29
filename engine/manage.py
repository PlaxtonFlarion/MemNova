#   __  __
#  |  \/  | __ _ _ __   __ _  __ _  ___
#  | |\/| |/ _` | '_ \ / _` |/ _` |/ _ \
#  | |  | | (_| | | | | (_| | (_| |  __/
#  |_|  |_|\__,_|_| |_|\__,_|\__, |\___|
#                            |___/
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import typing
import asyncio
from rich.prompt import Prompt
from engine.device import Device
from engine.terminal import Terminal
from memcore.design import Design


class Manage(object):

    def __init__(self, adb: str):
        self.adb = adb

    async def device_info(self, serial: str) -> dict:
        keys = {
            "brand": "ro.product.brand",
            "model": "ro.product.model",
            "release": "ro.build.version.release"
        }

        cmd = [self.adb, "-s", serial, "shell", "getprop"]
        response = await asyncio.gather(
            *(Terminal.cmd_line(cmd + [key]) for key in keys.values())
        )

        return {k: v or "N/A" for k, v in zip(keys, response)} | {"serial": serial}

    async def operate_device(self, imply: str) -> typing.Optional["Device"]:
        try_again, max_try_again = 0, 20

        while True:
            if try_again == max_try_again:
                return Design.Doc.log(f"[#FF5F00]设备连接超时 ...")

            if not (result := await Terminal.cmd_line([self.adb, "devices"])):
                continue

            device_dict = {}
            for i, line in enumerate(result.splitlines()[1:], start=1):
                if not (parts := line.strip().split()):
                    continue
                info = await self.device_info(parts[0])
                device_dict[str(i)] = Device(self.adb, **info)

            if not device_dict:
                try_again += 1
                Design.Doc.log(f"[#FFAF00]检测连接设备 ... 剩余 {(max_try_again - try_again):02} 次 ...")
                await asyncio.sleep(5)
                continue

            if (loc := len(device_dict)) == 1:
                Design.Doc.log(f"[#00FA9A]Connect ->[/] [{loc}] {device_dict[f'{loc}']}\n")
                return device_dict[f"{loc}"]

            device: typing.Optional["Device"] = None
            for k, v in device_dict.items():
                Design.Doc.log(f"[#00FA9A]Connect ->[/] [{k}] {v}")
                if imply == v.serial:
                    device = v

            try:
                return device if device else (
                    device_dict
                )[Prompt.ask(f"请选择", console=Design.console)]
            except KeyError:
                Design.Doc.log(f"[#FF005F]没有该设备，请重新选择 ...")
            finally:
                try_again = 0
                Design.console.print()


if __name__ == '__main__':
    pass
