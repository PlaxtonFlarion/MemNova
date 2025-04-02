import re
import typing
import asyncio
import uiautomator2
from engine.tackle import (
    PID, Terminal
)


class Device(object):

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
        self.u2_device = await asyncio.to_thread(uiautomator2.connect, self.serial)

    async def u2(self, choice: dict, method: str, *args, **kwargs) -> typing.Optional[str]:
        element = self.u2_device(**choice) if choice else self.u2_device
        if callable(method := getattr(element, method)):
            return await asyncio.to_thread(method, *args, **kwargs)

    @staticmethod
    async def sleep(delay: float, *_, **__) -> None:
        await asyncio.sleep(delay)

    async def pid_value(self, package: str) -> typing.Optional["PID"]:
        cmd = ["adb", "-s", self.serial, "shell", "ps", "-A", "|", "grep", package]
        result = await Terminal.cmd_line(*cmd)
        if result and (pid_list := result.split("\n")):
            try:
                return PID(
                    {i.split()[1]: name for i in pid_list if (name := i.split()[8]) == package}
                )
            except IndexError:
                return None

    async def uid_value(self, package: str) -> typing.Optional[str]:
        cmd = ["adb", "-s", self.serial, "shell", "dumpsys", "package", package, "|", "grep", "uid="]
        if result := await Terminal.cmd_line(*cmd):
            return uid.group(0) if (uid := re.search(r"(?<=uid=)\d+", result)) else None

    async def act_value(self) -> typing.Optional[str]:
        cmd = ["adb", "-s", self.serial, "shell", "dumpsys", "window", "|", "grep", "mCurrentFocus"]
        if result := await Terminal.cmd_line(*cmd):
            if activity := re.search(r"(?<=Window\{).*?(?=})", result):
                return activity.group().split("/" if "/" in activity.group() else None)[-1]

    async def adj_value(self, pid: str) -> typing.Optional[str]:
        cmd = ["adb", "-s", self.serial, "shell", "cat", f"/proc/{pid}/oom_adj"]
        if result := await Terminal.cmd_line(*cmd):
            return None if "No such file" in result else result

    async def pkg_value(self, pid: str) -> typing.Optional[str]:
        cmd = ["adb", "-s", self.serial, "shell", "cat", f"/proc/{pid}/status"]
        if result := await Terminal.cmd_line(*cmd):
            return vm.group(1) if (vm := re.search(r"VmRSS:.*?(\d+)", result, re.S)) else None

    async def screen_status(self) -> typing.Optional[bool]:
        cmd = ["adb", "-s", self.serial, "shell", "dumpsys", "deviceidle", "|", "grep", "mScreenOn"]
        if result := await Terminal.cmd_line(*cmd):
            return bool(re.search(r"(?<=mScreenOn=).*", result).group())


if __name__ == '__main__':
    pass
