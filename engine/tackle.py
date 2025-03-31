import sys
import yaml
import json
import typing
import asyncio
import aiofiles
from loguru import logger


class _MemrixBaseError(BaseException):
    pass


class MemrixError(_MemrixBaseError):

    def __init__(self, msg: typing.Any):
        self.msg = msg


class Terminal(object):

    @staticmethod
    async def cmd_line(*cmd: str) -> typing.Optional[str]:
        logger.debug([c for c in cmd])
        transports = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        encode = "GBK" if sys.platform == "win32" else "UTF-8"
        stdout, stderr = await transports.communicate()

        if stdout:
            return stdout.decode(encoding=encode, errors="ignore").strip()
        if stderr:
            return stderr.decode(encoding=encode, errors="ignore").strip()

    @staticmethod
    async def cmd_line_shell(cmd: str) -> typing.Optional[str]:
        logger.debug(cmd)
        transports = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        encode = "GBK" if sys.platform == "win32" else "UTF-8"
        stdout, stderr = await transports.communicate()

        if stdout:
            return stdout.decode(encoding=encode, errors="ignore").strip()
        if stderr:
            return stderr.decode(encoding=encode, errors="ignore").strip()


class ReadFile(object):

    @staticmethod
    async def read_yaml(file: str) -> dict:
        try:
            async with aiofiles.open(file, "r", encoding="UTF-8") as f:
                config = await asyncio.to_thread(yaml.load, await f.read(), Loader=yaml.FullLoader)
        except (FileNotFoundError, yaml.YAMLError) as e:
            raise MemrixError(e)

        return config

    @staticmethod
    async def read_json(file: str) -> dict:
        try:
            async with aiofiles.open(file, "r", encoding="UTF-8") as f:
                config = await asyncio.to_thread(json.loads, await f.read())
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise MemrixError(e)

        return config


class Logger(object):
    pass


if __name__ == '__main__':
    a = asyncio.run(ReadFile.read_yaml(r"/Users/acekeppel/PycharmProjects/MemNova/config.yaml"))
    print(type(a), a)
    pass
