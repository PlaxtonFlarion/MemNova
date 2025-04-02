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

import os
import re
import sys
import time
import json
import typing
import signal
import shutil
import asyncio
import aiofiles
import aiosqlite
import uiautomator2
from loguru import logger
from collections import Counter
from rich.console import Console
from engine.device import Device
from memnova import const
from engine.manage import Manage
from engine.parser import Parser
from engine.analyzer import Analyzer
from engine.tackle import (
    Config, Grapher, DataBase,
    Terminal, RAM, MemrixError, ReadFile
)

console: typing.Optional["Console"] = Console()


class ToolKit(object):

    text_content: typing.Optional[str] = None

    @staticmethod
    def transform(number: typing.Any):
        try:
            return round(float(number) / 1024, 2)
        except TypeError:
            return 0.00

    @staticmethod
    def addition(*args):
        try:
            return round(sum([float(arg) for arg in args]), 2)
        except TypeError:
            return 0.00

    @staticmethod
    def subtract(n1: typing.Any, n2: typing.Any):
        try:
            return round(float(n1) - float(n2), 2)
        except TypeError:
            return 0.00

    def fit(self, pattern: typing.Any):
        if find := re.search(fr"{pattern}", self.text_content, re.S):
            return self.transform(find.group(1))


class Player(object):
    pass


