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
import time
import json
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
from memnova.painter import Painter
from memnova.templater import Templater
from memnova.reporter import Reporter
from memnova.tracer import Tracer
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

        self.track, self.lapse, self.sleek, self.surge, self.forge, *_ = args
        _, _, _, _, _, self.focus, self.vault, self.title, self.hprof, *_ = args

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
            "stt": "*",
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

    async def profile(self, device: "Device", heaped: str) -> None:
        max_file = 0
        while self.task_close_event.is_set() or max_file >= 10:
            target = f"/data/local/temp/Hprof_{time.strftime('%Y%m%d%H%M%S')}.hprof"
            await device.dump_heap(self.focus, target)
            await device.pull(target, heaped)
            await device.remove(target)
            max_file += 1
            await asyncio.sleep(180)

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

    # """星痕律动 / 星落浮影"""
    async def mem_dump_task(self, device: "Device") -> None:

        async def flash_memory(pid: str) -> typing.Optional[dict[str, dict]]:
            if not (memory := await device.memory_info(self.focus)):
                return None

            logger.info(f"Dump -> [{pid}] - [{self.focus}]")
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
            self.dumped.clear()

            dump_start_time = time.time()

            if not (app_pid := await device.pid_value(self.focus)):
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

            uid = uid if (uid := await device.uid_value(self.focus)) else 0

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
        if not (check := await device.examine_pkg(self.focus)):
            raise MemrixError(f"应用名称不存在 {self.focus} -> {check}")

        reporter = Reporter(
            self.src_total_place, self.vault, const.TRACK_TREE_DIR if self.track else const.LAPSE_TREE_DIR
        )

        logger.add(reporter.log_file, level=const.NOTE_LEVEL, format=const.WRITE_FORMAT)

        logger.info(
            f"^*{self.padding} {const.APP_DESC} Engine Start {self.padding}*^"
        )

        prefix = "TRACK" if self.track else "LAPSE"
        team_name = f"{prefix}_DATA_{(now_format := time.strftime('%Y%m%d%H%M%S'))}"
        await self.refresh(
            self.focus, reporter.team_file, team_name, device.serial, reporter.before_time
        )

        # Notes: ========== 启动工具 ==========
        toolkit: typing.Optional["ToolKit"] = ToolKit()

        if not (heaped := Path(reporter.group_dir) / "Heaped").exists():
            heaped.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(reporter.db_file) as db:
            await asyncio.gather(
                Cubicle.create_mem_table(db), Cubicle.create_joint_table(db)
            )
            await Cubicle.insert_joint_data(
                db, self.file_folder, self.title, Period.convert_time(now_format)
            )

            self.animation_task = asyncio.create_task(
                self.design.memory_wave(self.memories, self.task_close_event)
            )
            watcher = asyncio.create_task(self.watcher())

            heap_profile_task = None
            if self.lapse and self.hprof:
                heap_profile_task = asyncio.create_task(self.profile(device, str(heaped)))

            self.dumped = asyncio.Event()
            while not self.task_close_event.is_set():
                await flash_memory_launch()
                await asyncio.sleep(self.align.speed)

        if heap_profile_task:
            await heap_profile_task
        await watcher
        await self.sample_stop(reporter)

    # """帧影流光 / 引力回廊"""
    async def gfx_dump_task(self, device: "Device") -> None:

        async def input_stream() -> None:
            async for line in transports.stdout:
                logger.info(line.decode(const.CHARSET).strip())

        async def error_stream() -> None:
            async for line in transports.stderr:
                logger.info(line.decode(const.CHARSET).strip())

        # Notes: ========== Start from here ==========
        if not (check := await device.examine_pkg(self.focus)):
            raise MemrixError(f"应用名称不存在 {self.focus} -> {check}")

        reporter = Reporter(
            self.src_total_place, self.vault, const.SLEEK_TREE_DIR if self.sleek else const.SURGE_TREE_DIR
        )

        logger.add(reporter.log_file, level=const.NOTE_LEVEL, format=const.WRITE_FORMAT)

        logger.info(
            f"^*{self.padding} {const.APP_DESC} Engine Start {self.padding}*^"
        )

        prefix = "SLEEK" if self.sleek else "SURGE"
        team_name = f"{prefix}_DATA_{(now_format := time.strftime('%Y%m%d%H%M%S'))}"
        await self.refresh(
            self.focus, reporter.team_file, team_name, device.serial, reporter.before_time
        )

        # Notes: ========== 启动工具 ==========
        tracer: "Tracer" = Tracer()

        if not (traces := Path(reporter.group_dir) / "Traces").exists():
            traces.mkdir(parents=True, exist_ok=True)
        if not (images := Path(reporter.group_dir) / "Images").exists():
            images.mkdir(parents=True, exist_ok=True)

        head = f"{title}_{now_format}" if (title := self.title) else self.file_folder
        trace_loc = traces / f"{head}_trace.perfetto-trace"
        image_loc = images / f"{head}_image.png"

        device_folder = f"/data/misc/perfetto-configs/{Path(self.ft_file).name}"
        target_folder = f"/data/misc/perfetto-traces/trace_{now_format}.perfetto-trace"

        await device.push(self.ft_file, device_folder)
        await device.change_mode(777, device_folder)

        watcher = asyncio.create_task(self.watcher())

        transports = await device.perfetto_start(device_folder, target_folder)
        _ = asyncio.create_task(input_stream())
        _ = asyncio.create_task(error_stream())

        self.memories.update({
            "msg": (msg := f"开始采样 ...")
        })
        logger.info(msg)
        self.animation_task = asyncio.create_task(
            self.design.memory_wave(self.memories, (perfetto_event := asyncio.Event()))
        )
        await self.task_close_event.wait()
        await device.perfetto_close()
        self.memories.update({
            "msg": (msg := f"结束采样 ...")
        })
        logger.info(msg)

        self.memories.update({
            "msg": (msg := f"拉取 ...")
        })
        logger.info(msg)
        await device.pull(target_folder, str(trace_loc))

        self.memories.update({
            "msg": (msg := f"解析样本 ...")
        })
        logger.info(msg)
        with TraceProcessor(str(trace_loc), config=TraceProcessorConfig(self.tp_shell)) as tp:
            if self.sleek:
                if not (raw_frames := await tracer.extract_primary_frames(tp, self.focus)):
                    self.memories.update({
                        "msg": (msg := f"没有有效样本 ...")
                    })
                    logger.info(msg)
                    perfetto_event.set()
                    await self.animation_task
                    raise MemrixError(f"没有有效样本 ...")

                vsync_sys = await Tracer.extract_vsync_sys_points(tp)  # 系统FPS
                vsync_app = await Tracer.extract_vsync_app_points(tp)  # 应用FPS

                roll_ranges = await tracer.extract_roll_ranges(tp)  # 滑动区间
                drag_ranges = await tracer.extract_drag_ranges(tp)  # 拖拽区间

                jank_ranges = await tracer.mark_consecutive_jank(raw_frames)  # 连续丢帧

                await tracer.annotate_frames(
                    raw_frames, roll_ranges, drag_ranges, jank_ranges, vsync_sys, vsync_app
                )
                await Painter.draw_frame_timeline(
                    raw_frames, roll_ranges, drag_ranges, jank_ranges, vsync_sys, vsync_app, str(image_loc)
                )

                gfx_info = {
                    "raw_frames": json.dumps(raw_frames),
                    "vsync_sys": json.dumps(vsync_sys),
                    "vsync_app": json.dumps(vsync_app),
                    "roll_ranges": json.dumps(roll_ranges),
                    "drag_ranges": json.dumps(drag_ranges),
                    "jank_ranges": json.dumps(jank_ranges),
                }
                self.memories.update({
                    "msg": (msg := f"存储样本 ...")
                })
                logger.info(msg)
                async with aiosqlite.connect(reporter.db_file) as db:
                    await asyncio.gather(
                        Cubicle.create_gfx_table(db), Cubicle.create_joint_table(db)
                    )
                    await Cubicle.insert_joint_data(
                        db, self.file_folder, self.title, Period.convert_time(now_format)
                    )
                    await Cubicle.insert_gfx_data(
                        db, self.file_folder, self.align.label, Period.convert_time(now_format), gfx_info
                    )
                    self.file_insert += len(raw_frames)
                    self.memories.update({
                        "msg": (msg := f"Article {self.file_insert} data insert success")
                    })
                    logger.info(msg)

            else:
                gfx_info = await tracer.aggregate_io_metrics(tp, self.focus)
                self.design.console.print(gfx_info)

            perfetto_event.set()

        await watcher
        await self.sample_stop(reporter)

    # """真相快照"""
    async def observation(self) -> None:
        if not (target_dir := Path(self.src_total_place) / self.focus).exists():
            raise MemrixError(f"Target directory {target_dir} does not exist ...")

        segment_router = {
            const.TRACK_TREE_DIR: {
                "folder": const.TRACK_TREE_DIR,
                "method": "plot_mem_segments",
                "render": "track_rendition",
            },
            const.LAPSE_TREE_DIR: {
                "folder": const.LAPSE_TREE_DIR,
                "method": "plot_mem_segments",
                "render": "lapse_rendition",
            },
            const.SLEEK_TREE_DIR: {
                "folder": const.SLEEK_TREE_DIR,
                "method": "plot_gfx_segments",
                "render": "sleek_rendition",
            }
        }

        parent_dir = target_dir.parent.name
        try:
            router = segment_router[parent_dir]
        except KeyError:
            raise MemrixError(f"Unsupported directory type: {parent_dir} ...")

        folder = router["folder"]
        method = router["method"]
        render = router["render"]

        reporter = Reporter(self.src_total_place, self.focus, folder)

        for file in [reporter.db_file, reporter.log_file, reporter.team_file]:
            if not Path(file).is_file():
                raise MemrixError(f"文件无效 {file}")

        async with aiosqlite.connect(reporter.db_file) as db:
            templater = Templater(
                db, os.path.join(reporter.group_dir, f"Report_{Path(reporter.group_dir).name}")
            )

            team_data = await FileAssist.read_yaml(reporter.team_file)
            if not (data_list := team_data.get("file")):
                raise MemrixError(f"No data scenario {data_list} ...")

            if not (report_list := await asyncio.gather(*(getattr(templater, method)(d) for d in data_list))):
                raise MemrixError(f"No data scenario {report_list} ...")

            rendition = getattr(reporter, render)(self.align, team_data, report_list)

            return await reporter.make_report(self.unity_template, templater.download, **rendition)


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

    async def arithmetic(function: "typing.Callable") -> None:
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
        cmd_lines.track, cmd_lines.lapse, cmd_lines.sleek, cmd_lines.surge, cmd_lines.forge,
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

    if cmd_lines.track or cmd_lines.lapse:
        return await arithmetic(memrix.mem_dump_task)

    elif cmd_lines.sleek:
        return await arithmetic(memrix.gfx_dump_task)

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
