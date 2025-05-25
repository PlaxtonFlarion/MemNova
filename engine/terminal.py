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

    Terminal 类提供统一接口封装，支持字符串或参数列表形式的命令输入，
    并可根据需求启用 shell 模式与超时控制，适用于脚本驱动的自动化任务执行。
    """

    @staticmethod
    async def cmd_line(cmd: list[str] | str, timeout: bool = True, shell: bool = False) -> typing.Optional[str]:
        """
        异步执行命令行指令，支持列表或字符串命令格式，可配置 shell 与超时行为。

        Parameters
        ----------
        cmd : Union[list[str], str]
            要执行的命令行指令，可以是命令字符串，也可以是参数列表。

        timeout : bool, optional
            是否启用 3 秒超时机制，默认为 True，若为 False 则无限等待命令结束。

        shell : bool, optional
            是否以 shell 模式执行命令（如支持管道、重定向等），默认为 False。

        Returns
        -------
        Optional[str]
            命令执行的标准输出或错误输出内容（首选 stdout），若超时或无输出则返回 None。
        """
        logger.debug(cmd)

        transports = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        ) if shell else await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                transports.communicate(), timeout=3
            ) if timeout else await transports.communicate()
        except asyncio.TimeoutError:
            return None

        if stdout:
            return stdout.decode(encoding=const.CHARSET, errors="ignore").strip()
        if stderr:
            return stderr.decode(encoding=const.CHARSET, errors="ignore").strip()

    @staticmethod
    async def cmd_link(cmd: list[str]) -> "asyncio.subprocess.Process":
        """
        异步执行命令行指令，并返回子进程传输句柄。

        该方法不等待命令执行结束，而是直接返回进程对象（用于流式或手动控制的场景）。

        Parameters
        ----------
        cmd : list[str]
            要执行的命令及其参数列表。

        Returns
        -------
        asyncio.subprocess.Process
            返回 asyncio 创建的子进程对象（transports），可手动调用 `.communicate()`、`.stdin.write()` 等方法继续交互。
        """
        logger.debug(cmd)

        transports = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        return transports


if __name__ == '__main__':
    pass
