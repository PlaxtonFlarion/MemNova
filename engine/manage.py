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
    """
    设备管理类，用于异步检测、筛选并连接 Android 设备。

    封装了基于 ADB 的设备枚举与连接逻辑，支持多设备选择提示，
    适用于 `Memrix` 各模式在执行前确定目标设备。

    Methods
    -------
    operate_device(serial: str) -> Optional[Device]
        通过 ADB 获取设备列表，查找目标设备，或由用户选择目标设备。
    """

    @staticmethod
    async def operate_device(serial: str) -> typing.Optional["Device"]:
        """
        检测当前已连接的 Android 设备，并根据传入或交互方式返回目标 `Device` 实例。

        方法内部调用 `adb devices` 获取当前连接的设备列表：
        - 如果只连接一个设备，自动返回
        - 如果连接多个设备：
          - 优先匹配 `serial` 参数
          - 若不匹配，则提示用户手动选择

        Parameters
        ----------
        serial : str
            预期匹配的设备序列号（若存在多个设备时用于优先匹配）。

        Returns
        -------
        Optional[Device]
            匹配到的设备对象，若无设备则持续等待；若用户输入错误，则提示重试。

        Notes
        -----
        - 如果未连接任何设备，会每隔 5 秒重新检查一次
        - 使用 rich 的 `Prompt.ask()` 提供用户选择界面
        - 若用户选择无效设备编号，将提示并重试
        - 返回对象为自定义 `Device` 类实例，需提供 `.serial` 属性支持匹配
        """

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
