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
from loguru import logger
from collections import Counter
from engine import const
from engine.device import Device
from engine.manage import Manage
from engine.parser import Parser
from engine.tackle import Config, Log, DataBase, Terminal, RAM, MemrixError, ReadFile


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


class Memrix(object):

    data_insert: int
    file_folder: str
    start_event: typing.Optional["asyncio.Event"] = asyncio.Event()
    close_event: typing.Optional["asyncio.Event"] = asyncio.Event()

    def __init__(
            self,
            memory: typing.Optional[bool],
            script: typing.Optional[bool],
            report: typing.Optional[bool],
            *args,
            **kwargs
    ):
        self.memory, self.script, self.report = memory, script, report

        sylora, self.serial, *_ = args

        self.template = kwargs["template"]
        self.src_total_place = kwargs["src_total_place"]
        self.config = kwargs["config"]

        if self.report:
            folder: str = sylora
        else:
            folder: str = time.strftime("%Y%m%d%H%M%S")
            self.var_action = sylora

        self.total_dirs = os.path.join(self.src_total_place, "Memory_Folder")
        self.other_dirs = os.path.join(self.src_total_place, self.total_dirs, "Subset")
        self.group_dirs = os.path.join(self.src_total_place, self.other_dirs, folder)
        self.pools_dirs = os.path.join(self.src_total_place, self.total_dirs, "memory_data.db")
        self.logs_paths = os.path.join(self.group_dirs, f"logs_{folder}.log")
        self.team_paths = os.path.join(self.group_dirs, f"team_{folder}.txt")

    async def dump_task(self):

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
            start_time = time.time()

            if not (pids := await device.pid_value(self.var_action)):
                return logger.info(f"{pids}\n")

            logger.info(device)
            logger.info({"Process": pids.member})
            remark_map = {"tms": time.strftime("%Y-%m-%d %H:%M:%S")}

            uid = uid if (uid := await device.uid_value(self.var_action)) else 0

            if not pids.member:
                return logger.info(f"[{pids.member}]\n")

            if not all(info_list := await asyncio.gather(
                    device.adj_value(list(pids.member.keys())[0]), device.act_value()
            )):
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
                logger.info(f"Article {self.data_insert} data insert success ...")
                self.data_insert += 1
            else:
                logger.info(f"Data insert skipped ...")

            logger.info(f"{time.time() - start_time:.2f} s\n")

        device = await Manage.operate_device()

        logger.add(self.logs_paths, level="INFO", format=const.LOG_FORMAT)

        logger.info(f"{'=' * 10} Memory Dump Start {'=' * 10}")
        self.data_insert = 0
        self.file_folder = "DATA_" + time.strftime("%Y%m%d%H%M%S")
        logger.info(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}")
        logger.info(f"{self.var_action}")
        logger.info(f"{self.config.label}")

        logger.info(f"{self.file_folder}\n")
        async with aiofiles.open(self.team_paths, "a", encoding=const.ENCODING) as f:
            await f.write(f"{self.config.label} -> {self.file_folder}\n")

        if not os.path.exists(self.other_dirs):
            os.makedirs(self.other_dirs, exist_ok=True)

        toolkit = ToolKit()

        async with aiosqlite.connect(self.pools_dirs) as db:
            await DataBase.create_table(db)
            await device.device_online()
            self.start_event.set()
            while True:
                if self.close_event.is_set():
                    return
                await flash_memory_launch()
                await asyncio.sleep(self.config.speed)

    # todo
    async def stop_task(self):
        pass

    # todo
    async def exec_task(self):
        try:
            open_file = await asyncio.to_thread(ReadFile.read_json, self.var_action)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise MemrixError(e)

        print(open_file)

    # todo
    async def stop_exec(self):
        pass

    # todo
    async def create_report(self):
        assert os.path.isfile(self.pools_dirs), self.pools_dirs
        assert os.path.isfile(self.logs_paths), self.logs_paths
        assert os.path.isfile(self.team_paths), self.team_paths


async def main():
    if not shutil.which("adb"):
        return logger.info(f"ADB 环境变量未配置 ...")

    if len(sys.argv) == 1:
        return logger.info(f"命令参数为空 ...")

    if any((memory := _cmd_lines.memory, script := _cmd_lines.script, report := _cmd_lines.report)):
        if not (sylora := _cmd_lines.sylora):
            return logger.info(f"--sylora 参数不能为空 ...")

        memrix = Memrix(
            memory, script, report, sylora, _cmd_lines.serial, **_keywords
        )
        if memory:
            return await memrix.dump_task()
        elif script:
            return await memrix.exec_task()
        elif report:
            return await memrix.create_report()

    return logger.info(f"主命令不能为空 ...")


if __name__ == '__main__':
    _software = os.path.basename(os.path.abspath(sys.argv[0])).strip().lower()

    _log = Log()

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

    _main_loop: "asyncio.AbstractEventLoop" = asyncio.get_event_loop()

    try:
        _main_loop.run_until_complete(main())
    except (KeyboardInterrupt, MemrixError):
        sys.exit(1)
    else:
        sys.exit(0)
