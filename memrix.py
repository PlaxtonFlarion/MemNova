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
import stat
import json
import time
import uuid
import typing
import signal
import shutil
import asyncio
import secrets

# ====[ 第三方库 ]====
import aiosqlite

# ====[ from: 内置模块 ]====
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

# ====[ from: 第三方库 ]====
from loguru import logger

# ====[ from: 本地模块 ]====
from engine.device import Device
from engine.manage import Manage
from engine.terminal import Terminal
from engine.tinker import (
    Active, Period, FileAssist, ToolKit, MemrixError
)
from memcore.api import Api
from memcore import authorize
from memcore.cubicle import Cubicle
from memcore.design import Design
from memcore.parser import Parser
from memcore.profile import Align
from memnova.templater import Templater
from memnova.reporter import Reporter
from memnova.tracer import GfxAnalyzer
from memnova import const


class Memrix(object):
    """Memrix"""

    file_insert: typing.Optional[int] = 0
    file_folder: typing.Optional[str] = ""

    __remote: dict = {}

    def __init__(self, wires: list, level: str, power: int, remote: dict, *args, **kwargs):
        """
        初始化核心控制器，配置运行模式、路径结构、分析状态与动画资源。
        """
        self.wires = wires  # 命令参数
        self.level = level  # 日志级别
        self.power = power  # 最大进程

        self.remote: dict = remote or {}  # workflow: 远程全局配置

        self.storm, self.sleek, self.forge, *_ = args
        _, _, _, self.focus, self.nodes, self.title, self.layer, *_ = args

        self.src_opera_place: str = kwargs["src_opera_place"]
        self.src_total_place: str = kwargs["src_total_place"]
        self.unity_template: str = kwargs["unity_template"]

        self.align: "Align" = kwargs["align"]

        self.adb: str = kwargs["adb"]
        self.perfetto: str = kwargs["perfetto"]
        self.tp_shell: str = kwargs["tp_shell"]
        self.trace_conv: str = kwargs["trace_conv"]

        self.ft_file: str = kwargs["ft_file"]

        self.padding: str = "=" * 10
        self.memories: dict[str, typing.Any] = {}

        self.design: "Design" = Design(self.level)

        self.animation_task: typing.Optional["asyncio.Task"] = None

        self.task_close_event: typing.Optional["asyncio.Event"] = asyncio.Event()
        self.dumped: typing.Optional["asyncio.Event"] = None

        self.data_queue: "asyncio.Queue" = asyncio.Queue()

    @property
    def remote(self) -> dict:
        return self.__remote

    @remote.setter
    def remote(self, value: dict) -> None:
        self.__remote = value if isinstance(value, dict) else {}

    def task_clean_up(self, *_, **__) -> None:
        self.memories.update({
            "MSG": (msg := "Finishing up ...")
        })
        logger.info(msg)
        self.task_close_event.set()

    async def watcher(self) -> None:
        logger.info(f"Token: {(token := f'{const.APP_DESC}.{secrets.token_hex(8)}')}")

        async def handler(reader: "asyncio.StreamReader", writer: "asyncio.StreamWriter") -> None:
            if (await reader.read(100)).decode().strip() == token:
                self.task_close_event.set()
            writer.close()
            await writer.wait_closed()

        server = await asyncio.start_server(handler, host="127.0.0.1", port=8765)
        async with server:
            await self.task_close_event.wait()
            server.close()
            await server.wait_closed()

    async def refresh(
        self,
        device: "Device",
        reporter: "Reporter",
        package: str,
        team_name: str,
        prefix: str,
    ) -> "Path":

        self.file_insert = 0
        self.file_folder = team_name

        format_before_time = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(reporter.before_time)
        )
        sample_speed = self.align.mem_speed if self.storm else self.align.gfx_speed

        logger.info(f"时间 -> {format_before_time}")
        logger.info(f"应用 -> {package}")
        logger.info(f"频率 -> {sample_speed}")
        logger.info(f"标签 -> {self.align.app_label}")
        logger.info(f"文件 -> {self.file_folder}\n")

        await self.design.summaries(
            format_before_time, package, sample_speed, self.align.app_label, self.file_folder
        )

        if Path(reporter.team_file).is_file():
            scene = await FileAssist.read_yaml(reporter.team_file)
            scene["file"].append(self.file_folder)
        else:
            scene = {
                "time": format_before_time,
                "mark": device.device_info | {"serial": device.serial},
                "type": prefix,
                "file": [self.file_folder]
            }
        await FileAssist.dump_yaml(reporter.team_file, scene)

        if not (traces := Path(reporter.group_dir) / const.TRACES_DIR / self.file_folder).exists():
            traces.mkdir(parents=True, exist_ok=True)

        return traces

    async def sample_stop(self, reporter: "Reporter", *args, **__) -> None:
        if self.dumped and not self.dumped.is_set():
            logger.info(f"Awaiting final sync ...")
            try:
                await asyncio.wait_for(self.dumped.wait(), timeout=3)
            except asyncio.TimeoutError:
                pass

        for task in args:
            if isinstance(task, asyncio.Task):
                try:
                    task.cancel()
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled: {task.get_name()}")

        await self.data_queue.join()

        msg = f"{self.file_insert} records. Zero point."
        self.memories.update(
            {"MSG": msg, "MOD": "*", "ACT": "*", "PSS": "*", "FOREGROUND": "*", "BACKGROUND": "*"}
            if self.storm else
            {"MSG": msg, "ANA": "*", "ERR": "*"}
        )

        if self.animation_task:
            try:
                await asyncio.wait_for(self.animation_task, timeout=3)
                logger.info(f"Cancelled: {self.animation_task.get_name()}")
            except asyncio.TimeoutError:
                pass

        time_cost = (time.time() - reporter.before_time) / 60
        logger.info(
            f"Mark={self.align.app_label} File={self.file_folder} Data={self.file_insert} Time={time_cost:.2f} m"
        )
        logger.info(f"{reporter.group_dir}")

        if self.file_insert:
            fc = Design.build_file_tree(reporter.group_dir)
            Design.console.print()
            Design.Doc.log(
                f"Usage: [bold #00D787]{const.APP_NAME} --forge [{fc}]{Path(reporter.group_dir).name}[/]"
            )

        logger.info(
            f"^*{self.padding} {const.APP_DESC} Engine Close {self.padding}*^"
        )

        Design.console.print()
        await self.design.system_disintegrate()

    async def gfx_alignment(
        self,
        track_enabled: bool,
        db: "aiosqlite.Connection",
        now_time: str
    ) -> None:

        if not track_enabled:
            return None

        while True:
            data = await self.data_queue.get()
            trace_file = data.get("trace_file")
            try:
                self.memories.update({
                    "MSG": f"[bold #87FFD7]Queue received {Path(trace_file).name}",
                    "ANA": f"[bold #00FF5F]Sample analyzing ...",
                })
                logger.info(f"Queue received {Path(trace_file).name}")

                gfx_analyzer = GfxAnalyzer()
                gfx_fmt_data = await asyncio.shield(asyncio.to_thread(
                    gfx_analyzer.extract_metrics, trace_file, self.tp_shell, self.focus
                ))

                await Cubicle.insert_gfx_data(
                    db, self.file_folder, self.align.app_label, Period.convert_time(now_time), gfx_fmt_data
                )

                self.file_insert += 1
                self.memories.update({
                    "MSG": f"[bold #00FF5F]Article {self.file_insert} data insert success",
                    "ANA": f"[bold #AFFF5F]Analyze engine ready",
                })
                logger.info(f"Article {self.file_insert} data insert success")

            except Exception as e:
                self.memories.update({
                    "MSG": "*",
                    "ANA": "*",
                    "ERR": f"[bold #FF5F5F]{e}",
                })
            finally:
                self.data_queue.task_done()

    async def track_collector(
        self,
        track_enabled: bool,
        device: "Device",
        db: "aiosqlite.Connection"
    ) -> None:

        async def mem_analyze() -> dict:
            meminfo_map, summary_map = {}, {}

            if not (mem_info := await device.mem_info(self.focus)):
                return {}

            if not re.search(r"====MEM====.*?====EOF====", mem_info, re.S):
                return {}

            if app_meminfo := re.search(r"\*\* MEMINFO.*?(?=App Summary)", mem_info, re.S):
                logger.info(f"Current APP MEMINFO\n{(meminfo_c := app_meminfo.group())}")
                for i in [
                    "Native Heap", "Dalvik Heap", "Dalvik Other", "Stack", "Ashmem", "Other dev",
                    ".so mmap", ".jar mmap", ".apk mmap", ".ttf mmap", ".dex mmap", ".oat mmap", ".art mmap",
                    "Other mmap", "GL mtrack", "Unknown"
                ]:
                    meminfo_map[i] = ToolKit.fit_mem(i, meminfo_c)
                meminfo_map["TOTAL USS"] = ToolKit.uss_addition(meminfo_c)

            if app_summary := re.search(r"App Summary.*?(?=Objects)", mem_info, re.S):
                logger.info(f"Current APP SUMMARY\n{(summary_c := app_summary.group())}")
                for i in [
                    "Java Heap", "Native Heap", "Graphics", "TOTAL PSS", "TOTAL RSS", "TOTAL SWAP"
                ]:
                    summary_map[i] = ToolKit.fit_mem(i, summary_c)

            return {"meminfo": meminfo_map} | {"summary": summary_map}

        async def io_analyze(pid: str) -> dict:
            io_map = {}

            if not (io_info := await device.io_info(pid)):
                return io_map

            if app_io := re.search(r"====I/O====.*?====EOF====", io_info, re.S):
                logger.info(f"Current APP IO\n{(app_io_c := app_io.group())}")
                for i in ["rchar", "wchar", "read_bytes", "write_bytes", "cancelled_write_bytes"]:
                    io_map[i] = ToolKit.fit_io(i, app_io_c)
                for j in ["syscr", "syscw"]:
                    io_map[j] = ToolKit.fit_io_count(j, app_io_c)

            return {"io": io_map}

        async def union_analyze(pid: str) -> dict:
            mem_map, io_map = await asyncio.gather(*(mem_analyze(), io_analyze(pid)))
            return mem_map | io_map if all((mem_map, io_map)) else {}

        async def track_launcher() -> None:
            self.dumped.clear()

            dump_start_time = time.time()

            if not (app_pid := await device.pid_value(self.focus)):
                self.dumped.set()
                self.memories.update({
                    "MSG": f"[bold #FF5F5F]Process -> {app_pid}",
                    "MOD": "*",
                    "ACT": "*",
                    "PSS": "*",
                })
                return logger.info(f"Process -> {app_pid}\n")

            logger.info(device)
            self.memories.update({
                "MSG": f"[bold #87D700]Process -> {app_pid.member}"
            })
            logger.info(f"Process -> {app_pid.member}")

            try:
                main_pid = list(app_pid.member.keys())[0]
            except (KeyError, IndexError) as e:
                self.dumped.set()
                self.memories.update({
                    "MSG": f"[bold #FF5F5F]Pid -> {e}",
                    "MOD": "*",
                    "ACT": "*",
                    "PSS": "*",
                })
                return logger.info(f"Pid -> {e}\n")

            activity, adj = await asyncio.gather(device.activity(), device.adj(main_pid))

            mark_map = {
                "mark": {"tms": time.strftime("%Y-%m-%d %H:%M:%S"), "act": activity}
            }

            if self.focus in activity:
                mode = "FG"
            else:
                mode = "FG" if adj is not None and int(adj) <= 0 else "BG"

            mark_map["mark"]["mode"], mark_map["mark"]["adj"] = mode, adj

            state = "FOREGROUND" if mark_map["mark"]["mode"] == "FG" else "BACKGROUND"
            color = "#00B5D8" if state.startswith("F") else "#F29E4C"
            self.memories.update({
                "MOD": f"[bold {color}]{state}",
                "ACT": activity
            })

            logger.info(f"TMS: {mark_map['mark']['tms']}")
            logger.info(f"ADJ: {mark_map['mark']['adj']}")
            logger.info(f"{mark_map['mark']['act']}")
            logger.info(f"{mark_map['mark']['mode']}")

            mark_map["mark"]["pid"] = json.dumps(app_pid.member)

            if all(result := await asyncio.gather(*(union_analyze(pid) for pid in list(app_pid.member.keys())))):
                muster = defaultdict(lambda: defaultdict(float))
                for r in result:
                    for key, value in r.items():
                        for k, v in value.items():
                            muster[key][k] += v
                muster = {k: dict(v) for k, v in muster.items()}

            else:
                self.dumped.set()
                self.memories.update({
                    "MSG": f"[bold #FF5F5F]Resp -> {result}",
                    "MOD": "*",
                    "ACT": "*",
                    "PSS": "*",
                })
                return logger.info(f"Resp -> {result}\n")

            try:
                logger.info(muster)
            except KeyError:
                return self.dumped.set()

            if final_map := mark_map | muster:
                await Cubicle.insert_mem_data(
                    db, self.file_folder, self.align.app_label, final_map
                )
                self.file_insert += 1
                msg = f"Article {self.file_insert} data insert success"

                self.memories[state] += 1
                self.memories.update({
                    "MSG": f"[bold #87D700]{msg}",
                    "PSS": f"{final_map.get('summary', {}).get('TOTAL PSS', 0):.2f} MB"
                })

            else:
                msg = f"Data insert skipped"
                self.memories.update({
                    "MSG": f"[bold #FF5F5F]{msg}",
                    "MOD": "*",
                    "ACT": "*",
                    "PSS": "*"
                })

            logger.info(msg)

            self.dumped.set()
            return logger.info(f"{time.time() - dump_start_time:.2f} s\n")

        if not track_enabled:
            return None

        self.dumped = asyncio.Event()
        while not self.task_close_event.is_set():
            await track_launcher()
            await asyncio.sleep(self.align.mem_speed)

    # """星痕律动 / 星落浮影 / 帧影流光 / 引力回廊"""
    async def track_core_task(self, device: "Device") -> None:

        # Workflow: ========== 检查配置 ==========
        if not (check := await device.examine_pkg(self.focus)):
            raise MemrixError(f"应用名称不存在 {self.focus} -> {check}")

        reporter = Reporter(
            self.src_total_place, self.nodes, prefix := "Storm" if self.storm else "Sleek", self.align
        )

        logger.info(
            f"^*{self.padding} {const.APP_DESC} Engine Start {self.padding}*^"
        )

        team_name = f"{prefix}_Data_{(now_time := time.strftime('%Y%m%d%H%M%S'))}"
        traces = await self.refresh(device, reporter, self.focus, team_name, prefix)

        if self.title:
            safe = re.sub(r'[\\/:"*?<>|]+', '', self.title)
            head = f"{safe[:11]}_{now_time}"
        else:
            head = self.file_folder

        trace_loc = traces / f"{head}_trace.perfetto-trace"

        perfetto = Perfetto(
            self.sleek, self.task_close_event, self.data_queue, self.align.gfx_speed,
            device, self.ft_file, traces, trace_loc, self.trace_conv
        )

        # Workflow: ========== 显示面板 ==========
        self.memories = {
            "MSG": "*", "MOD": "*", "ACT": "*", "PSS": "*", "FOREGROUND": 0, "BACKGROUND": 0
        } if self.storm else {
            "MSG": "*", "ANA": "*", "ERR": "*"
        }

        # Workflow: ========== 开始采样 ==========
        async with aiosqlite.connect(reporter.db_file) as db:
            await Cubicle.initialize_tables(
                db, self.file_folder, self.title, Period.convert_time(now_time), device.device_info | {"serial": device.serial}
            )
            self.animation_task = asyncio.create_task(
                self.design.mem_wave(self.memories, self.task_close_event)
                if self.storm else
                self.design.gfx_wave(self.memories, self.task_close_event),
                name="animation task"
            )

            gfx_task = asyncio.create_task(
                self.gfx_alignment(self.sleek, db, now_time), name="gfx alignment task"
            )
            pft_task = asyncio.create_task(perfetto.auto_pilot(), name="auto pilot task")

            watcher = asyncio.create_task(self.watcher())
            await self.track_collector(self.storm, device, db)

            await self.task_close_event.wait()

            # Workflow: ========== 结束采样 ==========
            await asyncio.gather(
                watcher, self.sample_stop(reporter, pft_task, gfx_task)
            )

    # """真相快照"""
    async def observation(self) -> None:

        original = Path(self.src_total_place) / const.TOTAL_DIR / const.TREE_DIR
        if not (target_dir := original / self.forge).exists():
            raise MemrixError(f"Target directory {target_dir.name} does not exist ...")

        segment_router = {
            "Storm": "mem_rendition", "Sleek": "gfx_rendition"
        }

        if len(parts := target_dir.name.split("_")) != 2:
            raise MemrixError(f"Unexpected directory name format: {target_dir.name}")
        src, dst = parts

        try:
            render = segment_router[dst]
        except KeyError:
            raise MemrixError(f"Unsupported directory type: {src} ...")

        reporter = Reporter(self.src_total_place, src, dst, self.align)

        for file in [reporter.db_file, reporter.log_file, reporter.team_file]:
            if not Path(file).is_file():
                raise MemrixError(f"Missing valid data file: {file}")

        try:
            team_data = await FileAssist.read_yaml(reporter.team_file)
        except Exception as e:
            raise MemrixError(e)

        if not (data_list := team_data.get("file")):
            raise MemrixError(f"No data scenario: {data_list} ...")

        self.memories = {
            "MSG": "*", "MAX": (total := len(data_list)), "CUR": 0, "TMS": "0.0 s",
        }
        self.animation_task = asyncio.create_task(
            self.design.lab_detonation(self.memories, self.task_close_event), name="animation task"
        )

        start_time, loop, templater = time.time(), asyncio.get_running_loop(), Templater(
            os.path.join(reporter.group_dir, f"Report_{Path(reporter.group_dir).name}")
        )

        async with aiosqlite.connect(reporter.db_file) as db:
            with ProcessPoolExecutor(initializer=Active.active, initargs=(const.SHOW_LEVEL,)) as executor:
                self.memories.update({"MSG": f"Rendering {total} tasks"})
                if not (rendition := await getattr(reporter, render)(
                    db, loop, executor, templater, self.memories, start_time, team_data, self.layer
                )):
                    self.task_close_event.set()
                    await self.animation_task
                    raise MemrixError(f"Rendering tasks failed")

        self.memories.update({"MSG": f"Polymerization"})
        html_file = await reporter.make_report(self.unity_template, templater.download, **rendition)
        self.memories.update({
            "MSG": f"Done", "TMS": f"{time.time() - start_time:.1f} s"
        })
        self.task_close_event.set()
        await self.animation_task

        Design.console.print()
        Design.build_file_tree(html_file)
        Design.console.print()

        return await self.design.system_disintegrate()


