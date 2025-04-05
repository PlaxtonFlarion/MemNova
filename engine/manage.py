#   __  __
#  |  \/  | __ _ _ __   __ _  __ _  ___
#  | |\/| |/ _` | '_ \ / _` |/ _` |/ _ \
#  | |  | | (_| | | | | (_| | (_| |  __/
#  |_|  |_|\__,_|_| |_|\__,_|\__, |\___|
#                            |___/
#
# 版权所有 (c) 2024  Memrix(记忆星核)
# 此文件受 Memrix(记忆星核) 许可证的保护。您可以在 LICENSE.md 文件中查看详细的许可条款。
#
# Copyright (c) 2024  Memrix(记忆星核)
# This file is licensed under the Memrix(记忆星核) License. See the LICENSE.md file for more details.
#

import typing
import asyncio
from rich.prompt import Prompt
from engine.device import Device
from engine.tackle import (
    Terminal, Grapher
)


class Manage(object):

    @staticmethod
    async def operate_device(serial: str) -> typing.Optional["Device"]:
        while True:
            device_dict = {}
            if result := await Terminal.cmd_line(*["adb", "devices"]):
                if serial_list := [line.split()[0] for line in result.split("\n")[1:]]:
                    device_dict = {
                        str(index): Device(serial) for index, serial in enumerate(serial_list, 1)
                    }

            if not device_dict:
                Grapher.view(f"[#FFAF00]检测连接设备 ...")
                await asyncio.sleep(5)
                continue

            if len(device_dict) == 1:
                return device_dict["1"]

            for k, v in device_dict.items():
                Grapher.view(f"[#00FA9A]Connect ->[/] [{k}] {v}")
                if serial == v.serial:
                    return v

            try:
                return device_dict[Prompt.ask(f"请选择", console=Grapher.console)]
            except KeyError:
                Grapher.view(f"[#FF005F]没有该设备，请重新选择 ...\n")


if __name__ == '__main__':
    pass
