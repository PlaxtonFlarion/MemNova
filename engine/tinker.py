#   _____ _       _
#  |_   _(_)_ __ | | _____ _ __
#    | | | | '_ \| |/ / _ \ '__|
#    | | | | | | |   <  __/ |
#    |_| |_|_| |_|_|\_\___|_|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import re
import sys
import yaml
import json
import random
import shutil
import typing
import aiofiles
from loguru import logger
from datetime import datetime
from rich.text import Text
from rich.console import Console
from rich.logging import (
    LogRecord, RichHandler
)
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
        return await Terminal.cmd_line(cmd + [file])

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

    @staticmethod
    async def describe_text(src: typing.Any, dst: str) -> None:
        """
        将字符串内容异步写入指定文件路径。

        Parameters
        ----------
        src : Any
            文件路径对象或路径字符串，表示写入目标文件。

        dst : str
            要写入的字符串内容。
        """
        async with aiofiles.open(src, "w", encoding=const.CHARSET) as f:
            await f.write(dst)


class Active(object):
    """
    日志输出与终端美化工具类，提供统一的视觉日志体验。
    """

    class _RichSink(RichHandler):
        """
        基于 RichHandler 的日志输出接收器，用于自定义控制台美化输出。

        _RichSink 继承自 rich.logging.RichHandler，重载 emit 方法，
        将日志信息通过 rich 控制台格式化输出，适用于实时、美观的日志展示。

        Parameters
        ----------
        console : Console
            rich 提供的 Console 实例，用于渲染日志文本与样式。
        """
        debug_color = [
            "#00CED1",  # 深青色 - 冷静理性
            "#7FFFD4",  # 冰蓝绿 - 轻盈科技
            "#66CDAA",  # 中度绿松石 - 适合背景级别
            "#20B2AA",  # 浅海蓝 - 稳定中间调
            "#5F9EA0",  # 军蓝灰 - 稳重调试色
            "#87CEEB",  # 天蓝 - 清晰非干扰性
            "#4682B4",  # 钢蓝 - 稍微暗一点用于子模块
            "#98FB98",  # 浅绿色 - 绿色无压调试层
            "#B0C4DE",  # 灰蓝色 - 安静辅助信息
            "#AAAAAA",  # 中灰 - 用于淡化无关 debug 流
        ]
        info_color = [
            "#00FF7F",  # 春绿色 - 默认 Info 风格，清新明亮
            "#32CD32",  # 酸橙绿 - 活跃进行中，状态良好
            "#3CB371",  # 中海绿 - 稍深一点，适合常驻状态
            "#40E0D0",  # 宝石绿 - 信息明确、富有层次感
            "#00FA9A",  # 亮绿色 - 活力信息输出
            "#90EE90",  # 浅绿 - 背景型提示，柔和不刺眼
            "#2E8B57",  # 海藻绿 - 正常运行中，低调稳定
            "#8FBC8F",  # 深灰绿 - 辅助性 info，例如预加载提示
            "#7CFC00",  # 草地绿 - 执行中提示，轻快欢快
            "#ADFF2F",  # 黄绿 - 接近完成或重要 info 提示
            "#F5DEB3",  # 小麦色 - 柔和状态提示
            "#F0E68C",  # 卡其 - 稳定温和
            "#FFE4B5",  # 浅橙米 - 成功通知感
            "#FFDAB9",  # 桃色 - 轻松提示色
            "#E6E6FA",  # 淡紫 - 不干扰的存在感
            "#D8BFD8",  # 藕荷紫 - 精致低饱和
            "#FFEFD5",  # 浅金 - 近似 OK 状态色
            "#FFFACD",  # 柠檬乳黄 - 活泼但不跳脱
            "#EEE8AA",  # 浅卡其 - 稳妥类日志色
            "#F0FFF0",  # 蜜瓜白 - 极淡提示背景色
        ]
        level_style = {
            "DEBUG": f"bold {random.choice(debug_color)}",
            "INFO": f"bold {random.choice(info_color)}",
            "WARNING": "bold #FFD700",
            "ERROR": "bold #FF4500",
            "CRITICAL": "bold #FF1493",
        }

        def __init__(self, console: "Console"):
            super().__init__(
                console=console, rich_tracebacks=True, show_path=False,
                show_time=False, markup=False
            )

        def emit(self, record: "LogRecord") -> None:
            """
            重载日志处理器的输出逻辑，将格式化后的记录打印到指定控制台。
            """
            self.console.print(
                const.PRINT_HEAD, Text(self.format(record), style=self.level_style.get(
                    record.levelname, "bold #ADD8E6"
                ))
            )

    @staticmethod
    def active(log_level: str) -> None:
        """
        配置并激活 Rich 控制台日志处理器。

        移除默认日志处理器，添加自定义 _RichSink 实例，结合 rich.console
        提供彩色输出支持，并通过传入的 log_level 控制日志等级。

        Parameters
        ----------
        log_level : str
            日志等级（如 "INFO", "DEBUG", "WARNING", "ERROR"），不区分大小写。
        """
        logger.remove()
        logger.add(
            Active._RichSink(Design.console),
            level=log_level, format=const.PRINT_FORMAT
        )


class Period(object):

    @staticmethod
    def convert_time(raw_time: str) -> str:
        try:
            dt = datetime.strptime(raw_time, "%Y%m%d%H%M%S")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise MemrixError(f"非法时间格式: {raw_time}")

    @staticmethod
    def compress_time(dt: "datetime") -> str:
        if isinstance(dt, str):
            # 可自适应格式，也可以指定格式如 "%Y-%m-%d %H:%M:%S"
            try:
                dt = datetime.fromisoformat(dt)
            except ValueError:
                dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y%m%d%H%M%S")


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


class ToolKit(object):
    """
    工具类，用于执行单位转换、数值计算与文本匹配等基础功能。
    """

    @staticmethod
    def fit_mem(text: str, text_content: str) -> float:
        try:
            match = re.search(fr"{text}.*?(\d+)", text_content, re.S)
            return round(float(match.group(1)) / 1024, 3)
        except (AttributeError, TypeError, ValueError):
            return 0.00

    @staticmethod
    def fit_io(text: str, text_content: str) -> float:
        try:
            match = re.search(fr"{text}.*?(\d+)", text_content, re.S)
            return round(float(match.group(1)) / 1024 / 1024, 3)
        except (AttributeError, TypeError, ValueError):
            return 0.00

    @staticmethod
    def fit_io_count(text: str, text_content: str) -> int:
        try:
            match = re.search(fr"{text}.*?(\d+)", text_content, re.S)
            return int(match.group(1))
        except (AttributeError, TypeError, ValueError):
            return 0

    @staticmethod
    def uss_addition(text_content: str) -> float:
        try:
            match = re.search(r"(?<=TOTAL).*(\d+)", text_content, re.S)
            total = match.group().split()
            p_dirty, p_clean = float(total[1]) / 1024, float(total[2]) / 1024
            return round(sum([p_dirty, p_clean]), 3)
        except (AttributeError, TypeError, ValueError):
            return 0.00


if __name__ == '__main__':
    pass
