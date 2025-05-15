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
from engine.tackle import Terminal
from memcore.display import Display


class Manage(object):
    """
    设备管理器，用于识别、筛选并连接 ADB 设备。

    提供基于 asyncio 的异步设备检测流程，支持自动识别单设备，
    或在多设备环境下提示用户交互选择。
    """

    @staticmethod
    async def operate_device(serial: str) -> typing.Optional["Device"]:
        """
        异步检测并连接目标设备，根据传入序列号匹配可用设备。

        - 若当前仅连接一个设备，将自动返回
        - 若存在多个设备，匹配序列号或提示用户手动选择
        - 若暂未检测到设备，则每 5 秒轮询并提示等待
        - 最大重试次数 20 次

        Parameters
        ----------
        serial : str
            目标设备的序列号，用于精确绑定目标设备。

        Returns
        -------
        Optional[Device]
            成功连接的设备对象，若始终无法连接则返回 None。

        Notes
        -----
        - 检测通过 adb devices 命令完成
        - 用户交互依赖 rich 的 Prompt 控制台组件
        """

        try_again, max_try_again = 0, 20
        while True:
            if try_again == max_try_again:
                return Display.Doc.log(f"[#FF5F00]设备连接超时 ...")

            device_dict = {}
            if result := await Terminal.cmd_line(["adb", "devices"]):
                if serial_list := [line.split()[0] for line in result.split("\n")[1:]]:
                    device_dict = {
                        str(index): Device(serial) for index, serial in enumerate(serial_list, 1)
                    }

            if not device_dict:
                try_again += 1
                Display.Doc.log(f"[#FFAF00]检测连接设备 ... 剩余 {(max_try_again - try_again):02} 次 ...")
                await asyncio.sleep(5)
                continue

            if (loc := len(device_dict)) == 1:
                Display.Doc.log(f"[#00FA9A]Connect ->[/] [{loc}] {device_dict[f'{loc}']}")
                return device_dict[f"{loc}"]

            device: typing.Optional["Device"] = None
            for k, v in device_dict.items():
                Display.Doc.log(f"[#00FA9A]Connect ->[/] [{k}] {v}")
                if serial == v.serial:
                    device = v

            try:
                return device if device else (
                    device_dict
                )[Prompt.ask(f"请选择", console=Display.console)]
            except KeyError:
                Display.Doc.log(f"[#FF005F]没有该设备，请重新选择 ...\n")
            finally:
                try_again = 0


if __name__ == '__main__':
    pass
