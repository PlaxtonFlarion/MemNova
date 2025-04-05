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
import aiosqlite
import uiautomator2
from loguru import logger
from collections import Counter
from engine.device import Device
from memnova import const
from engine.manage import Manage
from engine.parser import Parser
from engine.display import Display
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

    text_content: typing.Optional[str] = None

    @staticmethod
    def transform(number: typing.Any) -> float:
        try:
            return round(float(number) / 1024, 2)
        except TypeError:
            return 0.00

    @staticmethod
    def addition(*numbers) -> float:
        try:
            return round(sum([float(number) for number in numbers]), 2)
        except TypeError:
            return 0.00

    @staticmethod
    def subtract(number_begin: typing.Any, number_final: typing.Any) -> float:
        try:
            return round(float(number_begin) - float(number_final), 2)
        except TypeError:
            return 0.00

    def fit(self, pattern: typing.Union[str, "re.Pattern[str]"]) -> float:
        return self.transform(find.group(1)) if (
            find := re.search(fr"{pattern}", self.text_content, re.S)
        ) else 0.00


class Player(object):

    @staticmethod
    async def audio(audio_file: str) -> None:
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)


class Memrix(object):

    file_insert: typing.Optional[int]
    file_folder: typing.Optional[str]

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

        self.sylora, *_ = args

        self.src_total_place = kwargs["src_total_place"]
        self.template = kwargs["template"]
        self.config = kwargs["config"]

        if self.report:
            folder: str = self.sylora
        else:
            self.before_time = time.time()
            folder: str = time.strftime("%Y%m%d%H%M%S", time.localtime(self.before_time))

        self.total_dir = os.path.join(self.src_total_place, f"Memory_Folder")
        self.other_dir = os.path.join(self.src_total_place, self.total_dir, f"Subset")
        self.group_dir = os.path.join(self.src_total_place, self.other_dir, folder)

        self.db_file = os.path.join(self.src_total_place, self.total_dir, f"memory_data.db")
        self.log_file = os.path.join(self.group_dir, f"log_{folder}.log")
        self.team_file = os.path.join(self.group_dir, f"team_{folder}.yaml")

    def clean_up(self, *_, **__) -> None:
        loop = asyncio.get_running_loop()
        loop.create_task(self.dump_task_close())

    async def dump_task_close(self) -> None:
        self.dump_close_event.set()
        await self.dumped.wait()

        try:
            await asyncio.gather(
                *(asyncio.to_thread(task.cancel) for task in asyncio.all_tasks())
            )
        except asyncio.CancelledError:
            Grapher.view(f"[#E69F00]Canceled Task ...")

        time_cost = round((time.time() - self.before_time) / 60, 2)
        logger.info(
            f"{self.config.label} -> {self.file_folder} -> 获取: {self.file_insert} -> 耗时: {time_cost} 分钟"
        )
        logger.info(f"{self.group_dir}")
        logger.info(f"^* Dump Close *^")

    async def dump_task_start(self, device: "Device") -> None:

        async def flash_memory(pid: str) -> typing.Optional[dict[str, dict]]:
            if not (memory := await device.memory_info(package)):
                return None

            logger.info(f"Dump memory [{pid}] - [{package}]")
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

            memory_vms: dict = {"vms": toolkit.transform(await device.pkg_value(pid))}

            return {"resume_map": resume_map, "memory_map": memory_map, "memory_vms": memory_vms}

        async def flash_memory_launch() -> None:
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
            remark_map.update({"frg": "前台" if (int(remark_map["adj"])) <= 0 else "后台"})
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
                muster = {}
                for result in memory_result:
                    for k, v in result.items():
                        muster[k] = muster.get(k, Counter()) + Counter(v)
                muster = {k: dict(v) for k, v in muster.items()}
            else:
                self.dumped.set()
                return logger.info(f"{memory_result}\n")

            logger.info(muster["resume_map"].copy() | {"VmRss": muster["memory_vms"]["vms"]})

            ram = Ram({"remark_map": remark_map} | muster)

            if all(maps := (ram.remark_map, ram.resume_map, ram.memory_map)):
                await DataBase.insert_data(
                    db, self.file_folder, self.config.label, *maps, ram.memory_vms
                )
                self.file_insert += 1
                logger.info(f"Article {self.file_insert} data insert success ...")
            else:
                logger.info(f"Data insert skipped ...")

            self.dumped.set()
            return logger.info(f"{time.time() - dump_start_time:.2f} s\n")

        package: typing.Optional[str] = self.sylora

        if "Unable" in (check := await device.examine_package(package)):
            raise MemrixError(check)

        logger.add(self.log_file, level="INFO", format=const.LOG_FORMAT)

        logger.info(f"^* Dump Start *^")
        format_before_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.before_time))

        self.file_insert = 0
        self.file_folder = f"DATA_{time.strftime('%Y%m%d%H%M%S')}"

        logger.info(f"{format_before_time}")
        logger.info(f"{package}")
        logger.info(f"{self.config.label}")
        logger.info(f"{self.file_folder}\n")

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

        toolkit: "ToolKit" = ToolKit()

        async with aiosqlite.connect(self.db_file) as db:
            await DataBase.create_table(db)
            await dump_file_task
            self.exec_start_event.set()
            while not self.dump_close_event.is_set():
                await flash_memory_launch()
                await asyncio.sleep(self.config.speed)

    async def exec_task_start(self, device: "Device") -> None:
        try:
            open_file = await asyncio.to_thread(FileAssist.read_json, self.sylora)
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

        auto_dump_task = asyncio.create_task(self.dump_task_start(device))

        player: "Player" = Player()

        logger.info(f"^* Exec Start *^")
        for data in range(loopers):
            for key, values in mission.items():
                for i in values:
                    if not (cmds := i.get("cmds", None)) or cmds not in ["u2", "sleep", "audio"]:
                        continue
                    if callable(func := getattr(player if cmds == "audio" else device, cmds)):
                        vals, args, kwds = i.get("vals", []), i.get("args", []), i.get("kwds", {})
                        Grapher.view(
                            f"[#AFD7FF]{func.__name__} {vals} {args} {kwds} -> {await func(*vals, *args, **kwds)}"
                        )

        await self.dump_task_close()

        auto_dump_task.cancel()
        try:
            await auto_dump_task
        except asyncio.CancelledError:
            logger.info(f"^* Exec Close *^")

    async def create_report(self) -> None:
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

        avg_fg_max_values = [i["fg_max"] for i in report_list if "fg_max" in i]
        avg_fg_max = round(sum(avg_fg_max_values) / len(avg_fg_max_values), 2) if avg_fg_max_values else None
        avg_fg_avg_values = [i["fg_avg"] for i in report_list if "fg_avg" in i]
        avg_fg_avg = round(sum(avg_fg_avg_values) / len(avg_fg_avg_values), 2) if avg_fg_avg_values else None

        avg_bg_max_values = [i["bg_max"] for i in report_list if "bg_max" in i]
        avg_bg_max = round(sum(avg_bg_max_values) / len(avg_bg_max_values), 2) if avg_bg_max_values else None
        avg_bg_avg_values = [i["bg_avg"] for i in report_list if "bg_avg" in i]
        avg_bg_avg = round(sum(avg_bg_avg_values) / len(avg_bg_avg_values), 2) if avg_bg_avg_values else None

        rendering = {
            "title": f"{const.APP_DESC} Information",
            "major": {
                "time": team_data["time"],
                "headline": self.config.headline,
                "criteria": self.config.criteria,
            },
            "level": {
                "fg_max": self.config.fg_max, "fg_avg": self.config.fg_avg,
                "bg_max": self.config.bg_max, "bg_avg": self.config.bg_avg,
            },
            "average": {
                "avg_fg_max": avg_fg_max, "avg_fg_avg": avg_fg_avg,
                "avg_bg_max": avg_bg_max, "avg_bg_avg": avg_bg_avg,
            },
            "report_list": report_list
        }
        return await analyzer.form_report(self.template, **rendering)