class Perfetto(object):
    """Perfetto"""

    def __init__(
        self,
        track_enabled: bool,
        track_event: "asyncio.Event",
        data_queue: "asyncio.Queue",
        gfx_speed: float,
        device: "Device",
        ft_file: str,
        traces_dir: "Path",
        trace_loc: "Path",
        trace_conv: str
    ) -> None:

        self.track_enabled = track_enabled
        self.track_event = track_event
        self.data_queue = data_queue
        self.gfx_speed = gfx_speed
        self.device = device
        self.ft_file = ft_file
        self.traces_dir = traces_dir
        self.trace_loc = trace_loc
        self.trace_conv = trace_conv

        self.backs: list["asyncio.Task"] = []

    @staticmethod
    async def input_stream(transports: "asyncio.subprocess.Process") -> None:
        async for line in transports.stdout:
            logger.info(line.decode(const.CHARSET).strip())

    @staticmethod
    async def error_stream(transports: "asyncio.subprocess.Process") -> None:
        async for line in transports.stderr:
            logger.info(line.decode(const.CHARSET).strip())

    async def start(self) -> typing.Optional[str]:
        unique_id = time.strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:6]
        device_folder = f"/data/misc/perfetto-configs/{Path(self.ft_file).name}"
        target_folder = f"/data/misc/perfetto-traces/trace_{unique_id}.perfetto-trace"

        await self.device.push(self.ft_file, device_folder)
        await self.device.change_mode(777, device_folder)

        transports = await self.device.perfetto_start(
            device_folder, target_folder
        )
        _ = asyncio.create_task(self.input_stream(transports))
        _ = asyncio.create_task(self.error_stream(transports))

        return target_folder

    async def close(self, target_folder: str) -> None:
        trace_file = self.traces_dir / f"{Path(target_folder).stem}.perfetto-trace"

        await self.device.pull(target_folder, str(trace_file))
        await self.device.remove(target_folder)
        await self.data_queue.put({"trace_file": str(trace_file)})

    async def replenish(self, target_folder: str) -> None:
        if not self.track_enabled:
            return None

        await self.device.perfetto_close()
        await self.close(target_folder)

    async def auto_pilot(self) -> typing.Any:
        if not self.track_enabled:
            return None

        await self.device.remove("/data/misc/perfetto-traces/*.perfetto-trace")

        target_folder = None
        while not self.track_event.is_set():
            target_folder = await self.start()
            await asyncio.sleep(self.gfx_speed)
            await self.device.perfetto_close()
            self.backs.append(asyncio.create_task(self.close(target_folder)))

        await asyncio.gather(*self.backs)
        return await self.replenish(target_folder) if target_folder else None


