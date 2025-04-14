#  __  __                     _
# |  \/  | ___ _ __ ___  _ __(_)_  __
# | |\/| |/ _ \ '_ ` _ \| '__| \ \/ /
# | |  | |  __/ | | | | | |  | |>  <
# |_|  |_|\___|_| |_| |_|_|  |_/_/\_\
#
# 版权所有 (c) 2024  Memrix(记忆星核)
# 此文件受 Memrix(记忆星核) 许可证的保护。您可以在 LICENSE.md 文件中查看详细的许可条款。
#
# Copyright (c) 2024  Memrix(记忆星核)
# This file is licensed under the Memrix(记忆星核) License. See the LICENSE.md file for more details.
#

# ====[ 内置模块 ]====
import os
import re
import sys
import time
import json
import typing
import signal
import shutil
import asyncio

# ====[ 第三方库 ]====
import aiosqlite
import uiautomator2

# ====[ from: 内置模块 ]====
from collections import defaultdict

# ====[ from: 第三方库 ]====
from loguru import logger

# ====[ from: 本地模块 ]====
from engine.device import Device
from engine.manage import Manage
from memnova import const
from memcore.parser import Parser
from memcore.display import Display
from engine.analyzer import Analyzer
from engine.tackle import (
    Config, Grapher, DataBase,
    Ram, MemrixError, FileAssist
)

try:
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
    import pygame
except ImportError:
    raise ImportError("AudioPlayer requires pygame. install it first.")


class ToolKit(object):
    """
    内存工具类，用于执行单位转换、数值计算与文本匹配等基础功能。

    Attributes
    ----------
    text_content : Optional[str]
        用于正则匹配的文本内容。可通过 `fit()` 方法执行查找与转换。
    """

    text_content: typing.Optional[str] = None

    @staticmethod
    def transform(number: typing.Any) -> float:
        """
        将任意数字（或可转换为数字的值）转换为以 KB 为单位的浮点数。

        Parameters
        ----------
        number : Any
            任意可被转换为 float 的值（通常为字节数或字符串表示的数字）。

        Returns
        -------
        float
            返回值为输入数值除以 1024 后的结果，精确到小数点后两位。
            若转换失败，则返回 0.00。
        """

        try:
            return round(float(number) / 1024, 2)
        except TypeError:
            return 0.00

    @staticmethod
    def addition(*numbers) -> float:
        """
        执行多个数值的加法求和。

        Parameters
        ----------
        *numbers : float or str
            任意数量的参数，每个都应可被转换为 float。

        Returns
        -------
        float
            所有数值之和，四舍五入保留两位小数。
            若存在无法转换的值，则返回 0.00。
        """

        try:
            return round(sum([float(number) for number in numbers]), 2)
        except TypeError:
            return 0.00

    @staticmethod
    def subtract(number_begin: typing.Any, number_final: typing.Any) -> float:
        """
        执行两个数值之间的减法操作。

        Parameters
        ----------
        number_begin : Any
            被减数，需可转换为 float。
        number_final : Any
            减数，需可转换为 float。

        Returns
        -------
        float
            差值结果，四舍五入保留两位小数。
            若任一参数无法转换为 float，则返回 0.00。
        """

        try:
            return round(float(number_begin) - float(number_final), 2)
        except TypeError:
            return 0.00

    def fit(self, pattern: typing.Union[str, "re.Pattern[str]"]) -> float:
        """
         使用正则表达式在 `text_content` 中提取匹配的第一个分组，并转换为 KB 单位。

         Parameters
         ----------
         pattern : str or Pattern[str]
             要匹配的正则表达式，可以是字符串或已编译的 re.Pattern。

         Returns
         -------
         float
             若匹配成功，返回分组内容转换为 KB 后的浮点值；
             若匹配失败或分组无效，返回 0.00。
         """

        return self.transform(find.group(1)) if (
            find := re.search(pattern, self.text_content, re.S)
        ) else 0.00


class Player(object):
    """
    音频播放工具类，用于异步播放本地音频文件。
    """

    @staticmethod
    async def audio(audio_file: str, *_, **__) -> None:
        """
        异步播放指定的音频文件（支持常见音频格式）。

        使用 pygame 的音频引擎进行加载与播放。函数在播放期间会阻塞，直到播放结束。
        适用于需要在异步流程中播放提示音或语音反馈的场景。

        Parameters
        ----------
        audio_file : str
            音频文件的路径，支持 `.mp3`, `.wav`, `.ogg` 等格式。

        *_ :
            占位参数，未使用。

        **__ :
            占位关键字参数，未使用。

        Returns
        -------
        None
            无返回值。方法在音频播放完成后自动退出。

        Notes
        -----
        - 本方法需在支持 asyncio 的事件循环中运行。
        - pygame 必须已正确初始化，并具备音频播放环境。
        - 音量默认设置为最大（1.0），可在必要时添加音量控制参数。
        - 若音频播放失败（如文件路径无效或格式不受支持），可能抛出 pygame 错误。
        """

        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)


