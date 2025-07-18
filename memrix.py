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

# ====[ from: 第三方库 ]====
from loguru import logger
from perfetto.trace_processor import (
    TraceProcessor, TraceProcessorConfig
)

# ====[ from: 本地模块 ]====
from engine.device import Device
from engine.manage import Manage
from engine.terminal import Terminal
from engine.tinker import (
    Active, Period, Ram, FileAssist, ToolKit, MemrixError
)
from memcore.api import Api
from memcore import authorize
from memcore.cubicle import Cubicle
from memcore.design import Design
from memcore.parser import Parser
from memcore.profile import Align
from memnova.templater import Templater
from memnova.reporter import Reporter
from memnova.tracer import GfxAnalyzer, IoAnalyzer
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
        _, _, _, self.focus, self.vault, self.title, self.hprof, *_ = args

        self.src_opera_place: str = kwargs["src_opera_place"]
        self.src_total_place: str = kwargs["src_total_place"]
        self.unity_template: str = kwargs["unity_template"]

        self.align: "Align" = kwargs["align"]

        self.adb: str = kwargs["adb"]
        self.perfetto: str = kwargs["perfetto"]
        self.tp_shell: str = kwargs["tp_shell"]

        self.ft_file: str = kwargs["ft_file"]

        self.padding: str = "-" * 8
        self.memories: dict[str, typing.Union[str, int]] = {
            "msg": "*",
            "mod": "*",
            "act": "*",
            "pss": "*",
            "foreground": 0,
            "background": 0
        }
        self.design: "Design" = Design(self.level)

        self.animation_task: typing.Optional["asyncio.Task"] = None

        self.task_close_event: typing.Optional["asyncio.Event"] = asyncio.Event()
        self.dumped: typing.Optional["asyncio.Event"] = None

    @property
    def remote(self) -> dict:
        return self.__remote

    @remote.setter
    def remote(self, value: dict) -> None:
        self.__remote = value

    def task_clean_up(self, *_, **__) -> None:
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
            team_name: str
    ) -> "Path":

        self.file_insert = 0
        self.file_folder = team_name

        format_before_time = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(reporter.before_time)
        )

        logger.info(f"时间 -> {format_before_time}")
        logger.info(f"应用 -> {package}")
        logger.info(f"频率 -> {self.align.speed}")
        logger.info(f"标签 -> {self.align.label}")
        logger.info(f"文件 -> {self.file_folder}\n")

        await self.design.summaries(
            format_before_time, package, self.align.speed, self.align.label, self.file_folder
        )

        if Path(reporter.team_file).is_file():
            scene = await FileAssist.read_yaml(reporter.team_file)
            scene["file"].append(self.file_folder)
        else:
            scene = {
                "time": format_before_time,
                "mark": device.serial,
                "file": [self.file_folder]
            }
        await FileAssist.dump_yaml(reporter.team_file, scene)

        if not (traces := Path(reporter.group_dir) / const.TRACES_DIR).exists():
            traces.mkdir(parents=True, exist_ok=True)

        return traces

    async def sample_stop(self, reporter: "Reporter") -> None:
        if self.dumped and not self.dumped.is_set():
            logger.info(f"等待采样任务结束 ...")
            try:
                await asyncio.wait_for(self.dumped.wait(), timeout=3)
            except asyncio.TimeoutError:
                logger.info("采样任务超时结束 ...")

        if self.animation_task:
            try:
                await asyncio.wait_for(self.animation_task, timeout=3)
            except asyncio.TimeoutError:
                pass

        time_cost = (time.time() - reporter.before_time) / 60
        logger.info(
            f"Mark={self.align.label} File={self.file_folder} Data={self.file_insert} Time={time_cost:.2f} m"
        )
        logger.info(f"{reporter.group_dir}")

        if self.file_insert:
            fc = Design.build_file_tree(reporter.group_dir)
            Design.Doc.log(
                f"Usage: [#00D787]{const.APP_NAME} --forge --focus [{fc}]{Path(reporter.group_dir).name}[/]"
            )

        logger.info(
            f"^*{self.padding} {const.APP_DESC} Engine Close {self.padding}*^"
        )

        Design.console.print()
        await self.design.system_disintegrate()

    async def sample_analyze(
            self,
            track_gfx: bool,
            db: "aiosqlite.Connection",
            trace_loc: typing.Union["Path", str],
            now_time: str,
    ) -> None:

        gfx_fmt_data, io_fmt_data, now_time = {}, {}, Period.convert_time(now_time)

        with TraceProcessor(str(trace_loc), config=TraceProcessorConfig(self.tp_shell)) as tp:
            if track_gfx:
                gfx_analyzer = GfxAnalyzer()
                gfx_data = await gfx_analyzer.extract_metrics(tp, self.focus)
                gfx_fmt_data = {k: json.dumps(v) for k, v in gfx_data.items()}
                await Cubicle.insert_gfx_data(
                    db, self.file_folder, self.align.label, now_time, gfx_fmt_data
                )

            io_analyzer = IoAnalyzer()
            io_data = await io_analyzer.extract_metrics(tp, self.focus)
            io_fmt_data = {k: json.dumps(v) for k, v in io_data.items()}
            await Cubicle.insert_io_data(
                db, self.file_folder, self.align.label, now_time, io_fmt_data
            )

        self.file_insert += (len(gfx_fmt_data) + len(io_fmt_data))
        logger.info(f"Article {self.file_insert} data insert success")

    async def memory_collector(
            self,
            track_mem: bool,
            device: "Device",
            db: "aiosqlite.Connection",
    ) -> None:

        async def flash_memory(pid: str) -> typing.Optional[dict[str, dict]]:
            if not (memory := await device.memory_info(self.focus)):
                return None

            logger.info(f"Dump -> [{pid}] - [{self.focus}]")
            resume_map, memory_map, memory_vms = {}, {}, {}

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
            self.dumped.clear()

            dump_start_time = time.time()

            if not (app_pid := await device.pid_value(self.focus)):
                self.dumped.set()
                self.memories.update({
                    "msg": (msg := f"Process -> {app_pid}"),
                    "mod": "*",
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
                    "mod": "*",
                    "act": "*",
                    "pss": "*"
                })
                return logger.info(f"{msg}\n")

            adj, act = current_info_list

            uid = uid if (uid := await device.uid_value(self.focus)) else 0

            remark_map = {"tms": time.strftime("%Y-%m-%d %H:%M:%S")}

            remark_map.update({
                "uid": uid, "adj": adj, "act": act
            })
            remark_map.update({
                "mode": "FG" if self.focus in act else "FG" if int(adj) <= 0 else "BG"
            })

            state = "foreground" if remark_map["mode"] == "FG" else "background"
            self.memories.update({
                "mod": state,
                "act": act
            })

            logger.info(f"{remark_map['tms']}")
            logger.info(f"UID: {remark_map['uid']}")
            logger.info(f"ADJ: {remark_map['adj']}")
            logger.info(f"{remark_map['act']}")
            logger.info(f"{remark_map['mode']}")

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
                    "mod": "*",
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
                await Cubicle.insert_mem_data(
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
                    "mod": "*",
                    "act": "*",
                    "pss": "*"
                })

            self.memories.update({
                "msg": msg
            })
            logger.info(msg)

            self.dumped.set()
            return logger.info(f"{time.time() - dump_start_time:.2f} s\n")

        if not track_mem:
            return None

        toolkit: "ToolKit" = ToolKit()

        self.dumped = asyncio.Event()
        while not self.task_close_event.is_set():
            await flash_memory_launch()
            await asyncio.sleep(self.align.speed)

    # """星痕律动 / 星落浮影 / 帧影流光 / 引力回廊"""
    async def track_core_task(self, device: "Device") -> None:

        # Workflow: ========== 检查配置 ==========
        if not (check := await device.examine_pkg(self.focus)):
            raise MemrixError(f"应用名称不存在 {self.focus} -> {check}")

        reporter = Reporter(
            self.src_total_place, self.vault, prefix := "Storm" if self.storm else "Sleek", self.align
        )

        logger.info(
            f"^*{self.padding} {const.APP_DESC} Engine Start {self.padding}*^"
        )

        team_name = f"{Storm}_Data_{(now_time := time.strftime('%Y%m%d%H%M%S'))}"
        traces = await self.refresh(device, reporter, self.focus, team_name)

        head = f"{self.title}_{now_time}" if self.title else self.file_folder
        trace_loc = traces / f"{head}_trace.perfetto-trace"

        perfetto = Perfetto(self.sleek, device, self.ft_file, str(trace_loc))

        # Workflow: ========== 开始采样 ==========
        async with aiosqlite.connect(reporter.db_file) as db:
            await Cubicle.initialize_tables(
                db, self.file_folder, self.title, Period.convert_time(now_time)
            )
            self.animation_task = asyncio.create_task(
                self.design.memory_wave(self.memories, animation_event := asyncio.Event())
            )
            await perfetto.start()

            watcher = asyncio.create_task(self.watcher())
            await self.memory_collector(self.storm, device, db)

            await self.task_close_event.wait()

            await perfetto.close()
            await self.sample_analyze(db, trace_loc, now_time)

            animation_event.set()

        await asyncio.gather(watcher, self.sample_stop(reporter))

    # """真相快照"""
    async def observation(self) -> None:
        original = Path(self.src_total_place) / const.TOTAL_DIR / const.TREE_DIR
        if not (target_dir := original / self.focus).exists():
            raise MemrixError(f"Target directory {target_dir.name} does not exist ...")

        reporter = Reporter(self.src_total_place, self.focus, self.align)
        for file in [reporter.db_file, reporter.log_file, reporter.team_file]:
            if not Path(file).is_file():
                raise MemrixError(f"Missing valid data file: {file}")

        team_data = await FileAssist.read_yaml(reporter.team_file)

        segment_router = {
            "mem": "lapse_rendition" if self.hprof else "mem_rendition",
            "gfx": "gfx_rendition",
        }

        if not (classify_type := team_data.get("type")):
            raise MemrixError(f"No data classify type: {classify_type} ...")

        renderers = []
        for i in classify_type.strip().split(","):
            try:
                renderers.append(segment_router[i])
            except KeyError:
                raise MemrixError(f"Unexpected name format: {i} ...")

        async with aiosqlite.connect(reporter.db_file) as db:
            templater = Templater(
                os.path.join(reporter.group_dir, f"Report_{Path(reporter.group_dir).name}")
            )

            if not (data_list := team_data.get("file")):
                raise MemrixError(f"No data scenario: {data_list} ...")

            for rendition in await asyncio.gather(
                *(getattr(reporter, render)(db, templater, data_list, team_data) for render in renderers)
            ):
                await reporter.make_report(
                    self.unity_template, templater.download, **rendition
                )
            await asyncio.gather(*reporter.background_tasks)