# """Main"""
async def main() -> typing.Any:
    """
    主控制入口，用于解析命令行参数并根据不同模式执行配置展示、内存转储、脚本执行或报告生成等功能。
    """

    async def previewing() -> None:
        """
        预览对齐配置文件，若不存在则自动生成。
        """
        if not Path(align_file).exists():
            await align.dump_align()

        Design.console.print()
        Design.build_file_tree(align_file)
        await FileAssist.open(align_file)
        await align.load_align()

        return Design.console.print()

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

    async def arithmetic(function: typing.Callable) -> None:
        """
        执行通用异步任务函数。
        """
        if not cmd_lines.focus:
            raise MemrixError(f"--focus 参数不能为空 ...")

        manage = Manage(adb)
        if not (device := await manage.operate_device(cmd_lines.imply)):
            raise MemrixError(f"没有连接设备 ...")

        signal.signal(signal.SIGINT, memrix.task_clean_up)

        return await function(device)

    # Notes: ========== Start from here ==========
    Design.startup_logo()

    # 解析命令行参数
    parser = Parser()
    cmd_lines = parser.parse_cmd

    # 如果没有提供命令行参数，则显示帮助文档，并退出程序
    if len(system_parameter_list := sys.argv) == 1:
        return parser.parse_engine.print_help()

    # 获取命令行参数（去掉第一个参数，即脚本名称）
    wires = system_parameter_list[1:]

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

    Active.active(level := "INFO" if cmd_lines.watch else "WARNING")

    align_file = os.path.join(initial_source, const.SRC_OPERA_PLACE, const.ALIGN)
    align = Align(align_file)

    if cmd_lines.align:
        return await previewing()

    # Notes: ========== 授权流程 ==========
    lic_file = Path(src_opera_place) / const.LIC_FILE

    if apply_code := cmd_lines.apply:
        return await authorize.receive_license(apply_code, lic_file)

    # await authorize.verify_license(lic_file)

    # Notes: ========== 工具路径设置 ==========
    if platform == "win32":
        supports = os.path.join(turbo, "Windows").format()
        adb, perfetto, tp_shell = "adb.exe", "perfetto.exe", "trace_processor_shell.exe"
        trace_conv = "traceconv.exe"
    elif platform == "darwin":
        supports = os.path.join(turbo, "MacOS").format()
        adb, perfetto, tp_shell = "adb", "perfetto", "trace_processor_shell"
        trace_conv = "traceconv"
    else:
        raise MemrixError(f"{const.APP_DESC} is not supported on this platform: {platform}.")

    adb = os.path.join(supports, "platform-tools", adb)
    perfetto = os.path.join(supports, "perfetto-kit", perfetto)
    tp_shell = os.path.join(supports, "perfetto-kit", tp_shell)
    trace_conv = os.path.join(supports, "perfetto-kit", trace_conv)

    ft_file = os.path.join(supports, "perfetto-kit", "frametime.pbtxt")

    for tls in (tools := [adb, perfetto, tp_shell, trace_conv]):
        os.environ["PATH"] = os.path.dirname(tls) + env_symbol + os.environ.get("PATH", "")

    # Notes: ========== 模板与工具检查 ==========
    unity_template = os.path.join(src_templates, "unity_template.html")

    # 检查每个模板文件是否存在，如果缺失则显示错误信息并退出程序
    for tmp in (temps := [unity_template]):
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
    # await Design.flame_manifest()

    logger.info(f"{'=' * 15} 系统调试 {'=' * 15}")
    logger.info(f"操作系统: {platform}")
    logger.info(f"核心数量: {(power := os.cpu_count())}")
    logger.info(f"应用名称: {software}")
    logger.info(f"系统路径: {sys_symbol}")
    logger.info(f"环境变量: {env_symbol}")
    logger.info(f"日志等级: {level}")
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
        cmd_lines.storm, cmd_lines.sleek, cmd_lines.forge,
        cmd_lines.focus, cmd_lines.nodes, cmd_lines.title, cmd_lines.layer,
    )
    keywords = {
        "src_opera_place": src_opera_place,
        "src_total_place": src_total_place,
        "unity_template": unity_template,
        "align": align,
        "adb": adb,
        "perfetto": perfetto,
        "tp_shell": tp_shell,
        "trace_conv": trace_conv,
        "ft_file": ft_file,
    }
    remote = await global_config_task

    memrix = Memrix(wires, level, power, remote, *positions, **keywords)

    if cmd_lines.storm or cmd_lines.sleek:
        return await arithmetic(memrix.track_core_task)

    elif cmd_lines.forge:
        return await memrix.observation()

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
