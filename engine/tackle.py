#   _____          _    _
#  |_   _|_ _  ___| | _| | ___
#    | |/ _` |/ __| |/ / |/ _ \
#    | | (_| | (__|   <| |  __/
#    |_|\__,_|\___|_|\_\_|\___|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import os
import sys
import yaml
import json
import shutil
import typing
import asyncio
import aiosqlite
from loguru import logger
from rich.logging import RichHandler
from memcore.display import Display
from memcore.parser import Parser
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
            return stdout.decode(encoding=const.ENCODING, errors="ignore").strip()
        if stderr:
            return stderr.decode(encoding=const.ENCODING, errors="ignore").strip()

    @staticmethod
    async def cmd_link(cmd: list[str]) -> "asyncio.subprocess.Process":
        """
        异步执行命令行指令，并返回子进程传输句柄。

        该方法与 `cmd_line` 类似，但不等待命令执行结束，而是直接返回进程对象（用于流式或手动控制的场景）。

        Parameters
        ----------
        cmd : list[str]
            要执行的命令及其参数列表。

        Returns
        -------
        asyncio.subprocess.Process
            返回 asyncio 创建的子进程对象（transports），可手动调用 `.communicate()`、`.stdin.write()` 等方法继续交互。

        Notes
        -----
        - 与 `cmd_line` 不同，该方法不自动处理输出，也不会解码。
        - 适合用于需要长时间运行或交互式输入输出的子进程场景。

        Workflow
        --------
        1. 异步启动子进程并打开 stdout/stderr 管道。
        2. 返回子进程 transport 对象供外部使用。
        """
        logger.debug(cmd)

        transports = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        return transports


class FileAssist(object):
    """
    文件操作工具类，用于读取与写入 YAML / JSON 文件，并封装跨平台的文本文件打开方式。

    提供异步和同步方式的文件读写方法，支持编码处理、美化输出、键排序控制等，广泛用于 Memrix 配置、
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
    def read_yaml(file: str) -> dict:
        """
        从 YAML 文件中读取内容并返回为 Python 字典。

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
        with open(file, "r", encoding=const.ENCODING) as f:
            return yaml.load(f.read(), Loader=yaml.FullLoader)

    @staticmethod
    def read_json(file: str) -> dict:
        """
        从 JSON 文件中读取内容并返回为 Python 字典。

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
        with open(file, "r", encoding=const.ENCODING) as f:
            return json.loads(f.read())

    @staticmethod
    def dump_yaml(src: typing.Any, dst: dict) -> None:
        """
        将 Python 字典写入 YAML 文件，自动格式化并保留中文字符。

        Parameters
        ----------
        src : str
            目标 YAML 文件路径。

        dst : dict
            要写入的字典内容。
        """
        with open(src, "w", encoding=const.ENCODING) as f:
            yaml.dump(dst, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    @staticmethod
    def dump_json(src: typing.Any, dst: dict) -> None:
        """
         将 Python 字典写入 JSON 文件，格式化输出并保留中文内容。

         Parameters
         ----------
         src : str
             目标 JSON 文件路径。

         dst : dict
             要写入的字典内容。
         """
        with open(src, "w", encoding=const.ENCODING) as f:
            json.dump(dst, f, indent=4, separators=(",", ":"), ensure_ascii=False)


class Grapher(object):
    """
    日志输出与终端美化工具类，为 Memrix 提供统一的视觉日志体验。

    封装 `loguru` 日志系统与 `rich.console.Console`，用于配置日志格式、
    启用彩色输出、显示结构化信息，并提供格式化打印视图日志的便捷方法。
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
            RichHandler(console=Display.console, show_level=False, show_path=False, show_time=False),
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


