import sys
import time
import typing
import asyncio
from rich.console import Console
from engine.parser import Parser

console: typing.Optional["Console"] = Console()


class ToolKit(object):
    pass


class ProcessDetail(object):
    pass


class Group(object):
    pass


class Memrix(object):

    def __init__(
            self,
            memory: typing.Optional[bool],
            script: typing.Optional[bool],
            report: typing.Optional[bool],
            *args,
            **__
    ):
        self.memory, self.script, self.report = memory, script, report
        self.sylora, self.serial, *_ = args

        if self.memory:
            self.var_action = time.strftime("%Y%m%d%H%M%S")
        elif self.script:
            self.var_action = self.sylora
        elif self.report:
            self.var_action = self.sylora

        if not self.var_action:
            return

    async def dump_task(self):
        pass

    async def stop_task(self):
        pass

    async def exec_task(self):
        pass

    async def create_report(self):
        pass


async def main():
    memrix = Memrix(
        memory := cmd_lines.memory,
        script := cmd_lines.script,
        report := cmd_lines.report,
        cmd_lines.sylora, cmd_lines.serial
    )
    if memory:
        await memrix.dump_task()
    elif script:
        await memrix.exec_task()
    elif report:
        await memrix.create_report()
    else:
        return None


if __name__ == '__main__':
    cmd_lines = Parser.parse_cmd()

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        sys.exit(1)
    else:
        sys.exit(0)
