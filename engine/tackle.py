import os
import sys
import yaml
import json
import typing
import asyncio
import aiosqlite
from loguru import logger
from rich.console import Console
from rich.logging import RichHandler
from memnova import const
from engine.parser import Parser


class _MemrixBaseError(BaseException):
    pass


class MemrixError(_MemrixBaseError):

    def __init__(self, msg: typing.Any):
        self.msg = msg


class Terminal(object):

    @staticmethod
    async def cmd_line(*cmd: str) -> typing.Optional[str]:
        logger.debug([c for c in cmd])
        transports = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        encode = "GBK" if sys.platform == "win32" else "UTF-8"
        try:
            stdout, stderr = await asyncio.wait_for(transports.communicate(), timeout=3)
        except asyncio.TimeoutError:
            return None

        if stdout:
            return stdout.decode(encoding=encode, errors="ignore").strip()
        if stderr:
            return stderr.decode(encoding=encode, errors="ignore").strip()

    @staticmethod
    async def cmd_line_shell(cmd: str) -> typing.Optional[str]:
        logger.debug(cmd)
        transports = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        encode = "GBK" if sys.platform == "win32" else "UTF-8"
        try:
            stdout, stderr = await asyncio.wait_for(transports.communicate(), timeout=3)
        except asyncio.TimeoutError:
            return None

        if stdout:
            return stdout.decode(encoding=encode, errors="ignore").strip()
        if stderr:
            return stderr.decode(encoding=encode, errors="ignore").strip()


class ReadFile(object):

    @staticmethod
    def read_yaml(file: str) -> dict:
        with open(file, "r", encoding=const.ENCODING) as f:
            return yaml.load(f.read(), Loader=yaml.FullLoader)

    @staticmethod
    def read_json(file: str) -> dict:
        with open(file, "r", encoding=const.ENCODING) as f:
            return json.loads(f.read())


class Grapher(object):

    def __init__(self, log_level: str, console: "Console"):
        logger.remove()
        logger.add(
            RichHandler(console=console, show_level=False, show_path=False, show_time=False),
            level=log_level, format=const.LOG_FORMAT
        )


class PID(object):

    def __init__(self, member: typing.Optional[dict] = None):
        self.__member = member

    @property
    def member(self) -> typing.Optional[dict]:
        return self.__member


class RAM(object):

    def __init__(self, details: dict):
        self.__details = details

    @property
    def remark_map(self) -> typing.Optional[dict]:
        return self.__details.get("remark_map", None)

    @property
    def resume_map(self) -> typing.Optional[dict]:
        return self.__details.get("resume_map", None)

    @property
    def memory_map(self) -> typing.Optional[dict]:
        return self.__details.get("memory_map", None)

    @property
    def memory_vms(self) -> typing.Optional[typing.Any]:
        return self.__details.get("memory_vms", None)


class Config(object):

    __config = {
                "Memory": {
                    "speed": 1,
                    "label": "摘要标签"
                },
                "Report": {
                    "fg_max": 0.0,
                    "fg_avg": 0.0,
                    "bg_max": 0.0,
                    "bg_avg": 0.0,
                    "headline": "报告标题",
                    "criteria": "准出标准"
                }
            }

    def __init__(self, config_file: typing.Any):
        self.__load_config(config_file)

    def __getstate__(self):
        return self.__config

    def __setstate__(self, state):
        self.__config = state

    @property
    def speed(self):
        return self.__config["Memory"]["speed"]

    @property
    def label(self):
        return self.__config["Memory"]["label"]

    @property
    def fg_max(self):
        return self.__config["Report"]["fg_max"]

    @property
    def fg_avg(self):
        return self.__config["Report"]["fg_avg"]

    @property
    def bg_max(self):
        return self.__config["Report"]["bg_max"]

    @property
    def bg_avg(self):
        return self.__config["Report"]["bg_avg"]

    @property
    def headline(self):
        return self.__config["Report"]["headline"]

    @property
    def criteria(self):
        return self.__config["Report"]["criteria"]

    @speed.setter
    def speed(self, value: typing.Any):
        self.__config["Memory"]["speed"] = Parser.parse_integer(value)

    @label.setter
    def label(self, value: typing.Any):
        self.__config["Memory"]["label"] = value

    @fg_max.setter
    def fg_max(self, value: typing.Any):
        self.__config["Report"]["fg_max"] = Parser.parse_decimal(value)

    @fg_avg.setter
    def fg_avg(self, value: typing.Any):
        self.__config["Report"]["fg_avg"] = Parser.parse_decimal(value)

    @bg_max.setter
    def bg_max(self, value: typing.Any):
        self.__config["Report"]["bg_max"] = Parser.parse_decimal(value)

    @bg_avg.setter
    def bg_avg(self, value: typing.Any):
        self.__config["Report"]["bg_avg"] = Parser.parse_decimal(value)

    @headline.setter
    def headline(self, value: typing.Any):
        self.__config["Report"]["headline"] = value

    @criteria.setter
    def criteria(self, value: typing.Any):
        self.__config["Report"]["criteria"] = value

    def __load_config(self, config_file: typing.Any) -> None:
        try:
            user_config = ReadFile.read_yaml(config_file)
            for key, value in self.__config.items():
                for k, v in value.items():
                    setattr(self, k, user_config.get(key, {}).get(k, v))
        except (FileNotFoundError, yaml.YAMLError):
            self.__dump_config(config_file)

    def __dump_config(self, config_file: typing.Any) -> None:
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w", encoding="UTF-8") as f:
            yaml.dump(self.__config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


class DataBase(object):

    @staticmethod
    async def create_table(db: "aiosqlite.Connection"):
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
            vmrss: str
    ):
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

                vmrss
            )
        )
        await db.commit()

    @staticmethod
    async def query_data(db: "aiosqlite.Connection", data_dir: str) -> tuple[list, list]:

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