class Memrix(object):
    """
    Memrix 核心控制类，用于协调内存采集（记忆风暴）、自动化测试（巡航引擎）和报告生成（真相快照）。

    类实例在初始化时根据运行模式自动构建工作路径、配置数据库与日志文件，
    并提供事件同步机制以支持异步任务的协同关闭。

    Attributes
    ----------
    file_insert : Optional[int]
        成功插入的采集数据条数，记录写入数据库的轮次数。

    file_folder : Optional[str]
        当前采集数据所属的文件夹名称，用于组织日志与中间输出。

    exec_start_event : asyncio.Event
        自动化任务开始的事件标记，供其他协程判断任务是否已启动。

    dump_close_event : asyncio.Event
        控制内存采集任务是否退出的同步事件。

    dumped : asyncio.Event
        内存采集任务单轮完成的标志，用于同步数据写入与下一轮调度。
    """

    file_insert: typing.Optional[int] = 0
    file_folder: typing.Optional[str] = ""

    exec_start_event: typing.Optional["asyncio.Event"] = asyncio.Event()

    dump_close_event: typing.Optional["asyncio.Event"] = asyncio.Event()

    dumped: typing.Optional["asyncio.Event"] = None

    def __init__(
            self,
            memory: typing.Optional[bool],
            script: typing.Optional[bool],
            report: typing.Optional[bool],
            *args,
            **kwargs
    ):
        """
        初始化 Memrix 实例，根据所选运行模式（memory/script/report）配置任务路径与环境变量。

        初始化过程包括文件目录创建、数据库路径设定、日志与 YAML 场景文件命名等，
        并绑定配置文件对象与模板路径。

        Parameters
        ----------
        memory : Optional[bool]
            是否启用内存采集任务（记忆风暴模式）。

        script : Optional[bool]
            是否启用 UI 自动化测试任务（巡航引擎模式）。

        report : Optional[bool]
            是否启用报告生成流程（真相快照模式）。

        *args :
            额外位置参数，约定第一个为 target（测试任务标识或包名）。

        **kwargs :
            命名参数集合，必须包含以下键：
            - src_total_place : str
                输出根目录（用于存放 Memory_Folder 等结构）。
            - template : str
                报告模板文件路径。
            - config : Config
                从配置文件中解析出的运行配置对象。
        """

        self.memory, self.script, self.report = memory, script, report

        self.target, self.folder, *_ = args

        self.src_total_place: str = kwargs["src_total_place"]
        self.template: str = kwargs["template"]
        self.config: "Config" = kwargs["config"]

        if self.report:
            folder: str = self.target
        else:
            self.before_time = time.time()
            folder: str = self.folder if self.folder else (
                time.strftime("%Y%m%d%H%M%S", time.localtime(self.before_time))
            )

        self.total_dir = os.path.join(self.src_total_place, f"Memory_Folder")
        self.other_dir = os.path.join(self.src_total_place, self.total_dir, f"Subset")
        self.group_dir = os.path.join(self.src_total_place, self.other_dir, folder)

        self.db_file = os.path.join(self.src_total_place, self.total_dir, f"memory_data.db")
        self.log_file = os.path.join(self.group_dir, f"log_{folder}.log")
        self.team_file = os.path.join(self.group_dir, f"team_{folder}.yaml")

    def clean_up(self, *_, **__) -> None:
        """
        异步触发内存采集任务的收尾流程。

        该方法可在外部逻辑（如 UI 自动化任务结束）中调用，用于通知内存拉取逻辑停止，
        并调度关闭流程 `dump_task_close()`。本方法本身不等待任务执行完成，仅注册关闭任务。

        Parameters
        ----------
        *_ :
            占位参数，未使用。

        **__ :
            占位关键字参数，未使用。

        Returns
        -------
        None
            无返回值。调用后会异步调度关闭操作。
        """

        loop = asyncio.get_running_loop()
        loop.create_task(self.dump_task_close())

    async def dump_task_close(self) -> None:
        """
        关闭内存采样任务，释放资源并触发报告生成。

        该方法通常在用户中断（Ctrl+C）或任务完成后调用，执行以下流程：
        - 通知设备检查任务退出（设置事件）
        - 通知采样任务退出（设置事件）
        - 等待最后一次内存采样写入完成
        - 取消所有后台 asyncio 任务
        - 输出日志（采样次数、耗时等）

        Returns
        -------
        None
            无返回值，作为清理收尾动作。
        """

        self.dump_close_event.set()

        if self.dumped:
            Grapher.view(f"[#00AFFF]等待任务结束 ...")
            await self.dumped.wait()  # 等待本轮拉取完成

        try:
            # 退出所有任务
            await asyncio.gather(
                *(asyncio.to_thread(task.cancel) for task in asyncio.all_tasks())
            )
        except asyncio.CancelledError:
            Grapher.view(f"[#00AFFF]任务已经退出 ...")

        time_cost = (time.time() - self.before_time) / 60
        logger.info(
            f"Mark={self.config.label} File={self.file_folder} Data={self.file_insert} Time={time_cost:.2f}"
        )
        logger.info(f"{self.group_dir}")

        if self.file_insert:
            Display.build_file_tree(self.group_dir)
            Grapher.view(
                f"Usage: [#00D787]{const.APP_NAME} --report --target [#FFAF87]{os.path.basename(self.group_dir)}[/]"
            )

        logger.info(f"^===^ {const.APP_DESC} Engine Close ^===^")

    # """记忆风暴"""
    async def dump_task_start(self, device: "Device", deliver_package: typing.Optional[str] = None) -> None:
        """
        启动内存数据拉取任务（记忆风暴模式），定时采集目标应用的内存状态，并写入本地数据库。

        方法内部包含多级流程，包括：
        - 设备 PID / UID / Activity 状态获取
        - 内存快照解析（PSS、RSS、USS、SWAP、Graphics 等）
        - 多进程内存合并与结构构建
        - 数据持久化（使用 SQLite）
        - 文件结构与任务标识管理

        内部定义的协程包括：
        - `flash_memory(pid)`：对单个 PID 进行内存解析与归类
        - `flash_memory_launch()`：执行一次完整的采集流程，并组织入库结构

        采集周期由配置文件中的 `config.speed` 控制，任务会持续运行直到 `dump_close_event` 被触发。

        Parameters
        ----------
        device : Device
            目标设备对象，需实现 memory_info、pid_value、uid_value、adj_value、act_value 等接口方法。

        deliver_package : typing.Optional[str]
            可以传入的应用包名。

        Returns
        -------
        None
            异步执行，无返回值。函数结束表示内存拉取流程被主动中断或关闭。

        Raises
        ------
        MemrixError
            当目标包无法识别，或采集初始化失败时抛出异常。

        Notes
        -----
        - 拉取结果会写入数据库文件：`memory_data.db`
        - 每一轮采集完成后会写入日志，并更新进度统计
        - 日志与数据目录按时间命名，支持场景标记（YAML）
        - 多进程结构通过 `defaultdict()` 聚合并转换为嵌套字典
        - 如果 YAML 场景文件已存在，当前轮次将追加入 file 列表中

        Examples
        --------
        memrix = Memrix(memory=True, script=False, report=False, ..., config=...)
        await memrix.dump_task_start(device)
        """

        async def flash_memory(pid: str) -> typing.Optional[dict[str, dict]]:
            """
            拉取并解析指定进程（PID）的内存信息。

            调用设备的 `memory_info()` 接口获取完整原始内存数据（/proc/pid 等），
            解析后提取三大内存映射结构：

            - resume_map：汇总性指标（USS、RSS、PSS、Graphics、SWAP 等）
            - memory_map：详细结构（Native Heap、mmap 分段等）
            - memory_vms：VMS 估值（通过 pkg_value 拉取）

            使用正则表达式提取文本内容，结合 `ToolKit.fit()` 进行数据清洗与单位转换。

            Parameters
            ----------
            pid : str
                目标进程的 PID，用于获取应用的内存快照。

            Returns
            -------
            Optional[dict[str, dict]]
                包含三个键的字典（resume_map, memory_map, memory_vms）。
                若内存数据拉取失败，则返回 None。

            Notes
            -----
            - 使用多个正则表达式进行分段提取，并做空值过滤与容错
            - 支持识别 "App Summary" 与 "TOTAL" 结构
            - 采集结果为标准化后的数值映射（单位为 MB，四舍五入）
            """

            if not (memory := await device.memory_info(package)):
                return None

            logger.info(f"Dump memory [{pid}] - [{package}]")
            resume_map: dict = {}
            memory_map: dict = {}
            memory_vms: dict = {}

            if match_memory := re.search(r"(\*\*.*?TOTAL (?:\s+\d+){8})", memory, re.S):
                toolkit.text_content = (clean_memory := re.sub(r"\s+", " ", match_memory.group()))

                for element in [
                    "Native Heap", "Dalvik Heap", "Dalvik Other", "Stack", "Ashmem", "Other dev",
                    ".so mmap", ".jar mmap", ".apk mmap", ".ttf mmap", ".dex mmap", ".oat mmap", ".art mmap",
                    "Other mmap", "GL mtrack", "Unknown"
                ]:
                    memory_map[element] = toolkit.fit(f"{element} .*?(\\d+)")

                if total_memory := re.search(r"TOTAL.*\d+", clean_memory, re.S):
                    if part := total_memory.group().split():
                        resume_map["TOTAL USS"] = toolkit.transform(part[2])

            if match_resume := re.search(r"App Summary.*?TOTAL SWAP.*(\d+)", memory, re.S):
                toolkit.text_content = re.sub(r"\s+", " ", match_resume.group())

                resume_map["Graphics"] = toolkit.fit("Graphics: .*?(\\d+)")
                resume_map["TOTAL RSS"] = toolkit.fit("TOTAL RSS: .*?(\\d+)")
                resume_map["TOTAL PSS"] = toolkit.fit("TOTAL PSS: .*?(\\d+)")
                resume_map["TOTAL SWAP"] = toolkit.fit("TOTAL SWAP.*(\\d+)")

                resume_map["OPSS"] = toolkit.subtract(resume_map["TOTAL PSS"], resume_map["Graphics"])

            memory_vms["vms"] = toolkit.transform(await device.pkg_value(pid))

            return {"resume_map": resume_map, "memory_map": memory_map, "memory_vms": memory_vms}

        async def flash_memory_launch() -> None:
            """
            执行一轮完整的内存采集任务流程（包括应用状态 & 多进程内存分析）。

            步骤如下：
            1. 获取应用 PID 列表（支持多进程）
            2. 获取 UID / ADJ / ACT 状态信息
            3. 并发执行 `flash_memory(pid)`，合并所有结果
            4. 构建标准结构 Ram 对象
            5. 插入数据库并打印采集结果

            采集完成后自动触发 `self.dumped.set()`，用于通知主控制循环进入下一轮。

            Returns
            -------
            None
                无返回值，任务完成后直接更新数据记录与标志位。

            Notes
            -----
            - 使用 `asyncio.gather()` 并发拉取进程数据
            - 使用 `defaultdict()` 对结果进行多进程合并，保证结构完整性
            - 使用 `Ram(...)` 对象包装采集结果用于入库
            - 若数据不完整，将跳过插入并记录日志
            """

            self.dumped.clear()

            dump_start_time = time.time()

            if not (app_pid := await device.pid_value(package)):
                self.dumped.set()
                return logger.info(f"Process={app_pid}\n")

            logger.info(device)
            logger.info(f"Process={app_pid.member}")

            if not all(current_info_list := await asyncio.gather(
                    device.adj_value(list(app_pid.member.keys())[0]), device.act_value()
            )):
                self.dumped.set()
                return logger.info(f"{current_info_list}\n")

            adj, act = current_info_list

            uid = uid if (uid := await device.uid_value(package)) else 0

            remark_map = {"tms": time.strftime("%Y-%m-%d %H:%M:%S")}
            remark_map.update({"uid": uid, "adj": adj, "act": act})
            remark_map.update({"frg": "前台" if self.target in act else "前台" if int(adj) <= 0 else "后台"})

            logger.info(f"{remark_map['tms']}")
            logger.info(f"UID: {remark_map['uid']}")
            logger.info(f"ADJ: {remark_map['adj']}")
            logger.info(f"{remark_map['act']}")
            logger.info(f"{remark_map['frg']}")

            for k, v in app_pid.member.items():
                remark_map.update({"pid": k + " - " + v})

            if all(memory_result := await asyncio.gather(
                    *(flash_memory(k) for k in list(app_pid.member.keys()))
            )):
                """
                合并多个进程的 memory_result 结果，按 key 分类累加字段值。

                适用于多进程采样场景：
                - 每个 result 是结构为 {"resume_map": {...}, "memory_map": {...}} 的字典
                - 对每一类 map 中的数值字段执行逐字段加和

                使用双层 defaultdict(float) 结构自动初始化字段，避免 KeyError。

                最终返回结构为：
                {
                    "resume_map": {
                        "TOTAL PSS": float,
                        "TOTAL RSS": float,
                        ...
                    },
                    "memory_map": {
                        "Native Heap": float,
                        ...
                    },
                    ...
                }
                """

                # 使用双层 defaultdict 构建合并容器
                muster = defaultdict(lambda: defaultdict(float))
                # 遍历所有进程的 memory_result（每项包含多个子映射：resume_map、memory_map 等）
                for result in memory_result:
                    for key, value in result.items():
                        for k, v in value.items():
                            # 对同一个字段名累加所有进程的值（如 TOTAL PSS）
                            muster[key][k] += v
                # 将内部 defaultdict 转换为普通 dict 结构，便于后续使用（如插入数据库、写入 YAML）
                muster = {k: dict(v) for k, v in muster.items()}
            else:
                self.dumped.set()
                return logger.info(f"{memory_result}\n")

            try:
                logger.info(muster["resume_map"].copy() | {"VmRss": muster["memory_vms"]["vms"]})
            except KeyError:
                return self.dumped.set()

            ram = Ram({"remark_map": remark_map} | muster)

            if all(maps := (ram.remark_map, ram.resume_map, ram.memory_map)):
                await DataBase.insert_data(
                    db, self.file_folder, self.config.label, *maps, ram.memory_vms
                )
                self.file_insert += 1
                logger.info(f"Article {self.file_insert} data insert success")
            else:
                logger.info(f"Data insert skipped")

            self.dumped.set()
            return logger.info(f"{time.time() - dump_start_time:.2f} s\n")

        package: typing.Optional[str] = self.target  # 传入的应用名称

        if not deliver_package:
            if "Unable" in (check := await device.examine_package(package)):
                raise MemrixError(check)

        logger.add(self.log_file, level="INFO", format=const.LOG_FORMAT)

        logger.info(f"^===^ {const.APP_DESC} Engine Start ^===^")
        format_before_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.before_time))

        self.file_insert = 0
        self.file_folder = f"DATA_{time.strftime('%Y%m%d%H%M%S')}"

        logger.info(f"时间: {format_before_time}")
        logger.info(f"应用: {package}")
        logger.info(f"频率: {self.config.speed}")
        logger.info(f"标签: {self.config.label}")
        logger.info(f"文件: {self.file_folder}\n")

        if os.path.isfile(self.team_file):
            scene = await asyncio.to_thread(FileAssist.read_yaml, self.team_file)
            scene["file"].append(self.file_folder)
        else:
            scene = {
                "time": format_before_time, "mark": device.serial, "file": [self.file_folder]
            }
        dump_file_task = asyncio.create_task(
            asyncio.to_thread(FileAssist.dump_yaml, self.team_file, scene)
        )

        if not os.path.exists(self.other_dir):
            os.makedirs(self.other_dir, exist_ok=True)

        toolkit: typing.Optional["ToolKit"] = ToolKit()

        self.dumped = asyncio.Event()

        async with aiosqlite.connect(self.db_file) as db:
            await DataBase.create_table(db)
            await dump_file_task
            self.exec_start_event.set()
            while not self.dump_close_event.is_set():
                await flash_memory_launch()
                await asyncio.sleep(self.config.speed)

    # """巡航引擎"""
    async def exec_task_start(self, device: "Device") -> None:
        """
        执行自动化脚本任务（巡航引擎），按 JSON 文件中的流程指令驱动设备操作，并并行进行内存采集。

        支持的自动化指令包括：
        - `u2`：调用 uiautomator2 的控件操作接口
        - `sleep`：等待延时
        - `audio`：播放音频反馈（通过 Player.audio 实现）

        该方法将从指定的 JSON 文件中解析：
        - 循环次数（loopers）
        - 应用包名（package）
        - 对应任务组（由配置文件中的 `group` 指定）

        脚本执行过程中，会并行启动内存采集任务（`dump_task_start()`），
        并在主控流程结束后主动关闭采集任务。

        Parameters
        ----------
        device : Device
            被测试设备对象，需支持 u2_active、examine_package、u2/sleep 等命令映射接口。

        Returns
        -------
        None
            异步执行，无返回值。执行完成后自动关闭内存采集任务。

        Raises
        ------
        MemrixError
            - 当 JSON 文件缺失、字段不合法、数据类型错误
            - 当设备连接失败或包名无效
            - 当任务组名称不存在或解析失败

        Notes
        -----
        - 使用 asyncio 并发机制启动内存拉取任务
        - 所有指令通过 `getattr()` 动态调用：支持扩展其他命令类型
        - 使用 `Grapher.view()` 记录每一步执行命令和返回值
        - 主流程执行完毕后主动调用 `dump_task_close()` 清理资源

        Examples
        --------
        config.group = "mission"
        # 脚本结构：
        # {
        #   "loopers": 3,
        #   "package": "com.example.app",
        #   "mission": {
        #       "step1": [{"cmds": "u2", "vals": [...], "args": [...], "kwds": {...}}],
        #       ...
        #   }
        # }

        await memrix.exec_task_start(device)
        """

        try:
            open_file = await asyncio.to_thread(FileAssist.read_json, self.target)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise MemrixError(e)

        try:
            assert (loopers := int(open_file["loopers"])), f"循环次数为空 {loopers}"
            assert (package := open_file["package"]), f"包名为空 {package}"
            assert (mission := open_file[self.config.group]), f"脚本文件为空 {mission}"
        except (AssertionError, KeyError, TypeError) as e:
            raise MemrixError(e)

        if "Unable" in (check := await device.examine_package(package)):
            raise MemrixError(check)

        try:
            await device.u2_active()
        except (uiautomator2.exceptions.DeviceError, uiautomator2.exceptions.ConnectError) as e:
            raise MemrixError(e)

        auto_dump_task = asyncio.create_task(self.dump_task_start(device, package))

        player: "Player" = Player()

        """
        执行 JSON 自动化任务脚本中的所有命令。

        每个任务循环 loopers 次，任务脚本结构为：
        {
            "loopers": 10,
            "package": com.example.app,
            "mission": {
                "step1": [
                    {"cmds": "u2", "vals": [...], "args": [...], "kwds": {...}},
                    {"cmds": "audio", "vals": [...]},
                    ...
                ]
            }
        }

        支持命令类型：
        - u2    -> 通过 uiautomator2 执行 UI 控制命令
        - sleep -> 延迟（异步等待）
        - audio -> 播放音频片段

        每条命令会根据类型选择目标对象（device 或 player），
        并执行对应方法，打印带参数的运行结果日志。
        """
        logger.info(f"^* Exec Start *^")
        # 外层循环，控制任务执行次数（loopers 次）
        for data in range(loopers):
            # 遍历 JSON 脚本中每个任务组（如 click、input、swipe 等）
            for key, values in mission.items():
                # 遍历该任务组内的每条指令
                for i in values:
                    # 提取命令类型（cmds），并检查是否在支持的类型列表中
                    if not (cmds := i.get("cmds", None)) or cmds not in ["u2", "sleep", "audio"]:
                        continue
                    # 根据 cmds 类型选择对应执行对象（device 或 player），获取方法引用
                    if callable(func := getattr(player if cmds == "audio" else device, cmds)):
                        # 提取参数：位置参数 vals、额外 args、关键字参数 kwds
                        vals, args, kwds = i.get("vals", []), i.get("args", []), i.get("kwds", {})
                        # 打印即将执行的函数与参数，并异步执行该方法
                        Grapher.view(
                            f"[#AFD7FF]{func.__name__} {vals} {args} {kwds} -> {await func(*vals, *args, **kwds)}"
                        )

        await self.dump_task_close()

        auto_dump_task.cancel()
        try:
            await auto_dump_task
        except asyncio.CancelledError:
            logger.info(f"^* Exec Close *^")

    # """真相快照"""
    async def create_report(self) -> None:
        """
        生成内存测试报告（真相快照），基于数据库与中间缓存构建完整 HTML 分析结果。

        本方法会执行以下步骤：
        1. 验证采集数据（数据库、日志、任务标记文件）是否存在
        2. 读取 YAML 场景文件，获取所有已记录数据目录
        3. 使用 `Analyzer.draw_memory()` 渲染每一轮数据的统计图与数值结果
        4. 汇总所有测试轮次的前后台内存指标均值、峰值
        5. 调用 `Analyzer.form_report()` 根据模板生成最终报告页面

        报告结构将包含：
        - 测试信息（时间、设备、任务标签、评价标准）
        - 每轮数据对比分析图（柱状图、折线图等）
        - 总体统计：前台/后台峰值、均值
        - 数据详情列表（每轮一项）

        Returns
        -------
        None
            异步执行，无返回值。成功后将在报告目录中生成 HTML 文件。

        Raises
        ------
        MemrixError
            - 当所需文件不存在或路径错误
            - 当 YAML 场景中无采集数据记录
            - 当报告数据生成失败或为空

        Notes
        -----
        - 场景文件由 `dump_task_start()` 创建，每轮采集结束追加记录
        - 最终报告文件路径为：`{group_dir}/Report_{group_dir_name}/index.html`
        - 使用配置对象中的 `template`, `criteria`, `headline` 等参数进行个性化渲染
        - 报告内容适用于浏览器查看，也可导出为 PDF

        Examples
        --------
        await memrix.create_report()
        """

        for file in [self.db_file, self.log_file, self.team_file]:
            try:
                assert os.path.isfile(file), f"文件无效 {file}"
            except AssertionError as e:
                raise MemrixError(e)

        async with aiosqlite.connect(self.db_file) as db:
            analyzer = Analyzer(
                db, os.path.join(self.group_dir, f"Report_{os.path.basename(self.group_dir)}")
            )

            team_data = await asyncio.to_thread(FileAssist.read_yaml, self.team_file)
            if not (memory_data_list := team_data["file"]):
                raise MemrixError(f"No data scenario {memory_data_list} ...")

            if not (report_list := await asyncio.gather(
                    *(analyzer.draw_memory(data_dir) for data_dir in memory_data_list)
            )):
                raise MemrixError(f"No data scenario {report_list} ...")

            # 计算多组数据前台峰值
            avg_fg_max_values = [float(i["fg_max"]) for i in report_list if "fg_max" in i]
            avg_fg_max = f"{sum(avg_fg_max_values) / len(avg_fg_max_values):.2f}" if avg_fg_max_values else None
            # 计算多组数据前台均值
            avg_fg_avg_values = [float(i["fg_avg"]) for i in report_list if "fg_avg" in i]
            avg_fg_avg = f"{sum(avg_fg_avg_values) / len(avg_fg_avg_values):.2f}" if avg_fg_avg_values else None

            # 计算多组数据后台峰值
            avg_bg_max_values = [float(i["bg_max"]) for i in report_list if "bg_max" in i]
            avg_bg_max = f"{sum(avg_bg_max_values) / len(avg_bg_max_values):.2f}" if avg_bg_max_values else None
            # 计算多组数据后台均值
            avg_bg_avg_values = [float(i["bg_avg"]) for i in report_list if "bg_avg" in i]
            avg_bg_avg = f"{sum(avg_bg_avg_values) / len(avg_bg_avg_values):.2f}" if avg_bg_avg_values else None

            rendering = {
                "title": f"{const.APP_DESC} Information",
                "major": {
                    "time": team_data["time"],
                    "headline": self.config.headline,
                    "criteria": self.config.criteria,
                },
                "level": {
                    "fg_max": f"{self.config.fg_max:.2f}", "fg_avg": f"{self.config.fg_avg:.2f}",
                    "bg_max": f"{self.config.bg_max:.2f}", "bg_avg": f"{self.config.bg_avg:.2f}",
                },
                "average": {
                    "avg_fg_max": avg_fg_max, "avg_fg_avg": avg_fg_avg,
                    "avg_bg_max": avg_bg_max, "avg_bg_avg": avg_bg_avg,
                },
                "report_list": report_list
            }
            return await analyzer.form_report(self.template, **rendering)