async def main() -> typing.Optional[typing.Any]:
    if not shutil.which("adb"):
        raise MemrixError(f"ADB 环境变量未配置 ...")

    if len(sys.argv) == 1:
        raise MemrixError(f"命令参数为空 ...")

    if _cmd_lines.config:
        # 显示 Logo & License
        Display.show_logo()
        Display.show_license()

        Grapher.console.print_json(data=_config.configs)
        return await FileAssist.open(_config_file)

    if any((memory := _cmd_lines.memory, script := _cmd_lines.script, report := _cmd_lines.report)):
        if not (sylora := _cmd_lines.sylora):
            raise MemrixError(f"--sylora 参数不能为空 ...")

        # 显示 Logo & License
        Display.show_logo()
        Display.show_license()

        memrix = Memrix(
            memory, script, report, sylora, **_keywords
        )

        if memory:
            signal.signal(signal.SIGINT, memrix.clean_up)
            return await memrix.dump_task_start(
                await Manage.operate_device(_cmd_lines.serial)
            )
        elif script:
            signal.signal(signal.SIGINT, memrix.clean_up)
            return await memrix.exec_task_start(
                await Manage.operate_device(_cmd_lines.serial)
            )
        elif report:
            return await memrix.create_report()

    raise MemrixError(f"主命令不能为空 ...")


if __name__ == '__main__':
    #   __  __                     _        ____  _             _
    #  |  \/  | ___ _ __ ___  _ __(_)_  __ / ___|| |_ __ _ _ __| |_ ___ _ __
    #  | |\/| |/ _ \ '_ ` _ \| '__| \ \/ / \___ \| __/ _` | '__| __/ _ \ '__|
    #  | |  | |  __/ | | | | | |  | |>  <   ___) | || (_| | |  | ||  __/ |
    #  |_|  |_|\___|_| |_| |_|_|  |_/_/\_\ |____/ \__\__,_|_|   \__\___|_|

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
        _mx_feasible = os.path.dirname(_mx_work)
    else:
        Grapher.view(
            MemrixError(f"{const.APP_DESC} Adaptation Platform Windows or MacOS ...")
        )
        Display.show_fail()
        sys.exit(1)

    # 模板文件夹
    _template = os.path.join(_mx_work, const.SCHEMATIC, "templates", "memory.html")
    # 检查模板文件是否存在，如果缺失则显示错误信息并退出程序
    if not os.path.isfile(_template) and os.path.basename(_template).endswith(".html"):
        _tmp_name = os.path.basename(_template)
        Grapher.view(
            MemrixError(f"{const.APP_DESC}  missing files {_tmp_name} ...")
        )
        Display.show_fail()
        sys.exit(1)

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
            Grapher.view(
                MemrixError(f"{const.APP_DESC} missing files {_tls_name}")
            )
            Display.show_fail()
            sys.exit(1)

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

    # 打包关键字参数
    _keywords = {
        "src_total_place": _src_total_place, "template": _template, "config": _config,
    }

    # 命令行
    _cmd_lines = Parser.parse_cmd()

    try:
        asyncio.run(main())
    except MemrixError as _memrix_error:
        Grapher.view(_memrix_error)
        Display.show_fail()
        sys.exit(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        Display.show_done()
        sys.exit(0)
    else:
        Display.show_done()
        sys.exit(0)