class Config(object):
    """
    配置管理类，用于加载、更新与访问 Memrix 的 YAML 配置文件。

    封装了默认配置结构，包括内存采样频率、测试标签、报告参数等，
    并通过属性方式提供统一访问接口。同时支持类型容错转换与 YAML 写入。

    初始化时自动尝试读取配置文件，若不存在则写入默认配置。

    Parameters
    ----------
    config_file : str or Path
        配置文件的路径，必须为 YAML 格式。

    Attributes
    ----------
    configs : dict
        当前完整的配置字典结构，按功能模块划分为 Memory / Script / Report。
    """

    configs = {
        "Memory": {
            "speed": 1,
            "label": "应用名称"
        },
        "Script": {
            "group": "mission"
        },
        "Report": {
            "fg_max": 0.0,
            "fg_avg": 0.0,
            "bg_max": 0.0,
            "bg_avg": 0.0,
            "headline": "标题",
            "criteria": "标准"
        }
    }

    def __init__(self, config_file: typing.Any):
        self.load_config(config_file)

    def __getstate__(self):
        return self.configs

    def __setstate__(self, state):
        self.configs = state

    @property
    def speed(self):
        """
        采样间隔时间（秒），范围建议为 1~10。
        """
        return self.configs["Memory"]["speed"]

    @property
    def label(self):
        """
        当前测试任务的标签或名称，用于日志与报告标注。
        """
        return self.configs["Memory"]["label"]

    @property
    def group(self):
        """
        JSON 自动化脚本中任务组字段名。
        """
        return self.configs["Script"]["group"]

    @property
    def fg_max(self):
        """
        报告中前台 PSS 峰值容忍阈。
        """
        return self.configs["Report"]["fg_max"]

    @property
    def fg_avg(self):
        """
        报告中前台 PSS 平均值容忍阈。
        """
        return self.configs["Report"]["fg_avg"]

    @property
    def bg_max(self):
        """
        报告中后台 PSS 峰值容忍阈。
        """
        return self.configs["Report"]["bg_max"]

    @property
    def bg_avg(self):
        """
        报告中后台 PSS 平均值容忍阈。
        """
        return self.configs["Report"]["bg_avg"]

    @property
    def headline(self):
        """
        报告页标题。
        """
        return self.configs["Report"]["headline"]

    @property
    def criteria(self):
        """
        报告中的性能评估标准描述。
        """
        return self.configs["Report"]["criteria"]

    @speed.setter
    def speed(self, value: typing.Any):
        self.configs["Memory"]["speed"] = Parser.parse_decimal(value)

    @label.setter
    def label(self, value: typing.Any):
        self.configs["Memory"]["label"] = value

    @group.setter
    def group(self, value: typing.Any):
        self.configs["Script"]["group"] = value

    @fg_max.setter
    def fg_max(self, value: typing.Any):
        self.configs["Report"]["fg_max"] = Parser.parse_decimal(value)

    @fg_avg.setter
    def fg_avg(self, value: typing.Any):
        self.configs["Report"]["fg_avg"] = Parser.parse_decimal(value)

    @bg_max.setter
    def bg_max(self, value: typing.Any):
        self.configs["Report"]["bg_max"] = Parser.parse_decimal(value)

    @bg_avg.setter
    def bg_avg(self, value: typing.Any):
        self.configs["Report"]["bg_avg"] = Parser.parse_decimal(value)

    @headline.setter
    def headline(self, value: typing.Any):
        self.configs["Report"]["headline"] = value

    @criteria.setter
    def criteria(self, value: typing.Any):
        self.configs["Report"]["criteria"] = value

    def load_config(self, config_file: typing.Any) -> None:
        """
        加载 YAML 配置文件并更新当前配置项。

        如果指定的配置文件存在且格式正确，则逐项读取其中内容并设置为当前属性值。
        若文件不存在或读取失败（语法错误等），则自动写入默认配置并覆盖原文件。

        Parameters
        ----------
        config_file : str or Path
            配置文件的路径，应为 YAML 格式。

        Notes
        -----
        - 文件结构必须匹配默认结构中的模块与字段
        - 使用 setattr 动态写入各字段以触发 setter 类型转换（如 parse_integer / parse_decimal）
        """
        try:
            user_config = FileAssist.read_yaml(config_file)
            for key, value in self.configs.items():
                for k, v in value.items():
                    setattr(self, k, user_config.get(key, {}).get(k, v))
        except (FileNotFoundError, yaml.YAMLError):
            self.dump_config(config_file)

    def dump_config(self, config_file: typing.Any) -> None:
        """
        将当前配置结构写入 YAML 文件，自动格式化并支持中文。

        如果目标路径的文件夹不存在，将自动创建。写入内容为 self.configs，
        使用 UTF-8 编码保存，保留键顺序并启用多行友好格式。

        Parameters
        ----------
        config_file : str or Path
            要写入的配置文件路径。
        """
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        FileAssist.dump_yaml(config_file, self.configs)