class Perfetto(object):
    """Perfetto"""

    __transports: typing.Optional["asyncio.subprocess.Process"] = None

    def __init__(
            self,
            device: "Device",
            ft_file: typing.Union["Path", str],
            trace_loc: typing.Union["Path", str]
    ) -> None:

        self.__device = device
        self.__ft_file = str(ft_file)
        self.__trace_loc = str(trace_loc)

        self.__device_folder: typing.Optional[str] = None
        self.__target_folder: typing.Optional[str] = None

    async def __input_stream(self) -> None:
        async for line in self.__transports.stdout:
            logger.info(line.decode(const.CHARSET).strip())

    async def __error_stream(self) -> None:
        async for line in self.__transports.stderr:
            logger.info(line.decode(const.CHARSET).strip())

    async def start(self) -> None:
        unique_id = uuid.uuid4().hex[:8]
        self.__device_folder = f"/data/misc/perfetto-configs/{Path(self.__ft_file).name}"
        self.__target_folder = f"/data/misc/perfetto-traces/trace_{unique_id}.perfetto-trace"

        await self.__device.push(self.__ft_file, self.__device_folder)
        await self.__device.change_mode(777, self.__device_folder)

        self.__transports = await self.__device.perfetto_start(
            self.__device_folder, self.__target_folder
        )
        _ = asyncio.create_task(self.__input_stream())
        _ = asyncio.create_task(self.__error_stream())

    async def close(self) -> None:
        await self.__device.perfetto_close()
        await self.__device.pull(self.__target_folder, self.__trace_loc)
        await self.__device.remove(self.__target_folder)
        self.__transports = None


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
    await Design.flame_manifest()

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
        cmd_lines.focus, cmd_lines.vault, cmd_lines.title, cmd_lines.hprof,
    )
    keywords = {
        "src_opera_place": src_opera_place,
        "src_total_place": src_total_place,
        "unity_template": unity_template,
        "align": align,
        "adb": adb,
        "perfetto": perfetto,
        "tp_shell": tp_shell,
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
