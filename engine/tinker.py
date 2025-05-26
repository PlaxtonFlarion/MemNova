#   _____          _    _
#  |_   _|_ _  ___| | _| | ___
#    | |/ _` |/ __| |/ / |/ _ \
#    | | (_| | (__|   <| |  __/
#    |_|\__,_|\___|_|\_\_|\___|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import sys
import yaml
import json
import shutil
import typing
import aiofiles
from loguru import logger
from rich.logging import RichHandler
from engine.terminal import Terminal
from memcore.design import Design
from memnova import const


class _MemrixBaseError(BaseException):
    """
    Memrix 异常体系的基础类。

    所有 Memrix 框架内部抛出的异常应继承自此类，确保能够被统一捕获与分类。
    该类本身不带有任何行为，仅作为逻辑标识用途。
    """
    pass


class MemrixError(_MemrixBaseError):
    """
    Memrix 主异常类，用于报告运行时的关键错误信息。

    通常用于命令参数异常、任务执行失败、文件丢失、设备连接错误等情况。
    异常信息支持 rich 格式化输出（带颜色标记），在终端中以醒目的红色提示。

    Parameters
    ----------
    msg : Any
        异常提示信息，可以是字符串、对象或其他格式，会被格式化为终端输出内容。

    Attributes
    ----------
    msg : Any
        存储传入的异常信息内容，用于渲染提示。
    """

    def __init__(self, msg: typing.Any):
        self.msg = msg

    def __str__(self):
        """
        返回带有 rich 渲染标记的异常信息，适配 Grapher.view() 等日志系统。
        """
        return f"<{const.APP_DESC}Error> {self.msg}"

    __repr__ = __str__


class FileAssist(object):
    """
    文件操作工具类，用于读取与写入 YAML / JSON 文件，并封装跨平台的文本文件打开方式。

    提供异步方式的文件读写方法，支持编码处理、美化输出、键排序控制等，广泛用于 Memrix 配置、
    场景记录、报告数据缓存等操作。
    """

    @staticmethod
    async def open(file: str) -> typing.Optional[str]:
        """
        打开指定文件，使用系统默认文本编辑器，支持异步调用。

        - Windows：优先尝试 Notepad++，若不存在则退回到系统记事本
        - macOS：使用 TextEdit 并以阻塞模式打开（-W）

        Parameters
        ----------
        file : str
            要打开的文件路径。

        Returns
        -------
        Optional[str]
            执行结果的标准输出或错误输出；失败时返回 None。
        """
        if sys.platform == "win32":
            cmd = ["notepad++"] if shutil.which("notepad++") else ["Notepad"]
        else:
            cmd = ["open", "-W", "-a", "TextEdit"]
        return await Terminal.cmd_line(cmd + [file], timeout=False)

    @staticmethod
    async def read_yaml(file: str) -> dict:
        """
        异步读取 YAML 文件并解析为字典数据。

        Parameters
        ----------
        file : str
            YAML 文件路径。

        Returns
        -------
        dict
            解析后的字典数据。

        Raises
        ------
        yaml.YAMLError
            当 YAML 文件格式错误时抛出。
        """
        async with aiofiles.open(file, "r", encoding=const.CHARSET) as f:
            return yaml.load(await f.read(), Loader=yaml.FullLoader)

    @staticmethod
    async def read_json(file: str) -> dict:
        """
        异步读取 JSON 文件内容并返回为 Python 字典。

        Parameters
        ----------
        file : str
            JSON 文件路径。

        Returns
        -------
        dict
            解析后的字典数据。

        Raises
        ------
        json.JSONDecodeError
            当 JSON 文件格式无效时抛出。
        """
        async with aiofiles.open(file, "r", encoding=const.CHARSET) as f:
            return json.loads(await f.read())

    @staticmethod
    async def dump_yaml(src: str, dst: dict) -> None:
        """
        异步将 Python 字典写入 YAML 文件，自动格式化并保留中文字符。

        Parameters
        ----------
        src : str
            目标 YAML 文件路径。

        dst : dict
            要写入的字典内容。
        """
        async with aiofiles.open(src, "w", encoding=const.CHARSET) as f:
            await f.write(
                yaml.dump(dst, allow_unicode=True, default_flow_style=False, sort_keys=False)
            )

    @staticmethod
    async def dump_json(src: str, dst: dict) -> None:
        """
        异步将 Python 字典写入 JSON 文件，格式化输出并保留中文内容。

        Parameters
        ----------
        src : str
            目标 JSON 文件路径。

        dst : dict
            要写入的字典内容。
        """
        async with aiofiles.open(src, "w", encoding=const.CHARSET) as f:
            await f.write(
                json.dumps(dst, indent=4, separators=(",", ":"), ensure_ascii=False)
            )


class Active(object):
    """
    日志输出与终端美化工具类，提供统一的视觉日志体验。
    """

    @staticmethod
    def active(log_level: str) -> None:
        """
        启用 rich 日志渲染器，绑定至 loguru 并设置日志等级。

        内部将清空 loguru 的默认日志通道，绑定 rich 格式控制器，并使用指定等级激活输出。

        Parameters
        ----------
        log_level : str
            日志等级（如 "INFO", "DEBUG", "WARNING", "ERROR"）。
        """
        logger.remove()
        logger.add(
            RichHandler(console=Design.console, show_level=False, show_path=False, show_time=False),
            level=log_level, format=const.PRINT_FORMAT
        )


class Pid(object):
    """
    多进程 PID 映射结构，用于保存包名下关联的所有 PID 及其进程名。

    常用于应用多进程分析场景，支持通过 `member` 属性访问字典形式的映射关系。

    Parameters
    ----------
    member : Optional[dict]
        PID 与进程名的映射字典，结构为 {pid: process_name}。
    """

    def __init__(self, member: typing.Optional[dict] = None):
        self.__member = member

    @property
    def member(self) -> typing.Optional[dict]:
        """
        返回内部 PID 映射关系。
        """
        return self.__member


class Ram(object):
    """
    内存数据结构封装类，用于统一组织一次内存采集轮次中的各类数据分区。

    封装了 remark、resume、memory、vms 四类结构化字典数据，便于统一传递、
    插入数据库、绘图分析或报告生成。

    Parameters
    ----------
    details : dict[str, dict]
        完整内存数据结构，要求包含以下键：
        - remark_map : 应用运行时信息（时间戳、PID、UID、ADJ 等）
        - resume_map : 内存汇总指标（PSS、USS、RSS、SWAP 等）
        - memory_map : 内存详细构成（Native Heap、.so、.dex 等）
        - memory_vms : 虚拟内存信息（如 VmRSS）
    """

    def __init__(self, details: dict[str, dict]):
        self.__details = details

    @property
    def remark_map(self) -> typing.Optional[dict]:
        """
        应用运行状态数据。
        """
        return self.__details.get("remark_map", None)

    @property
    def resume_map(self) -> typing.Optional[dict]:
        """
        内存总览汇总信息。
        """
        return self.__details.get("resume_map", None)

    @property
    def memory_map(self) -> typing.Optional[dict]:
        """
        内存组成明细结构。
        """
        return self.__details.get("memory_map", None)

    @property
    def memory_vms(self) -> typing.Optional[dict]:
        """
        虚拟内存估值信息。
        """
        return self.__details.get("memory_vms", None)


if __name__ == '__main__':
    pass
