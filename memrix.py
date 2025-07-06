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
import stat
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
from perfetto.trace_processor import (
    TraceProcessor, TraceProcessorConfig
)

# ====[ from: 本地模块 ]====
from engine.device import Device
from engine.manage import Manage
from engine.medias import Player
from engine.terminal import Terminal
from engine.tinker import (
    Active, Ram, FileAssist, ToolKit, MemrixError
)
from memcore.api import Api
from memcore import authorize
from memcore.cubicle import Cubicle
from memcore.design import Design
from memcore.parser import Parser
from memcore.profile import Align
from memnova.analyzer import Analyzer
from memnova.reporter import Reporter
from memnova.tracer import Tracer
from memnova import const


class Memrix(object):
    """
    Memrix 核心控制类，用于协调内存采集（记忆风暴）、自动化测试（巡航引擎）和报告生成（真相快照）。

    类实例在初始化时根据运行模式自动构建工作路径、配置数据库与日志文件，
    并提供事件同步机制以支持异步任务的协同关闭。
    """

    file_insert: typing.Optional[int] = 0
    file_folder: typing.Optional[str] = ""

    __remote: dict = {}

    def __init__(self, remote: dict, *args, **kwargs):
        """
        初始化核心控制器，配置运行模式、路径结构、分析状态与动画资源。
        """
        self.remote: dict = remote or {}  # workflow: 远程全局配置

        self.sleek, self.storm, self.pulse, self.forge, *_ = args
        _, _, _, _, self.focus, self.vault, self.watch, *_ = args

        self.src_opera_place: str = kwargs["src_opera_place"]
        self.src_total_place: str = kwargs["src_total_place"]
        self.memory_template: str = kwargs["memory_template"]

        self.align: "Align" = kwargs["align"]

        self.adb: str = kwargs["adb"]
        self.perfetto: str = kwargs["perfetto"]
        self.tp_shell: str = kwargs["tp_shell"]

        self.ft_file: str = kwargs["ft_file"]

        self.padding: str = "-" * 8
        self.memories: dict[str, typing.Union[str, int]] = {
            "exc": "*",
            "msg": "*",
            "stt": "*",
            "act": "*",
            "pss": "*",
            "foreground": 0,
            "background": 0
        }
        self.design: "Design" = Design(self.watch)

        self.animation_task: typing.Optional["asyncio.Task"] = None

        self.exec_start_event: typing.Optional["asyncio.Event"] = asyncio.Event()
        self.task_close_event: typing.Optional["asyncio.Event"] = asyncio.Event()

        self.dumped: typing.Optional["asyncio.Event"] = None

    @property
    def remote(self) -> dict:
        return self.__remote

    @remote.setter
    def remote(self, value: dict) -> None:
        self.__remote = value

    def clean_up(self, *_, **__) -> None:
        """
        异步触发内存采集任务的收尾流程。
        """
        self.task_close_event.set()

    async def refresh(
            self,
            package: str,
            team_file: str,
            team_name: str,
            team_mark: str,
            team_time: float
    ) -> None:

        self.file_insert = 0
        self.file_folder = team_name

        format_before_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(team_time))

        logger.info(f"时间 -> {format_before_time}")
        logger.info(f"应用 -> {package}")
        logger.info(f"频率 -> {self.align.speed}")
        logger.info(f"标签 -> {self.align.label}")
        logger.info(f"文件 -> {self.file_folder}\n")

        await self.design.summaries(
            format_before_time, package, self.align.speed, self.align.label, self.file_folder
        )

        if Path(team_file).is_file():
            scene = await FileAssist.read_yaml(team_file)
            scene["file"].append(self.file_folder)
        else:
            scene = {
                "time": format_before_time, "mark": team_mark, "file": [self.file_folder]
            }
        await FileAssist.dump_yaml(team_file, scene)

    async def dump_task_close(self, before_time: float, group_dir: str) -> None:
        """
        关闭内存采样任务，释放资源并触发报告生成。
        """
        if self.dumped and not self.dumped.is_set():
            logger.info(f"等待任务结束 ...")
            try:
                await asyncio.wait_for(self.dumped.wait(), timeout=3)
            except asyncio.TimeoutError:
                logger.info("任务超时结束 ...")

        if self.animation_task:
            await self.animation_task

        time_cost = (time.time() - before_time) / 60
        logger.info(
            f"Mark={self.align.label} File={self.file_folder} Data={self.file_insert} Time={time_cost:.2f} m"
        )
        logger.info(f"{group_dir}")

        if self.file_insert:
            fc = Design.build_file_tree(group_dir)
            Design.Doc.log(
                f"Usage: [#00D787]{const.APP_NAME} --forge --focus [{fc}]{Path(group_dir).name}[/]"
            )

        logger.info(
            f"^*{self.padding} {const.APP_DESC} Engine Close {self.padding}*^"
        )

        Design.console.print()
        await self.design.system_disintegrate()

    # """记忆风暴"""
    async def dump_task_start(self, device: "Device", post_pkg: typing.Optional[str] = None) -> None:

        async def flash_memory(pid: str) -> typing.Optional[dict[str, dict]]:
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
                "frg": "前台" if package in act else "前台" if int(adj) <= 0 else "后台"
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
                muster = defaultdict(lambda: defaultdict(float))
                for result in memory_result:
                    for key, value in result.items():
                        for k, v in value.items():
                            muster[key][k] += v
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
                await Cubicle.insert_mem_data(db, self.file_folder, self.align.label, *maps, ram.memory_vms)
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

        # Notes: ========== Start from here ==========
        package = post_pkg or self.focus

        if not post_pkg and not (check := await device.examine_pkg(package)):
            raise MemrixError(f"应用名称不存在 {package} -> {check}")

        reporter = Reporter(self.src_total_place, self.vault, const.M_SUBSET_DIR)

        logger.add(reporter.log_file, level=const.NOTE_LEVEL, format=const.WRITE_FORMAT)

        logger.info(
            f"^*{self.padding} {const.APP_DESC} Engine Start {self.padding}*^"
        )

        team_name = f"MEM_DATA_{time.strftime('%Y%m%d%H%M%S')}"
        await self.refresh(
            package, reporter.team_file, team_name, device.serial, reporter.before_time
        )

        # Notes: ========== 启动工具 ==========
        toolkit: typing.Optional["ToolKit"] = ToolKit()

        self.dumped = asyncio.Event()

        async with aiosqlite.connect(reporter.db_file) as db:
            await Cubicle.create_mem_table(db)
            self.animation_task = asyncio.create_task(
                self.design.memory_wave(self.memories, self.task_close_event)
            )
            self.exec_start_event.set()
            while not self.task_close_event.is_set():
                await flash_memory_launch()
                await asyncio.sleep(self.align.speed)

        await self.dump_task_close(reporter.before_time, reporter.group_dir)

    # """巡航引擎"""
    async def exec_task_start(self, device: "Device") -> None:

        async def automatic() -> None:
            logger.info(f"^*{self.padding} Exec Start {self.padding}*^")

            for outer in range(open_file.get("loopers", 1)):
                for index, mission in enumerate(open_file.get("mission", [])):

                    for key, value in mission.items():
                        for inner in range(value.get("loopers", 1)):
                            for step in value.get("command", []):

                                cmds = step.get("cmds", "")
                                vals = step.get("vals", [])
                                args = step.get("args", [])
                                kwds = step.get("kwds", {})

                                target = player if cmds == "audio_player" else device

                                self.memories.update({"exc": f"{cmds} → {vals}, {args}, {kwds}"})

                                if callable(func := getattr(target, cmds, None)):
                                    try:
                                        logger.info(f"[{key}] Step {cmds} → {vals}, {args}, {kwds}")
                                        await func(*vals, *args, **kwds)
                                    except Exception as e:
                                        logger.info(f"[{key}] Failed {cmds}: {e}")
                                else:
                                    logger.info(f"[{key}] Unknown command: {cmds}")

            logger.info(f"^*{self.padding} Exec Close {self.padding}*^")
            self.task_close_event.set()

        # Notes: ========== Start from here ==========
        try:
            open_file = await FileAssist.read_json(self.focus)

            if not (_ := int(open_file.get("loopers", 0))):
                raise ValueError("循环次数为空")

            if not (package := open_file.get("package", "").strip()):
                raise ValueError("应用名称为空")

            if not (_ := open_file.get(self.align.group, [])):
                raise ValueError(f"脚本文件为空，未找到字段: {self.align.group}")

        except (FileNotFoundError, TypeError, ValueError, json.JSONDecodeError) as e_:
            raise MemrixError(e_)

        if not (check := await device.examine_pkg(package)):
            raise MemrixError(f"应用名称不存在 {package} -> {check}")

        try:
            await device.automator_activation()
        except (u2exc.DeviceError, u2exc.ConnectError) as e_:
            raise MemrixError(e_)

        allowed_extra_task = asyncio.create_task(Api.formatting())

        if self.storm:
            function = self.dump_task_start
        elif self.sleek:
            function = self.frame_tracer
        else:
            raise MemrixError("<UNK>")

        auto_exec_task = asyncio.create_task(function(device, package))

        await self.exec_start_event.wait()

        allowed_extra = await allowed_extra_task or [const.WAVERS]
        player: "Player" = Player(self.src_opera_place, allowed_extra)

        automatic_task = asyncio.create_task(automatic())

        await self.task_close_event.wait()

        automatic_task.cancel()
        try:
            await automatic_task
        except asyncio.CancelledError:
            logger.info(f"Automated task completed ...")

        await auto_exec_task

    # """真相快照"""
    async def create_mem_report(self) -> None:
        reporter = Reporter(self.src_total_place, self.focus, const.M_SUBSET_DIR)

        for file in [reporter.db_file, reporter.log_file, reporter.team_file]:
            if not Path(file).is_file():
                raise MemrixError(f"文件无效 {file}")

        async with aiosqlite.connect(reporter.db_file) as db:
            analyzer = Analyzer(
                db, os.path.join(reporter.group_dir, f"Report_{Path(reporter.group_dir).name}")
            )

            team_data = await FileAssist.read_yaml(reporter.team_file)
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
            return await analyzer.form_report(self.memory_template, **rendering)

    # Notes: 流畅度测试
    async def frame_tracer(self, device: "Device", post_pkg: typing.Optional[str] = None) -> None:
        # Notes: ========== Start from here ==========
        package = post_pkg or self.focus

        if not post_pkg and not (check := await device.examine_pkg(package)):
            raise MemrixError(f"应用名称不存在 {package} -> {check}")

        reporter = Reporter(self.src_total_place, self.vault, const.F_SUBSET_DIR)

        logger.add(reporter.log_file, level=const.NOTE_LEVEL, format=const.WRITE_FORMAT)

        logger.info(
            f"^*{self.padding} {const.APP_DESC} Engine Start {self.padding}*^"
        )

        team_name = f"GFX_DATA_{time.strftime('%Y%m%d%H%M%S')}"
        await self.refresh(
            package, reporter.team_file, team_name, device.serial, reporter.before_time
        )

        # Notes: ========== 启动工具 ==========
        tracer: "Tracer" = Tracer()

        trace_loc = os.path.join(
            reporter.group_dir, f"{self.file_folder}_trace.perfetto-trace"
        )

        device_folder = f"/data/local/tmp/{Path(self.ft_file).name}"
        target_folder = f"/data/misc/perfetto-traces/trace_{time.strftime('%Y%m%d%H%M%S')}.perfetto-trace"

        await device.push(self.ft_file, device_folder)
        await device.change_mode(777, device_folder)

        transports = await Terminal.cmd_link(
            ["adb", "shell", "-tt", f"cat {device_folder} | perfetto --txt -c - -o {target_folder}"]
        )

        logger.info(f"开始采样 ...")
        await self.task_close_event.wait()
        transports.terminate()

        await device.pull(target_folder, trace_loc)

        config = TraceProcessorConfig(self.tp_shell)
        with TraceProcessor(trace_loc, config=config) as tp:
            primary_frames = await tracer.extract_primary_frames(tp, package)
            roll_ranges = await tracer.extract_roll_ranges(tp)
            drag_ranges = await tracer.extract_drag_ranges(tp)
            jank_ranges = await tracer.mark_consecutive_jank(primary_frames)

        async with aiosqlite.connect(reporter.db_file) as db:
            await Cubicle.create_gfx_table(db)
            analyzer = Analyzer(
                db, os.path.join(reporter.group_dir, f"Report_{Path(reporter.group_dir).name}")
            )
            segment_ms = 2000
            await analyzer.plot_multiple_segments(
                primary_frames, roll_ranges, drag_ranges, jank_ranges, segment_ms, self.file_folder
            )


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

    async def authorized() -> None:
        """
        检查目录下的所有文件是否具备执行权限，如果文件没有执行权限，则自动添加 +x 权限。
        """
        if platform != "darwin":
            return None

        tools_set = [kit for kit in [adb, perfetto, tp_shell] if Path(kit).exists()]

        ensure = [
            kit for kit in tools_set if not (Path(kit).stat().st_mode & stat.S_IXUSR)
        ]

        if not ensure:
            return None

        for auth in ensure:
            logger.debug(f"Authorizing: {auth}")

        for resp in await asyncio.gather(
            *(Terminal.cmd_line(["chmod", "+x", kit]) for kit in ensure), return_exceptions=True
        ):
            logger.debug(f"Authorize: {resp}")

    # Notes: ========== Start from here ==========
    Design.startup_logo()

    # 解析命令行参数
    parser = Parser()
    cmd_lines = parser.parse_cmd

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

    # Notes: ========== 路径初始化 ==========
    src_templates = os.path.join(mx_work, const.SCHEMATIC, const.TEMPLATES).format()

    turbo = os.path.join(mx_work, const.SCHEMATIC, const.SUPPORTS).format()

    if not os.path.exists(
        initial_source := os.path.join(mx_feasible, const.STRUCTURE).format()
    ):
        os.makedirs(initial_source, exist_ok=True)

    if not os.path.exists(
        src_opera_place := os.path.join(initial_source, const.SRC_OPERA_PLACE).format()
    ):
        os.makedirs(src_opera_place, exist_ok=True)

    if not os.path.exists(
        src_total_place := os.path.join(initial_source, const.SRC_TOTAL_PLACE).format()
    ):
        os.makedirs(src_total_place, exist_ok=True)

    Active.active(watch := "INFO" if cmd_lines.watch else "WARNING")

    align_file = os.path.join(initial_source, const.SRC_OPERA_PLACE, const.ALIGN)
    align = Align(align_file)

    if cmd_lines.align:
        return await previewing()

    # Notes: ========== 授权流程 ==========
    lic_file = Path(src_opera_place) / const.LIC_FILE

    if apply_code := cmd_lines.apply:
        return await authorize.receive_license(apply_code, lic_file)

    await authorize.verify_license(lic_file)

    # Notes: ========== 工具路径设置 ==========
    if platform == "win32":
        supports = os.path.join(turbo, "Windows").format()
        adb, perfetto, tp_shell = "adb.exe", "perfetto.exe", "trace_processor_shell.exe"
    elif platform == "darwin":
        supports = os.path.join(turbo, "MacOS").format()
        adb, perfetto, tp_shell = "adb", "perfetto", "trace_processor_shell"
    else:
        raise MemrixError(f"{const.APP_DESC} is not supported on this platform: {platform}.")

    adb = os.path.join(supports, "platform-tools", adb)
    perfetto = os.path.join(supports, "perfetto-kit", perfetto)
    tp_shell = os.path.join(supports, "perfetto-kit", tp_shell)

    ft_file = os.path.join(supports, "perfetto-kit", "frametime.pbtxt")

    for tls in (tools := [adb, perfetto, tp_shell]):
        os.environ["PATH"] = os.path.dirname(tls) + env_symbol + os.environ.get("PATH", "")

    # Notes: ========== 同步命令 ==========
    # ......

    # Notes: ========== 模板与工具检查 ==========
    memory_template = os.path.join(src_templates, "memory.html")

    # 检查每个模板文件是否存在，如果缺失则显示错误信息并退出程序
    for tmp in (temps := [memory_template]):
        if os.path.isfile(tmp) and os.path.basename(tmp).endswith(".html"):
            continue
        tmp_name = os.path.basename(tmp)
        raise MemrixError(f"{const.APP_DESC} missing files {tmp_name}")

    # 三方应用以及文件授权
    await authorized()

    # 检查每个工具是否存在，如果缺失则显示错误信息并退出程序
    for tls in tools:
        if not shutil.which((tls_name := os.path.basename(tls))):
            raise MemrixError(f"{const.APP_DESC} missing files {tls_name}")

    # Notes: ========== 配置与启动 ==========

    # 远程全局配置
    global_config_task = asyncio.create_task(Api.remote_config())
    # 启动仪式
    await Design.flame_manifest()

    logger.info(f"{'=' * 15} 系统调试 {'=' * 15}")
    logger.info(f"操作系统: {platform}")
    logger.info(f"应用名称: {software}")
    logger.info(f"系统路径: {sys_symbol}")
    logger.info(f"环境变量: {env_symbol}")
    logger.info(f"日志等级: {watch}")
    logger.info(f"工具目录: {turbo}")
    logger.info(f"{'=' * 15} 系统调试 {'=' * 15}\n")

    logger.info(f"{'=' * 15} 环境变量 {'=' * 15}")
    for env in os.environ["PATH"].split(env_symbol):
        logger.info(f"ENV: {env}")
    logger.info(f"{'=' * 15} 环境变量 {'=' * 15}\n")

    logger.info(f"{'=' * 15} 工具路径 {'=' * 15}")
    for tls in tools:
        logger.info(f"TLS: {tls}")
    logger.info(f"{'=' * 15} 工具路径 {'=' * 15}\n")

    logger.info(f"{'=' * 15} 报告模版 {'=' * 15}")
    for tmp in temps:
        logger.info(f"TMP: {tmp}")
    logger.info(f"{'=' * 15} 报告模版 {'=' * 15}\n")

    logger.info(f"{'=' * 15} 初始路径 {'=' * 15}")
    logger.info(f"部署文件路径: {align_file}")
    logger.info(f"{'=' * 15} 初始路径 {'=' * 15}\n")

    await align.load_align()

    positions = (
        cmd_lines.sleek, cmd_lines.storm, cmd_lines.pulse, cmd_lines.forge,
        cmd_lines.focus, cmd_lines.vault, cmd_lines.watch
    )
    keywords = {
        "src_opera_place": src_opera_place,
        "src_total_place": src_total_place,
        "memory_template": memory_template,
        "align": align,
        "adb": adb,
        "perfetto": perfetto,
        "tp_shell": tp_shell,
        "ft_file": ft_file,
    }
    remote = await global_config_task

    memrix = Memrix(remote, *positions, **keywords)

    if cmd_lines.sleek:
        if not cmd_lines.focus:
            raise MemrixError(f"--focus 参数不能为空 ...")

        manage = Manage(adb)
        if not (device := await manage.operate_device(cmd_lines.imply)):
            raise MemrixError(f"没有连接设备 ...")

        signal.signal(signal.SIGINT, memrix.clean_up)

        return await memrix.frame_tracer(device)

    elif cmd_lines.storm or cmd_lines.pulse:
        if not cmd_lines.focus:
            raise MemrixError(f"--focus 参数不能为空 ...")

        manage = Manage(adb)
        if not (device := await manage.operate_device(cmd_lines.imply)):
            raise MemrixError(f"没有连接设备 ...")

        signal.signal(signal.SIGINT, memrix.clean_up)

        main_task = getattr(
            memrix, "dump_task_start" if cmd_lines.storm else "exec_task_start"
        )(device)
        return await main_task

    elif cmd_lines.forge:
        return await memrix.create_mem_report()

    else:
        return None


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
        main_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(main_loop)
        main_loop.run_until_complete(main())
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