async def main() -> typing.Optional[typing.Any]:
    """
    Memrix 命令行工具的主执行入口。

    根据命令行参数解析执行不同的操作模式，包括：
    - `--memory`：启动记忆风暴模式，持续拉取设备内存状态
    - `--script`：启动巡航引擎模式，执行 UI 自动化测试脚本
    - `--report`：生成 HTML 内存报告（真相快照）
    - `--config`：打开配置文件编辑器，并显示当前配置

    如果未指定参数，则显示帮助信息；如未检测到 ADB 环境，将抛出异常。

    Returns
    -------
    Optional[Any]
        根据所选模式返回不同结果（通常无返回值或为任务句柄）；如无参数则返回帮助输出。

    Raises
    ------
    MemrixError
        - 若未配置 ADB 环境变量
        - 无连接设备
        - 若未传入有效命令
        - 若 `--target` 参数缺失但 memory/script/report 被调用

    Notes
    -----
    - 在 `--memory` 与 `--script` 模式中，注册了 SIGINT (Ctrl+C) 信号监听以触发资源清理
    - 内部通过 `Memrix` 类组合并调度各个子模块的异步操作
    - 所有参数来自 `_cmd_lines`，配置来自 `_config.configs`

    Examples
    --------
    # 打开配置编辑器
    $ memrix --config

    # 启动内存采集任务
    $ memrix --memory --target com.example.app

    # 执行自动化测试任务
    $ memrix --script --target example.json

    # 生成测试报告
    $ memrix --report --target 20240405123000
    """

    if len(sys.argv) == 1:
        return _parser.parse_engine.print_help()

    if not shutil.which("adb"):
        raise MemrixError(f"ADB 环境变量未配置 ...")

    if _cmd_lines.config:
        Display.show_logo()
        Display.show_license()

        Display.build_file_tree(_config_file)
        Grapher.console.print("\n")
        Grapher.console.print_json(data=_config.configs)
        return await FileAssist.open(_config_file)

    if any((memory := _cmd_lines.memory, script := _cmd_lines.script, report := _cmd_lines.report)):
        if not (target := _cmd_lines.target):
            raise MemrixError(f"--target 参数不能为空 ...")

        Display.show_logo()
        Display.show_license()

        memrix = Memrix(
            memory, script, report, target, _cmd_lines.folder, **_keywords
        )

        if memory:
            if not (device := await Manage.operate_device(_cmd_lines.serial)):
                raise MemrixError(f"没有连接设备 ...")
            signal.signal(signal.SIGINT, memrix.clean_up)
            return await memrix.dump_task_start(device)

        elif script:
            if not (device := await Manage.operate_device(_cmd_lines.serial)):
                raise MemrixError(f"没有连接设备 ...")
            signal.signal(signal.SIGINT, memrix.clean_up)
            return await memrix.exec_task_start(device)

        elif report:
            return await memrix.create_report()

    raise MemrixError(f"主命令不能为空 ...")