class Memrix(object):

    data_insert: int
    file_folder: str

    exec_start_event: typing.Optional["asyncio.Event"] = asyncio.Event()
    dump_close_event: typing.Optional["asyncio.Event"] = asyncio.Event()

    dumped: typing.Optional["asyncio.Event"] = asyncio.Event()

    def __init__(
            self,
            memory: typing.Optional[bool],
            script: typing.Optional[bool],
            report: typing.Optional[bool],
            *args,
            **kwargs
    ):
        self.memory, self.script, self.report = memory, script, report

        sylora, *_ = args

        self.template = kwargs["template"]
        self.src_total_place = kwargs["src_total_place"]
        self.config = kwargs["config"]

        if self.report:
            folder: str = sylora
        else:
            self.before_time = time.time()
            folder: str = time.strftime("%Y%m%d%H%M%S", time.localtime(self.before_time))
            self.var_action = sylora

        self.total_dirs = os.path.join(self.src_total_place, "Memory_Folder")
        self.other_dirs = os.path.join(self.src_total_place, self.total_dirs, "Subset")
        self.group_dirs = os.path.join(self.src_total_place, self.other_dirs, folder)
        self.pools_dirs = os.path.join(self.src_total_place, self.total_dirs, "memory_data.db")
        self.logs_paths = os.path.join(self.group_dirs, f"logs_{folder}.log")
        self.team_paths = os.path.join(self.group_dirs, f"team_{folder}.txt")

    def clean_up(self, *_, **__) -> None:
        loop = asyncio.get_running_loop()
        loop.create_task(self.dump_task_close())

    async def dump_task_close(self) -> None:
        self.dump_close_event.set()
        await self.dumped.wait()
        head = f"{self.config.label} -> {self.file_folder} -> "
        tail = f"获取: {self.data_insert} -> 耗时: {round((time.time() - self.before_time) / 60, 2)} 分钟"
        logger.info(f"{head + tail}")
        logger.info(f"{self.group_dirs}")
        logger.info(f"^* Dump Close *^")

    async def dump_task_start(self, device: "Device"):

        async def flash_memory(pid):
            cmd = ["adb", "-s", device.serial, "shell", "dumpsys", "meminfo", self.var_action]
            if not (memory := await Terminal.cmd_line(*cmd)):
                return None

            logger.info(f"Dump memory [{pid}] - [{self.var_action}]")
            resume_map: dict = {}
            memory_map: dict = {}

            if match_memory := re.search(r"(\*\*.*?TOTAL (?:\s+\d+){8})", memory, re.S):
                toolkit.text_content = (clean_memory := re.sub(r"\s+", " ", match_memory.group()))
                memory_map.update({
                    "Native Heap": toolkit.fit("Native Heap .*?(\\d+)"),
                    "Dalvik Heap": toolkit.fit("Dalvik Heap .*?(\\d+)"),
                    "Dalvik Other": toolkit.fit("Dalvik Other .*?(\\d+)"),
                    "Stack": toolkit.fit("Stack .*?(\\d+)"),
                    "Ashmem": toolkit.fit("Ashmem .*?(\\d+)"),
                    "Other dev": toolkit.fit("Other dev .*?(\\d+)"),
                    ".so mmap": toolkit.fit(".so mmap .*?(\\d+)"),
                    ".jar mmap": toolkit.fit(".jar mmap .*?(\\d+)"),
                    ".apk mmap": toolkit.fit(".apk mmap .*?(\\d+)"),
                    ".ttf mmap": toolkit.fit(".ttf mmap .*?(\\d+)"),
                    ".dex mmap": toolkit.fit(".dex mmap .*?(\\d+)"),
                    ".oat mmap": toolkit.fit(".oat mmap .*?(\\d+)"),
                    ".art mmap": toolkit.fit(".art mmap .*?(\\d+)"),
                    "Other mmap": toolkit.fit("Other mmap .*?(\\d+)"),
                    "GL mtrack": toolkit.fit("GL mtrack .*?(\\d+)"),
                    "Unknown": toolkit.fit("Unknown .*?(\\d+)")
                })
                if total_memory := re.search(r"TOTAL.*\d+", clean_memory, re.S):
                    if part := total_memory.group().split():
                        resume_map.update({"TOTAL USS": toolkit.transform(part[2])})

            if match_resume := re.search(r"App Summary.*?TOTAL SWAP.*(\d+)", memory, re.S):
                toolkit.text_content = re.sub(r"\s+", " ", match_resume.group())
                resume_map.update(
                    {
                        "Graphics": toolkit.fit("Graphics: .*?(\\d+)"),
                        "TOTAL RSS": toolkit.fit("TOTAL RSS: .*?(\\d+)"),
                        "TOTAL PSS": toolkit.fit("TOTAL PSS: .*?(\\d+)"),
                        "TOTAL SWAP": toolkit.fit("TOTAL SWAP.*(\\d+)")
                    }
                )
                resume_map.update(
                    {
                        "OPSS": toolkit.subtract(resume_map.get("TOTAL PSS"), resume_map.get("Graphics"))
                    }
                )

            memory_vms = toolkit.transform(await device.pkg_value(pid))

            return {"resume_map": resume_map, "memory_map": memory_map, "memory_vms": memory_vms}

        async def flash_memory_launch():
            self.dumped.clear()

            dump_start_time = time.time()

            logger.info(device)

            if not (pids := await device.pid_value(self.var_action)):
                self.dumped.set()
                return logger.info(f"Process={pids}\n")

            logger.info({"Process": pids.member})
            remark_map = {"tms": time.strftime("%Y-%m-%d %H:%M:%S")}

            uid = uid if (uid := await device.uid_value(self.var_action)) else 0

            if not pids.member:
                self.dumped.set()
                return logger.info(f"[{pids.member}]\n")

            if not all(info_list := await asyncio.gather(
                    device.adj_value(list(pids.member.keys())[0]), device.act_value()
            )):
                self.dumped.set()
                return logger.info(f"{info_list}\n")

            adj, act = info_list
            remark_map.update({"uid": uid, "adj": adj, "act": act})
            remark_map.update({"frg": "前台" if (int(remark_map["adj"])) <= 0 else "后台"})
            logger.info(f"{remark_map['tms']}")
            logger.info(f"UID: {remark_map['uid']}")
            logger.info(f"ADJ: {remark_map['adj']}")
            logger.info(f"{remark_map['act']}")
            logger.info(f"{remark_map['frg']}")

            for k, v in pids.member.items():
                remark_map.update({"pid": k + " - " + v})

            memory_result = await asyncio.gather(
                *(flash_memory(key) for key in list(pids.member.keys()))
            )

            muster = Counter()
            for result in memory_result:
                if not result:
                    self.dumped.set()
                    return logger.info(f"{result}\n")
                muster.update(result)
            muster = dict(muster)

            display_map = muster["resume_map"].copy()
            logger.info(display_map | {"VmRss": muster["memory_vms"]})

            ram = RAM({"remark_map": remark_map} | muster)

            if all(maps := (ram.remark_map, ram.resume_map, ram.memory_map)):
                await DataBase.insert_data(
                    db, self.file_folder, self.config.label, *maps, ram.memory_vms
                )
                self.data_insert += 1
                logger.info(f"Article {self.data_insert} data insert success ...")
            else:
                logger.info(f"Data insert skipped ...")

            logger.info(f"{time.time() - dump_start_time:.2f} s\n")
            self.dumped.set()

        logger.add(self.logs_paths, level="INFO", format=const.LOG_FORMAT)

        async with aiofiles.open(self.team_paths, "a", encoding=const.ENCODING) as f:
            await f.write(f"{self.config.label} -> {self.file_folder}\n")

        if not os.path.exists(self.other_dirs):
            os.makedirs(self.other_dirs, exist_ok=True)

        toolkit = ToolKit()

        async with aiosqlite.connect(self.pools_dirs) as db:
            await DataBase.create_table(db)

            logger.info(f"^* Dump Start *^")
            self.data_insert = 0
            self.file_folder = f"DATA_{time.strftime('%Y%m%d%H%M%S')}"
            logger.info(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.before_time))}")
            logger.info(f"{self.var_action}")
            logger.info(f"{self.config.label}")
            logger.info(f"{self.file_folder}\n")

            self.exec_start_event.set()
            while not self.dump_close_event.is_set():
                await flash_memory_launch()
                await asyncio.sleep(self.config.speed)

    async def exec_task_start(self, device: "Device") -> None:
        try:
            assert os.path.isfile(self.var_action), self.var_action
            open_file = await asyncio.to_thread(ReadFile.read_json, self.var_action)
        except (AssertionError, FileNotFoundError, json.JSONDecodeError) as e:
            raise MemrixError(f"WARN: Json解析错误 {e}")

        if not (script := open_file.get("script", {})):
            raise MemrixError(f"WARN: 没有获取到脚本 ...")

        try:
            await device.u2_active()
        except (uiautomator2.exceptions.DeviceError, uiautomator2.exceptions.ConnectError) as e:
            raise MemrixError(e)

        auto_dump_task = asyncio.create_task(
            self.dump_task_start(device)
        )
        exec_done = asyncio.Event()

        player = Player()

        async def auto_exec_task():
            await self.exec_start_event.wait()

            logger.info(f"^* Exec Start *^")
            for data in range(open_file.get("looper", 1)):
                for key, values in script.items():
                    func_task_list = []
                    for i in values:
                        if self.dump_close_event.is_set():
                            return
                        if not (cmds := i.get("cmds", None)) or cmds not in ["u2", "sleep", "audio"]:
                            continue
                        if callable(func := getattr(player if cmds == "audio" else device, cmds)):
                            logger.info(
                                f"{func.__name__} {(vals := i.get('vals', []))} {(args := i.get('args', []))} {(kwds := i.get('kwds', {}))}"
                            )
                            func_task_list.append(asyncio.create_task(func(*vals, *args, **kwds)))
                            # logger.info(f"Returns: {await func(*vals, *args, **kwds)}")
                    await asyncio.gather(*func_task_list)
            exec_done.set()

        await auto_exec_task()
        await self.dump_task_close() if exec_done.is_set() else None

        auto_dump_task.cancel()
        try:
            await auto_dump_task
        except asyncio.CancelledError:
            logger.info(f"^* Exec Close *^")

    async def create_report(self):
        assert os.path.isfile(self.pools_dirs), self.pools_dirs
        assert os.path.isfile(self.logs_paths), self.logs_paths
        assert os.path.isfile(self.team_paths), self.team_paths

        async with aiosqlite.connect(self.pools_dirs) as db:
            analyzer = Analyzer(
                db, os.path.join(self.group_dirs, f"Report_{os.path.basename(self.group_dirs)}")
            )

            report_mains_dict = {
                "times": time.strftime("%Y-%m-%d %H:%M:%S"),
                "headline": self.config.headline,
                "criteria": self.config.criteria,
            }
            report_level_dict = {
                "fg_max": self.config.fg_max,
                "fg_avg": self.config.fg_avg,
                "bg_max": self.config.bg_max,
                "bg_avg": self.config.bg_avg
            }

            async with aiofiles.open(self.team_paths, "r", encoding=const.ENCODING) as file:
                memory_data_list = [
                    re.search(r"DATA_\d+", m).group() for m in await file.readlines()
                ]

            finals = await asyncio.gather(
                *(analyzer.draw_memory(directory) for directory in memory_data_list)
            )

            if report_list := [mem for mem in finals if mem]:
                return await analyzer.form_report(
                    report_mains_dict,
                    report_level_dict,
                    report_list,
                    os.path.dirname(self.template)
                )
            return logger.info("One Scenes Data ...")


