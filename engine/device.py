#   ____             _
#  |  _ \  _____   _(_) ___ ___
#  | | | |/ _ \ \ / / |/ __/ _ \
#  | |_| |  __/\ V /| | (_|  __/
#  |____/ \___| \_/ |_|\___\___|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import re
import typing
import asyncio
import uiautomator2
from engine.tinker import Pid
from engine.terminal import Terminal


class Device(object):
    """
    Android 设备操作封装类，提供设备级数据采集与控制接口。

    该类用于连接并操作指定序列号的 Android 设备，提供基于 ADB 与 uiautomator2 的高层封装，
    支持异步获取 UID、PID、当前 Activity、前后台状态、内存信息等关键指标，
    是内存监控与自动化执行的核心桥梁组件。

    Parameters
    ----------
    serial : str
        设备的序列号，用于连接 ADB 与 uiautomator2。

    Attributes
    ----------
    serial : str
        当前绑定设备的序列号。

    u2_device : Optional[uiautomator2.Device]
        已连接的 uiautomator2 设备对象，在调用 `u2_active()` 后可用。
    """
    u2_device: typing.Optional["uiautomator2.Device"] = None

    def __init__(self, serial: str):
        self.serial = serial

    def __str__(self):
        return f"<Device serial={self.serial}>"

    __repr__ = __str__

    def __getstate__(self):
        return {"serial": self.serial}

    def __setstate__(self, state):
        self.serial = state["serial"]

    async def u2_active(self) -> None:
        """
        使用序列号连接 uiautomator2 设备。
        """
        self.u2_device = await asyncio.to_thread(uiautomator2.connect, self.serial)

    async def u2(
            self, choice: dict, method: str, *args, **kwargs
    ) -> typing.Optional[typing.Union[typing.Any, Exception]]:
        """
        执行 uiautomator2 元素方法，支持传参与回调。
        """
        element = self.u2_device(**choice) if choice else self.u2_device
        if callable(method := getattr(element, method)):
            try:
                return await asyncio.to_thread(method, *args, **kwargs)
            except Exception as e:
                return e

    @staticmethod
    async def sleep(delay: float, *_, **__) -> None:
        """
        协程内延时函数（替代 time.sleep）。
        """
        await asyncio.sleep(delay)

    async def pid_value(self, package: str) -> typing.Optional["Pid"]:
        """
        查询指定包名对应的进程 PID（支持多进程）。
        """
        cmd = ["adb", "-s", self.serial, "shell", "ps", "-A", "|", "grep", package]
        result = await Terminal.cmd_line(cmd)
        if result and (pid_list := result.split("\n")):
            try:
                return Pid(
                    {i.split()[1]: name for i in pid_list if (name := i.split()[8]) == package}
                )
            except IndexError:
                return None

    async def uid_value(self, package: str) -> typing.Optional[str]:
        """
        获取指定包名对应的 UID。
        """
        cmd = ["adb", "-s", self.serial, "shell", "dumpsys", "package", package, "|", "grep", "uid="]
        if result := await Terminal.cmd_line(cmd):
            return uid.group(0) if (uid := re.search(r"(?<=uid=)\d+", result)) else None

    async def act_value(self) -> typing.Optional[str]:
        """
        获取当前正在前台显示的 Activity 名称。
        """
        cmd = ["adb", "-s", self.serial, "shell", "dumpsys", "window", "|", "grep", "mCurrentFocus"]
        if result := await Terminal.cmd_line(cmd):
            if activity := re.search(r"(?<=Window\{).*?(?=})", result):
                return activity.group().split("/" if "/" in activity.group() else None)[-1]

    async def adj_value(self, pid: str) -> typing.Optional[str]:
        """
        获取进程 ADJ 值（前后台判定）。
        """
        cmd = ["adb", "-s", self.serial, "shell", "cat", f"/proc/{pid}/oom_adj"]
        if result := await Terminal.cmd_line(cmd):
            return None if "No such file" in result else result

    async def pkg_value(self, pid: str) -> typing.Optional[str]:
        """
        获取进程内存 VmRSS 值（用于内存图补充）。
        """
        cmd = ["adb", "-s", self.serial, "shell", "cat", f"/proc/{pid}/status"]
        if result := await Terminal.cmd_line(cmd):
            return vm.group(1) if (vm := re.search(r"VmRSS:.*?(\d+)", result, re.S)) else None

    async def screen_status(self) -> typing.Optional[bool]:
        """
        判断当前设备屏幕是否点亮。
        """
        cmd = ["adb", "-s", self.serial, "shell", "dumpsys", "deviceidle", "|", "grep", "mScreenOn"]
        if result := await Terminal.cmd_line(cmd):
            return bool(re.search(r"(?<=mScreenOn=).*", result).group())

    async def examine_package(self, package: str) -> typing.Optional[str]:
        """
        检查指定包名是否存在于目标设备上，并返回其路径。
        """
        cmd = ["adb", "-s", self.serial, "shell", "pm", "path", package]
        return result if (result := await Terminal.cmd_line(cmd)) else None

    async def memory_info(self, package: str) -> typing.Optional[str]:
        """
        获取应用内存明细（dumpsys meminfo 原始文本）。
        """
        cmd = ["adb", "-s", self.serial, "shell", "dumpsys", "meminfo", package]
        return result if (result := await Terminal.cmd_line(cmd)) else None


if __name__ == '__main__':
    pass
