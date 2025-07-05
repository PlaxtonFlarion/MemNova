#   _____                   _             _
#  |_   _|__ _ __ _ __ ___ (_)_ __   __ _| |
#    | |/ _ \ '__| '_ ` _ \| | '_ \ / _` | |
#    | |  __/ |  | | | | | | | | | | (_| | |
#    |_|\___|_|  |_| |_| |_|_|_| |_|\__,_|_|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import typing
import asyncio
from loguru import logger
from memnova import const


class Terminal(object):
    """
    异步命令行执行工具类，用于跨平台执行 shell 或子进程命令。
    """

    @staticmethod
    async def cmd_line(cmd: list[str], transmit: typing.Optional[bytes] = None) -> typing.Optional[str]:
        logger.debug(cmd)

        transports = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await transports.communicate(transmit)

        if stdout:
            return stdout.decode(encoding=const.CHARSET, errors="ignore").strip()
        if stderr:
            return stderr.decode(encoding=const.CHARSET, errors="ignore").strip()

    @staticmethod
    async def cmd_link(cmd: list[str]) -> "asyncio.subprocess.Process":
        logger.debug(cmd)

        transports = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        return transports

    @staticmethod
    async def cmd_line_shell(cmd: str, transmit: typing.Optional[bytes] = None) -> typing.Any:
        logger.debug(cmd)

        transports = await asyncio.create_subprocess_shell(
            cmd,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await transports.communicate(transmit)

        if stdout:
            return stdout.decode(encoding=const.CHARSET, errors="ignore").strip()
        if stderr:
            return stderr.decode(encoding=const.CHARSET, errors="ignore").strip()

    @staticmethod
    async def cmd_link_shell(cmd: str) -> "asyncio.subprocess.Process":
        logger.debug(cmd)

        transports = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        return transports


if __name__ == '__main__':
    pass