async def main():
    if not shutil.which("adb"):
        return logger.info(f"ADB 环境变量未配置 ...")

    if len(sys.argv) == 1:
        return logger.info(f"命令参数为空 ...")

    if any((memory := _cmd_lines.memory, script := _cmd_lines.script, report := _cmd_lines.report)):
        if not (sylora := _cmd_lines.sylora):
            return logger.info(f"--sylora 参数不能为空 ...")

        memrix = Memrix(
            memory, script, report, sylora, **_keywords
        )

        if memory:
            signal.signal(signal.SIGINT, memrix.clean_up)
            return await memrix.dump_task_start(
                await Manage(console).operate_device(_cmd_lines.serial)
            )
        elif script:
            signal.signal(signal.SIGINT, memrix.clean_up)
            return await memrix.exec_task_start(
                await Manage(console).operate_device(_cmd_lines.serial)
            )
        elif report:
            return await memrix.create_report()

    return logger.info(f"主命令不能为空 ...")


if __name__ == '__main__':
    _software = os.path.basename(os.path.abspath(sys.argv[0])).strip().lower()

    Grapher("INFO", console)

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
        _mx_feasible = os.path.dirname(_mx_work)
    else:
        sys.exit(1)

    # 模板文件路径
    _template = os.path.join(_mx_work, "schematic", "templates", "memory.html")

    # 初始路径
    if not os.path.exists(
            _initial_source := os.path.join(_mx_feasible, "Specially").format()
    ):
        os.makedirs(_initial_source, exist_ok=True)

    # 报告路径
    if not os.path.exists(
            _src_total_place := os.path.join(_initial_source, "Memrix_Report").format()
    ):
        os.makedirs(_src_total_place, exist_ok=True)

    _config = Config(os.path.join(_initial_source, "Memrix_Mix", "config.yaml"))

    _keywords = {
        "template": _template, "src_total_place": _src_total_place, "config": _config
    }

    _cmd_lines = Parser.parse_cmd()

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, AssertionError, MemrixError):
        sys.exit(1)
    else:
        sys.exit(0)
