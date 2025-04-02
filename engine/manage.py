from rich.console import Console
from engine.device import Device


class Manage(object):

    def __init__(self, console: "Console"):
        self.console = console

    async def operate_device(self, serial: str):
        return Device(serial)


if __name__ == '__main__':
    pass
