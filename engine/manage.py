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
                    device_dict = {str(index): Device(serial) for index, serial in enumerate(serial_list, 1)}

            if not device_dict:
                Grapher.view(f"[#FFAF00]检测连接设备 ...")
                await asyncio.sleep(5)
                continue

            if len(device_dict) == 1:
                return device_dict["1"]

            for key, value in device_dict.items():
                Grapher.view(f"[#00FA9A]Connect ->[/] [{key}] {value}")
                if serial == value.serial:
                    return value

            try:
                return device_dict[Prompt.ask(f"请选择", console=Grapher.console)]
            except KeyError:
                Grapher.view(f"[#FF005F]没有该设备，请重新选择 ...\n")


if __name__ == '__main__':
    pass