if __name__ == '__main__':
    #   __  __                     _        ____  _             _
    #  |  \/  | ___ _ __ ___  _ __(_)_  __ / ___|| |_ __ _ _ __| |_ ___ _ __
    #  | |\/| |/ _ \ '_ ` _ \| '__| \ \/ / \___ \| __/ _` | '__| __/ _ \ '__|
    #  | |  | |  __/ | | | | | |  | |>  <   ___) | || (_| | |  | ||  __/ |
    #  |_|  |_|\___|_| |_| |_|_|  |_/_/\_\ |____/ \__\__,_|_|   \__\___|_|
    #
    # 版权所有 (c) 2024  Memrix(记忆星核)
    # 此文件受 Memrix(记忆星核) 许可证的保护。您可以在 LICENSE.md 文件中查看详细的许可条款。
    #
    # Copyright (c) 2024  Memrix(记忆星核)
    # This file is licensed under the Memrix(记忆星核) License. See the LICENSE.md file for more details.
    #

    try:
        # 显示加载动画
        Display.show_animate()

        # 获取当前操作系统平台和应用名称
        _platform = sys.platform.strip().lower()
        _software = os.path.basename(os.path.abspath(sys.argv[0])).strip().lower()
        _sys_symbol = os.sep
        _env_symbol = os.path.pathsep

        # 激活日志
        Grapher.active("INFO")

        # 根据应用名称确定工作目录和配置目录
        if _software == f"{const.APP_NAME}.exe":
            # Windows
            _mx_work = os.path.dirname(os.path.abspath(sys.argv[0]))
            _mx_feasible = os.path.dirname(_mx_work)
        elif _software == f"{const.APP_NAME}":
            # MacOS
            _mx_work = os.path.dirname(sys.executable)
            _mx_feasible = os.path.dirname(_mx_work)
        elif _software == f"{const.APP_NAME}.py":
            # IDE
            _mx_work = os.path.dirname(os.path.abspath(__file__))
            _mx_feasible = _mx_work
        else:
            raise MemrixError(f"{const.APP_DESC} compatible with {const.APP_NAME} command")

        # 模板文件夹
        _template = os.path.join(_mx_work, const.SCHEMATIC, "templates", "memory.html")
        # 检查模板文件是否存在，如果缺失则显示错误信息并退出程序
        if not os.path.isfile(_template) and os.path.basename(_template).endswith(".html"):
            _tmp_name = os.path.basename(_template)
            raise MemrixError(f"{const.APP_DESC}  missing files {_tmp_name}")

        # 设置工具源路径
        _turbo = os.path.join(_mx_work, const.SCHEMATIC, "supports").format()

        # 根据平台设置工具路径
        if _platform == "win32":
            # Windows
            _npp = os.path.join(_turbo, "Windows", "npp_portable_mini", "notepad++.exe")
            # 将工具路径添加到系统 PATH 环境变量中
            os.environ["PATH"] = os.path.dirname(_npp) + _env_symbol + os.environ.get("PATH", "")
            # 检查工具是否存在，如果缺失则显示错误信息并退出程序
            if not shutil.which((_tls_name := os.path.basename(_npp))):
                raise MemrixError(f"{const.APP_DESC} missing files {_tls_name}")

        # 设置初始路径
        if not os.path.exists(
                _initial_source := os.path.join(_mx_feasible, "Specially").format()
        ):
            os.makedirs(_initial_source, exist_ok=True)

        # 设置报告路径
        if not os.path.exists(
                _src_total_place := os.path.join(_initial_source, "Memrix_Report").format()
        ):
            os.makedirs(_src_total_place, exist_ok=True)

        # 设置初始配置文件路径
        _config_file = os.path.join(_initial_source, "Memrix_Mix", "config.yaml")
        # 加载初始配置
        _config = Config(_config_file)

        # 命令行解析器
        _parser = Parser()
        # 命令行
        _cmd_lines = Parser().parse_cmd

        # 打包关键字参数
        _keywords = {
            "src_total_place": _src_total_place, "template": _template, "config": _config
        }

        asyncio.run(main())

    except MemrixError as _error:
        Grapher.view(_error)
        Display.show_fail()
        sys.exit(1)
    except KeyboardInterrupt:
        Display.show_exit()
        sys.exit(0)
    except asyncio.CancelledError:
        Display.show_done()
        sys.exit(0)
    else:
        Display.show_done()
        sys.exit(0)
