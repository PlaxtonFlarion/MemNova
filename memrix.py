#  __  __                     _
# |  \/  | ___ _ __ ___  _ __(_)_  __
# | |\/| |/ _ \ '_ ` _ \| '__| \ \/ /
# | |  | |  __/ | | | | | |  | |>  <
# |_|  |_|\___|_| |_| |_|_|  |_/_/\_\
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

# ====[ 内置模块 ]====
import os
import re
import sys
import json
import time
import typing
import signal
import shutil
import asyncio

# ====[ 第三方库 ]====
import aiosqlite
import uiautomator2.exceptions as u2exc

# ====[ from: 内置模块 ]====
from pathlib import Path
from collections import defaultdict

# ====[ from: 第三方库 ]====
from loguru import logger

# ====[ from: 本地模块 ]====
from engine.channel import (
    Channel, Messenger
)
from engine.device import Device
from engine.manage import Manage
from engine.tinker import (
    Active, Ram, FileAssist, MemrixError
)
from memcore import authorize
from memcore.cubicle import DataBase
from memcore.design import Design
from memcore.parser import Parser
from memcore.profile import Align
from memnova.analyzer import Analyzer
from memnova import const

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

    def __init__(self, opera_place: str, allowed_extra: list):
        self.opera_place = opera_place
        self.allowed_extra = allowed_extra

    async def audio(self, audio_file: str, *_, **__) -> None:
        """
        异步播放指定的音频文件（支持常见音频格式）。

        使用 pygame 的音频引擎进行加载与播放。函数在播放期间会阻塞，直到播放结束。
        适用于需要在异步流程中播放提示音或语音反馈的场景。

        Parameters
        ----------
        audio_file : str
            音频文件的路径，支持 `.mp3`, `.wav`, `.ogg` 等格式。

        Notes
        -----
        - 本方法需在支持 asyncio 的事件循环中运行。
        - pygame 必须已正确初始化，并具备音频播放环境。
        - 音量默认设置为最大（1.0），可在必要时添加音量控制参数。
        - 若音频播放失败（如文件路径无效或格式不受支持），可能抛出 pygame 错误。
        """
        voice = Path(audio_file)
        logger.info(f"Player -> {voice.name}")
        audio_file = await Api.synthesize(
            voice.stem, voice.suffix or const.WAVERS, self.opera_place, self.allowed_extra
        )

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
    """

    file_insert: typing.Optional[int] = 0
    file_folder: typing.Optional[str] = ""

    remote: dict = {}

    def __init__(self, storm: bool, pulse: bool, forge: bool, *args, **kwargs):
        """
        初始化核心控制器，配置运行模式、路径结构、分析状态与动画资源。
        """
        self.storm, self.pulse, self.forge = storm, pulse, forge

        self.focus, self.vault, self.watch, *_ = args

        self.src_opera_place: str = kwargs["src_opera_place"]
        self.src_total_place: str = kwargs["src_total_place"]
        self.template: str = kwargs["template"]
        self.align: "Align" = kwargs["align"]

        if self.forge:
            vault: str = self.focus
        else:
            self.before_time: float = time.time()
            vault: str = self.vault if self.vault else (
                time.strftime("%Y%m%d%H%M%S", time.localtime(self.before_time))
            )

        self.total_dir: str = os.path.join(self.src_total_place, const.TOTAL_DIR)
        self.other_dir: str = os.path.join(self.src_total_place, self.total_dir, const.SUBSET_DIR)
        self.group_dir: str = os.path.join(self.src_total_place, self.other_dir, vault)

        self.db_file: str = os.path.join(self.src_total_place, self.total_dir, const.DB_FILE)
        self.log_file: str = os.path.join(self.group_dir, f"{const.APP_NAME}_log_{vault}.log")
        self.team_file: str = os.path.join(self.group_dir, f"{const.APP_NAME}_team_{vault}.yaml")

        self.pad: str = "-" * 8
        self.memories: dict[str, typing.Union[str, int]] = {
            "msg": "*",
            "stt": "*",
            "act": "*",
            "pss": "*",
            "foreground": 0,
            "background": 0
        }
        self.design: "Design" = Design(self.watch)

        self.mistake: typing.Optional["Exception"] = None

        self.animation_task: typing.Optional["asyncio.Task"] = None

        self.exec_start_event: typing.Optional["asyncio.Event"] = asyncio.Event()
        self.closed: typing.Optional["asyncio.Event"] = None

        self.dump_close_event: typing.Optional["asyncio.Event"] = asyncio.Event()
        self.dumped: typing.Optional["asyncio.Event"] = None

    def clean_up(self, *_, **__) -> None:
        """
        异步触发内存采集任务的收尾流程。
        """
        self.dump_close_event.set()

    async def dump_task_close(self) -> None:
        """
        关闭内存采样任务，释放资源并触发报告生成。
        """
        if self.dumped and not self.dumped.is_set():
            logger.info(f"等待任务结束 ...")
            await self.dumped.wait()

        if self.closed and not self.closed.is_set():
            logger.info(f"等待流程结束 ...")
            await self.closed.wait()

        if self.animation_task:
            await self.animation_task

        time_cost = (time.time() - self.before_time) / 60
        logger.info(
            f"Mark={self.align.label} File={self.file_folder} Data={self.file_insert} Time={time_cost:.2f} m"
        )
        logger.info(f"{self.group_dir}")

        if self.file_insert:
            fc = Design.build_file_tree(self.group_dir)
            Design.Doc.log(
                f"Usage: [#00D787]{const.APP_NAME} --forge --focus [{fc}]{Path(self.group_dir).name}[/]"
            )

        logger.info(
            f"^*{self.pad} {const.APP_DESC} Engine Close {self.pad}*^"
        )

        Design.console.print()
        await self.design.system_disintegrate()

    # """记忆风暴"""
    async def dump_task_start(self, device: "Device", post_pkg: typing.Optional[str] = None) -> None:
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

        采集周期由配置文件控制，任务会持续运行直到 `dump_close_event` 被触发。

        Parameters
        ----------
        device : Device
            目标设备对象，需实现 memory_info、pid_value、uid_value、adj_value、act_value 等接口方法。

        post_pkg : typing.Optional[str]
            可以传入的应用包名。
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
            """
            if not (memory := await device.memory_info(package)):
                return None

            logger.info(f"Dump -> [{pid}] - [{package}]")
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
            """
            self.dumped.clear()

            dump_start_time = time.time()

            if not (app_pid := await device.pid_value(package)):
                self.dumped.set()
                self.memories.update({
                    "msg": (msg := f"Process -> {app_pid}"),
                    "stt": "*",
                    "act": "*",
                    "pss": "*"
                })
                return logger.info(f"{msg}\n")

            logger.info(device)
            self.memories.update({
                "msg": (msg := f"Process -> {app_pid.member}"),
            })
            logger.info(msg)

            if not all(current_info_list := await asyncio.gather(
                    device.adj_value(list(app_pid.member.keys())[0]), device.act_value()
            )):
                self.dumped.set()
                self.memories.update({
                    "msg": (msg := f"Info -> {current_info_list}"),
                    "stt": "*",
                    "act": "*",
                    "pss": "*"
                })
                return logger.info(f"{msg}\n")

            adj, act = current_info_list

            uid = uid if (uid := await device.uid_value(package)) else 0

            remark_map = {"tms": time.strftime("%Y-%m-%d %H:%M:%S")}

            remark_map.update({
                "uid": uid, "adj": adj, "act": act
            })
            remark_map.update({
                "frg": "前台" if self.focus in act else "前台" if int(adj) <= 0 else "后台"
            })

            state = "foreground" if remark_map["frg"] == "前台" else "background"
            self.memories.update({
                "stt": state,
                "act": act
            })

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
                self.memories.update({
                    "msg": (msg := f"Resp -> {memory_result}"),
                    "stt": "*",
                    "act": "*",
                    "pss": "*"
                })
                return logger.info(f"{msg}\n")

            try:
                logger.info(muster["resume_map"].copy() | {"VmRss": muster["memory_vms"]["vms"]})
            except KeyError:
                return self.dumped.set()

            ram = Ram({"remark_map": remark_map} | muster)

            if all(maps := (ram.remark_map, ram.resume_map, ram.memory_map)):
                await DataBase.insert_data(
                    db, self.file_folder, self.align.label, *maps, ram.memory_vms
                )
                self.file_insert += 1
                msg = f"Article {self.file_insert} data insert success"

                self.memories[state] += 1
                self.memories.update({
                    "pss": f"{ram.resume_map['TOTAL PSS']:.2f} MB"
                })

            else:
                msg = f"Data insert skipped"
                self.memories.update({
                    "stt": "*",
                    "act": "*",
                    "pss": "*"
                })

            self.memories.update({
                "msg": msg
            })
            logger.info(msg)

            self.dumped.set()
            return logger.info(f"{time.time() - dump_start_time:.2f} s\n")

        # Notes: Start from here
        package: typing.Optional[str] = post_pkg or self.focus

        if not post_pkg and not (check := await device.examine_pkg(package)):
            self.mistake = MemrixError(f"应用名称不存在 {package} -> {check}")
            return self.dump_close_event.set()

        logger.add(self.log_file, level=const.NOTE_LEVEL, format=const.WRITE_FORMAT)

        logger.info(
            f"^*{self.pad} {const.APP_DESC} Engine Start {self.pad}*^"
        )
        format_before_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.before_time))

        self.file_insert = 0
        self.file_folder = f"DATA_{time.strftime('%Y%m%d%H%M%S')}"

        logger.info(f"时间 -> {format_before_time}")
        logger.info(f"应用 -> {package}")
        logger.info(f"频率 -> {self.align.speed}")
        logger.info(f"标签 -> {self.align.label}")
        logger.info(f"文件 -> {self.file_folder}\n")

        await self.design.summaries(
            format_before_time, package, self.align.speed, self.align.label, self.file_folder
        )

        if os.path.isfile(self.team_file):
            scene = await FileAssist.read_yaml(self.team_file)
            scene["file"].append(self.file_folder)
        else:
            scene = {
                "time": format_before_time, "mark": device.serial, "file": [self.file_folder]
            }
        dump_file_task = asyncio.create_task(FileAssist.dump_yaml(self.team_file, scene))

        if not os.path.exists(self.other_dir):
            os.makedirs(self.other_dir, exist_ok=True)

        toolkit: typing.Optional["ToolKit"] = ToolKit()

        self.dumped = asyncio.Event()

        async with aiosqlite.connect(self.db_file) as db:
            await DataBase.create_table(db)
            await dump_file_task

            self.animation_task = asyncio.create_task(
                self.design.memory_wave(self.memories, self.dump_close_event)
            )

            self.exec_start_event.set()

            while not self.dump_close_event.is_set():
                await flash_memory_launch()
                await asyncio.sleep(self.align.speed)

    # """巡航引擎"""
    async def exec_task_start(self, device: "Device") -> None:
        """
        执行任务调度主流程，负责：
        - 加载焦点任务 JSON 配置；
        - 校验任务数据、应用是否安装；
        - 启动 UI 自动化服务；
        - 启动自动转储任务；
        - 根据 JSON 结构执行多轮命令任务；
        - 正确设置同步事件状态与错误追踪。

        Parameters
        ----------
        device : Device
            当前连接的目标设备对象，必须已初始化并可交互。

        Raises
        ------
        - 无直接 raise；所有错误通过设置 `self.mistake` 标记，并提前 return；
        - 支持如下异常的容错处理：
            - FileNotFoundError、AssertionError、json.JSONDecodeError 等文件读取/格式校验类；
            - u2.DeviceError、u2.ConnectError 设备连接类异常；
            - 包名不存在等业务校验错误。
        """
        try:
            open_file = await FileAssist.read_json(self.focus)

            assert (loopers := int(open_file["loopers"])), f"循环次数为空 {loopers}"
            assert (package := open_file["package"]), f"应用名称为空 {package}"
            assert (mission := open_file[self.align.group]), f"脚本文件为空 {mission}"
        except (FileNotFoundError, AssertionError, TypeError, ValueError, json.JSONDecodeError) as e:
            self.mistake = MemrixError(e)
            return self.dump_close_event.set()

        if not (check := await device.examine_pkg(package)):
            self.mistake = MemrixError(f"应用名称不存在 {package} -> {check}")
            return self.dump_close_event.set()

        try:
            await device.automator_activation()
        except (u2exc.DeviceError, u2exc.ConnectError) as e:
            self.mistake = MemrixError(e)
            return self.dump_close_event.set()

        allowed_extra_task = asyncio.create_task(Api.formatting())
        auto_dump_task = asyncio.create_task(self.dump_task_start(device, package))

        await self.exec_start_event.wait()

        allowed_extra = await allowed_extra_task or [const.WAVERS]
        player: "Player" = Player(self.src_opera_place, allowed_extra)

        self.closed = asyncio.Event()

        logger.info(f"^*{self.pad} Exec Start {self.pad}*^")

        for data in range(loopers):
            for key, value in mission.items():
                for i in value:
                    cmds = i.get("cmds", "")

                    self.closed.clear()
                    if callable(func := getattr(player if cmds == "audio" else device, cmds)):
                        vals, args, kwds = i.get("vals", []), i.get("args", []), i.get("kwds", {})

                        try:
                            logger.info(f"{func.__name__} Digital -> {vals} {args} {kwds}")
                            resp = await func(*vals, *args, **kwds)
                        except Exception as e:
                            logger.error(f"Mistake -> {e}")
                        else:
                            logger.info(f"{func.__name__} Returns -> {resp}")

                    else:
                        logger.info(f"Lost func -> {cmds}")
                    self.closed.set()

        self.dump_close_event.set()
        await auto_dump_task

        logger.info(f"^*{self.pad} Exec Close {self.pad}*^")

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

        Raises
        ------
        MemrixError
            - 当所需文件不存在或路径错误
            - 当 YAML 场景中无采集数据记录
            - 当报告数据生成失败或为空
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

            team_data = await FileAssist.read_yaml(self.team_file)
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
                    "headline": self.align.headline,
                    "criteria": self.align.criteria,
                },
                "level": {
                    "fg_max": f"{self.align.fg_max:.2f}", "fg_avg": f"{self.align.fg_avg:.2f}",
                    "bg_max": f"{self.align.bg_max:.2f}", "bg_avg": f"{self.align.bg_avg:.2f}",
                },
                "average": {
                    "avg_fg_max": avg_fg_max, "avg_fg_avg": avg_fg_avg,
                    "avg_bg_max": avg_bg_max, "avg_bg_avg": avg_bg_avg,
                },
                "report_list": report_list
            }
            return await analyzer.form_report(self.template, **rendering)


class Api(object):
    """
    Api

    通用异步接口适配器类，封装各类与远程服务交互的静态方法，包括数据获取、
    文件生成、命令配置加载等逻辑，适用于微服务通信、TTS 服务、自动化平台等场景。

    当前支持的服务包括语音格式元信息拉取、语音合成任务、业务用例命令获取等。
    所有接口方法均通过异步方式与后端 API 通信，支持 JSON 响应解析及异常处理。

    Notes
    -----
    - 提供统一的参数打包与请求流程，封装远程接口调用的细节。
    - 支持动态参数拼接、异常捕获、数据缓存与文件写入。
    - 可根据实际业务场景扩展其他静态方法，如上传日志、获取配置、拉取资源等。
    """

    @staticmethod
    async def ask_request_get(
        url: str, key: typing.Optional[str] = None, *_, **kwargs
    ) -> dict:
        """
        通用异步 GET 请求方法。

        构造带参数的异步 GET 请求，自动附带默认参数并发送到指定 URL。支持从响应中提取指定字段，
        用于统一的业务数据获取流程，如模板信息、配置元数据等。

        Parameters
        ----------
        url : str
            请求的目标接口地址。

        key : str, optional
            可选的响应字段键名，若提供则返回对应字段的内容，否则返回整个响应字典。

        *_
            保留参数，未使用。

        **kwargs
            追加到请求参数中的动态键值对，用于拼接请求 query 参数。

        Returns
        -------
        dict
            远程服务返回的 JSON 数据（或提取后的字段值）。

        Raises
        ------
        FramixError
            当请求失败、响应格式异常或字段不存在时，将在 `Messenger` 层抛出自定义异常。
        """
        params = Channel.make_params() | kwargs
        async with Messenger() as messenger:
            resp = await messenger.poke("GET", url, params=params)
            return resp.json()[key] if key else resp.json()

    @staticmethod
    async def formatting() -> typing.Optional[list]:
        """
        获取支持的语音合成格式列表。

        异步从远程服务获取格式信息，若发生异常则返回 None 并记录日志。

        Returns
        -------
        list or None
            成功时返回格式字符串列表，例如 ["mp3", "ogg", "webm"]；
            若请求失败则返回 None。

        Raises
        ------
        Exception
            当远程请求或解析失败时捕获并记录日志，返回 None。
        """
        params = Channel.make_params()
        try:
            async with Messenger() as messenger:
                resp = await messenger.poke("GET", const.SPEECH_META_URL, params=params)
                return resp.json()["formats"]
        except Exception as e:
            return logger.debug(e)

    @staticmethod
    async def profession(case: str) -> dict:
        """
        根据指定用例名从业务接口获取命令列表。

        通过异步请求远程业务系统，加载指定 case 的命令配置数据。

        Parameters
        ----------
        case : str
            用例名称，用于作为参数查询业务命令配置。

        Returns
        -------
        dict
            返回包含命令配置的字典组成结构。

        Raises
        ------
        FramixError
            当网络请求失败或响应异常时，将在外层调用中处理。
        """
        params = Channel.make_params() | {"case": case}
        async with Messenger() as messenger:
            resp = await messenger.poke("GET", const.BUSINESS_CASE_URL, params=params)
            return resp.json()

    @staticmethod
    async def synthesize(speak: str, waver: str, src_opera_place: str, allowed_extra: list) -> str:
        """
        合成语音音频文件。

        根据指定文本与音频格式生成语音文件，若已存在本地缓存则直接返回路径；
        否则通过远程接口获取下载链接并保存音频至本地。

        Parameters
        ----------
        speak : str
            要合成的语音内容。

        waver : str
            请求的音频格式后缀（如 'mp3'、'wav'）。

        allowed_extra : list
            支持的音频格式列表，仅这些格式会触发远程合成逻辑。

        src_opera_place : str
            本地语音文件根目录（将生成在其下的 VOICES 子目录中）。

        Returns
        -------
        str
            本地语音文件的绝对路径，或拼接后的默认字符串（当 waver 不被允许时）。
        """
        allowed_ext = {ext.lower().lstrip('.') for ext in allowed_extra}
        logger.debug(f"Allowed ext -> {allowed_ext}")

        # 清洗输入
        clean_speak = speak.strip()
        clean_waver = waver.strip().lower().lstrip(".")

        # 检查 speak 中是否包含扩展名
        match = re.search(r"\.([a-zA-Z0-9]{1,6})$", clean_speak)
        speak_ext = match.group(1).lower() if match else ""
        speak_stem = re.sub(r"\.([a-zA-Z0-9]{1,6})$", "", clean_speak)

        # 判断是否为音频请求
        if clean_waver in allowed_ext:
            final_speak = speak_stem
            final_waver = clean_waver
        elif speak_ext in allowed_ext:
            final_speak = speak_stem
            final_waver = speak_ext
        else:
            # 非音频请求，直接拼接返回
            combination = f"{clean_speak}.{clean_waver}" if clean_waver else clean_speak
            logger.debug(f"Non-audio request, combination -> {combination}")
            return combination

        # 构建文件名和本地缓存路径
        audio_name = str(Path(final_speak).with_suffix(f".{final_waver}"))

        if not (voices := Path(src_opera_place) / const.VOICES).exists():
            voices.mkdir(parents=True, exist_ok=True)

        if (audio_file := voices / audio_name).is_file():
            logger.debug(f"Local audio file: {audio_file}")
            return str(audio_file)

        # 构建 payload
        payload = {"speak": final_speak, "waver": final_waver} | Channel.make_params()
        logger.debug(f"Remote synthesize: {payload}")

        try:
            async with Messenger() as messenger:
                resp = await messenger.poke("POST", const.SPEECH_VOICE_URL, json=payload)
                logger.debug(f"Download url: {(download_url := resp.json()['url'])}")

                redis_or_r2_resp = await messenger.poke("GET", download_url)
                audio_file.write_bytes(redis_or_r2_resp.content)

        except Exception as e:
            logger.debug(e)

        return str(audio_file)

    @staticmethod
    async def remote_config() -> typing.Optional[dict]:
        """
        获取远程配置中心的全局配置数据。
        """
        try:
            config_data = await Api.ask_request_get(const.GLOBAL_CF_URL)
            auth_info = authorize.verify_signature(config_data)
        except Exception as e:
            return logger.debug(e)

        return auth_info.get("configuration", {})


# """Main"""
async def main() -> typing.Optional[typing.Any]:
    """
    主控制入口，用于解析命令行参数并根据不同模式执行配置展示、内存转储、脚本执行或报告生成等功能。
    """

    async def previewing() -> None:
        """
        预览对齐配置文件，若不存在则自动生成。
        """
        if not Path(align_file).exists():
            await align.dump_align()

        Design.build_file_tree(align_file)
        await FileAssist.open(align_file)
        await align.load_align()

        return Design.console.print_json(data=align.aligns)

    # Notes: Start from here
    Design.startup_logo()

    # 解析命令行参数
    parser = Parser()
    cmd_lines = Parser().parse_cmd

    # 如果没有提供命令行参数，则显示帮助文档，并退出程序
    if len(sys.argv) == 1:
        return parser.parse_engine.print_help()

    # 获取当前操作系统平台和应用名称
    platform = sys.platform.strip().lower()
    software = os.path.basename(os.path.abspath(sys.argv[0])).strip().lower()
    sys_symbol = os.sep
    env_symbol = os.path.pathsep

    # 根据应用名称确定工作目录和配置目录
    if software == f"{const.APP_NAME}.exe":
        mx_work = os.path.dirname(os.path.abspath(sys.argv[0]))
        mx_feasible = os.path.dirname(mx_work)
    elif software == f"{const.APP_NAME}":
        mx_work = os.path.dirname(sys.executable)
        mx_feasible = os.path.dirname(mx_work)
    elif software == f"{const.APP_NAME}.py":
        mx_work = os.path.dirname(os.path.abspath(__file__))
        mx_feasible = mx_work
    else:
        raise MemrixError(f"{const.APP_DESC} compatible with {const.APP_NAME} command")

    # 模板文件源路径
    src_templates = os.path.join(mx_work, const.SCHEMATIC, const.TEMPLATES).format()
    # 模板版本文件路径
    _ = os.path.join(src_templates, const.X_TEMPLATE_VERSION).format()
    # 模板文件路径
    template = os.path.join(src_templates, "memory.html")
    # 检查模板文件是否存在，如果缺失则显示错误信息并退出程序
    if not os.path.isfile(template) or not os.path.basename(template).endswith(".html"):
        tmp_name = os.path.basename(template)
        raise MemrixError(f"{const.APP_DESC} missing files {tmp_name}")

    # 设置工具源路径
    turbo = os.path.join(mx_work, const.SCHEMATIC, const.SUPPORTS).format()

    # 根据平台设置工具路径
    if platform == "win32":
        npp = os.path.join(turbo, "Windows", "npp_portable_mini", "notepad++.exe")
        # 将工具路径添加到系统 PATH 环境变量中
        os.environ["PATH"] = os.path.dirname(npp) + env_symbol + os.environ.get("PATH", "")
        # 检查工具是否存在，如果缺失则显示错误信息并退出程序
        if not shutil.which((tls_name := os.path.basename(npp))):
            raise MemrixError(f"{const.APP_DESC} missing files {tls_name}")

    # 初始文件夹路径
    if not os.path.exists(
        initial_source := os.path.join(mx_feasible, const.STRUCTURE).format()
    ):
        os.makedirs(initial_source, exist_ok=True)

    # 配置文件夹路径
    if not os.path.exists(
        src_opera_place := os.path.join(initial_source, const.SRC_OPERA_PLACE).format()
    ):
        os.makedirs(src_opera_place, exist_ok=True)

    # 报告文件夹路径
    if not os.path.exists(
        src_total_place := os.path.join(initial_source, const.SRC_TOTAL_PLACE).format()
    ):
        os.makedirs(src_total_place, exist_ok=True)

    # 激活日志
    Active.active(watch := "INFO" if cmd_lines.watch else "WARNING")

    # 设置初始配置文件路径
    align_file = os.path.join(initial_source, const.SRC_OPERA_PLACE, const.ALIGN)
    # 加载初始配置
    align = Align(align_file)

    if cmd_lines.align:
        return await previewing()

    lic_file = Path(src_opera_place) / const.LIC_FILE

    # 应用激活
    if apply_code := cmd_lines.apply:
        return await authorize.receive_license(apply_code, lic_file)

    # 授权校验
    await authorize.verify_license(lic_file)

    logger.info(f"{'=' * 15} 系统调试 {'=' * 15}")
    logger.info(f"操作系统: {platform}")
    logger.info(f"应用名称: {software}")
    logger.info(f"系统路径: {sys_symbol}")
    logger.info(f"环境变量: {env_symbol}")
    logger.info(f"日志等级: {watch}")
    logger.info(f"工具目录: {turbo}")
    logger.info(f"{'=' * 15} 系统调试 {'=' * 15}\n")

    await align.load_align()

    if any((storm := cmd_lines.storm, pulse := cmd_lines.pulse, forge := cmd_lines.forge)):
        if not (focus := cmd_lines.focus):
            raise MemrixError(f"--focus 参数不能为空 ...")

        keywords = {
            "src_opera_place": src_opera_place,
            "src_total_place": src_total_place,
            "template": template,
            "align": align
        }
        memrix = Memrix(
            storm, pulse, forge, focus, cmd_lines.vault, watch, **keywords
        )

        if storm or pulse:
            if not shutil.which("adb"):
                raise MemrixError(f"ADB 环境变量未配置 ...")

            if not (device := await Manage.operate_device(cmd_lines.imply)):
                raise MemrixError(f"没有连接设备 ...")

            signal.signal(signal.SIGINT, memrix.clean_up)

            global_config_task = asyncio.create_task(Api.remote_config())
            await Design.flame_manifest()
            memrix.remote = await global_config_task or {}

            main_task = asyncio.create_task(
                getattr(memrix, "dump_task_start" if storm else "exec_task_start")(device)
            )

            await memrix.dump_close_event.wait()

            if mistake := memrix.mistake:
                raise mistake

            await memrix.dump_task_close()
            main_task.cancel()
            return await main_task

        elif forge:
            await Design.doll_animation()
            return await memrix.create_report()

        else:
            return None

    else:
        raise MemrixError(f"主命令不能为空 ...")


# """Test"""
async def test() -> None:
    pass


if __name__ == '__main__':
    #   __  __                     _
    #  |  \/  | ___ _ __ ___  _ __(_)_  __
    #  | |\/| |/ _ \ '_ ` _ \| '__| \ \/ /
    #  | |  | |  __/ | | | | | |  | |>  <
    #  |_|  |_|\___|_| |_| |_|_|  |_/_/\_\
    #

    # asyncio.run(test())

    try:
        asyncio.run(main())
    except MemrixError as _error:
        Design.Doc.err(_error)
        Design.show_fail()
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(Design.show_exit())
    except asyncio.CancelledError:
        sys.exit(Design.show_done())
    else:
        sys.exit(Design.show_done())