class DataBase(object):
    """
    内存数据数据库操作类，为 Memrix 提供异步持久化能力。

    基于 aiosqlite 提供的异步接口，实现数据表创建、内存数据插入与采集结果查询。
    所有操作基于统一结构的 memory_data 表，支持前后台筛选与图表构建数据输出。
    """

    @staticmethod
    async def create_table(db: "aiosqlite.Connection") -> None:
        """
        创建内存采样数据表 `memory_data`，如果表不存在则自动创建。

        表结构涵盖基础信息（时间戳、PID、UID）、前后台状态、内存汇总值与详细内存段字段，
        可用于图表展示、报告分析与任务回溯。

        Parameters
        ----------
        db : aiosqlite.Connection
            异步 SQLite 数据库连接对象。
        """

        await db.execute('''CREATE TABLE IF NOT EXISTS memory_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_dir TEXT,
            label TEXT,
            timestamp INTEGER,
            pid INTEGER,
            uid INTEGER,
            adj INTEGER,
            activity TEXT,
            foreground INTEGER,
            graphics REAL,
            rss REAL,
            pss REAL,
            uss REAL,
            swap REAL,
            opss REAL,
            native_heap REAL,
            dalvik_heap REAL,
            dalvik_other REAL,
            stack REAL,
            ashmem REAL,
            gfx_dev REAL,
            other_dev REAL,
            so_mmap REAL,
            jar_mmap REAL,
            apk_mmap REAL,
            ttf_mmap REAL,
            dex_mmap REAL,
            oat_mmap REAL,
            art_mmap REAL,
            other_mmap REAL,
            egl_mtrack REAL,
            gl_mtrack REAL,
            unknown REAL,
            vmrss REAL)''')
        await db.commit()

    @staticmethod
    async def insert_data(
            db: "aiosqlite.Connection",
            data_dir: str,
            label: str,
            remark_map: dict,
            resume_map: dict,
            memory_map: dict,
            vmrss: dict
    ) -> None:
        """
        将一轮内存采样结果写入数据库。

        参数由 `Ram` 对象构建而成，拆解为 remark（基础）、resume（汇总）、
        memory（明细）和 vmrss（估值）四部分。

        Parameters
        ----------
        db : aiosqlite.Connection
            异步 SQLite 数据库连接对象。

        data_dir : str
            当前任务的目录标识（轮次标记）。

        label : str
            当前测试任务的标签名称。

        remark_map : dict
            应用运行状态数据，如时间戳、PID、UID、Activity、是否前台等。

        resume_map : dict
            汇总内存数据，如 PSS、USS、RSS、SWAP、Graphics 等。

        memory_map : dict
            详细内存段数据，如 Native Heap、.dex、.so、Stack 等。

        vmrss : dict
            虚拟内存估值，如 VmRSS。
        """
        await db.execute('''INSERT INTO memory_data (
            data_dir,
            label,
            timestamp,
            pid,
            uid,
            adj,
            activity,
            foreground,
            graphics,
            rss,
            pss,
            uss,
            swap,
            opss,
            native_heap,
            dalvik_heap,
            dalvik_other,
            stack,
            ashmem,
            other_dev,
            so_mmap,
            jar_mmap,
            apk_mmap,
            ttf_mmap,
            dex_mmap,
            oat_mmap,
            art_mmap,
            other_mmap,
            gl_mtrack,
            unknown,
            vmrss) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                data_dir,
                label,
                remark_map["tms"],
                remark_map["pid"],
                remark_map["uid"],
                remark_map["adj"],
                remark_map["act"],
                remark_map["frg"],

                resume_map["Graphics"],
                resume_map["TOTAL RSS"],
                resume_map["TOTAL PSS"],
                resume_map["TOTAL USS"],
                resume_map["TOTAL SWAP"],
                resume_map["OPSS"],

                memory_map["Native Heap"],
                memory_map["Dalvik Heap"],
                memory_map["Dalvik Other"],
                memory_map["Stack"],
                memory_map["Ashmem"],
                memory_map["Other dev"],
                memory_map[".so mmap"],
                memory_map[".jar mmap"],
                memory_map[".apk mmap"],
                memory_map[".ttf mmap"],
                memory_map[".dex mmap"],
                memory_map[".oat mmap"],
                memory_map[".art mmap"],
                memory_map["Other mmap"],
                memory_map["GL mtrack"],
                memory_map["Unknown"],

                vmrss["vms"]
            )
        )
        await db.commit()

    @staticmethod
    async def query_data(db: "aiosqlite.Connection", data_dir: str) -> tuple[list, list]:
        """
        查询指定数据目录（轮次）下的前台与后台内存采样数据。

        输出结果格式为用于图表展示的有序列表，按时间排序，字段结构如下：
        (timestamp, rss, pss, uss, opss, activity, adj, foreground)

        Parameters
        ----------
        db : aiosqlite.Connection
            异步 SQLite 数据库连接对象。

        data_dir : str
            数据采样轮次标识（对应插入时的 data_dir 字段）。

        Returns
        -------
        tuple[list, list]
            两个列表分别为：
            - 前台数据列表（foreground = '前台'）
            - 后台数据列表（foreground = '后台'）
        """

        async def find(sql):
            async with db.execute(sql) as cursor:
                return await cursor.fetchall()

        fg_sql = f"""SELECT timestamp, rss, pss, uss, opss, activity, adj, foreground FROM memory_data
        WHERE foreground = '前台' and data_dir = '{data_dir}' and pss != ''
        """
        bg_sql = f"""SELECT timestamp, rss, pss, uss, opss, activity, adj, foreground FROM memory_data
        WHERE foreground = '后台' and data_dir = '{data_dir}' and pss != ''
        """

        fg_list, bg_list = await asyncio.gather(
            find(fg_sql), find(bg_sql)
        )

        return fg_list, bg_list


if __name__ == '__main__':
    pass
