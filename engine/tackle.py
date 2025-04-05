#   _____          _    _
#  |_   _|_ _  ___| | _| | ___
#    | |/ _` |/ __| |/ / |/ _ \
#    | | (_| | (__|   <| |  __/
#    |_|\__,_|\___|_|\_\_|\___|
#
# 版权所有 (c) 2024  Memrix(记忆星核)
# 此文件受 Memrix(记忆星核) 许可证的保护。您可以在 LICENSE.md 文件中查看详细的许可条款。
#
# Copyright (c) 2024  Memrix(记忆星核)
# This file is licensed under the Memrix(记忆星核) License. See the LICENSE.md file for more details.
#

import os
import sys
import time
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

    def __str__(self):
        return f"[#FF4C4C]<{const.APP_DESC}Error> {self.msg}"

    __repr__ = __str__


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


class FileAssist(object):

    @staticmethod
    async def open(file: str) -> typing.Optional[str]:
        cmd = ["notepad++"] if sys.platform == "win32" else ["open", "-W", "-a", "TextEdit"]
        return await Terminal.cmd_line(*(cmd + [file]))

    @staticmethod
    def read_yaml(file: str) -> dict:
        with open(file, "r", encoding=const.ENCODING) as f:
            return yaml.load(f.read(), Loader=yaml.FullLoader)

    @staticmethod
    def read_json(file: str) -> dict:
        with open(file, "r", encoding=const.ENCODING) as f:
            return json.loads(f.read())

    @staticmethod
    def dump_yaml(src: typing.Any, dst: dict) -> None:
        with open(src, "w", encoding="utf-8") as f:
            yaml.dump(dst, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    @staticmethod
    def dump_json(src: typing.Any, dst: dict) -> None:
        with open(src, "w", encoding=const.ENCODING) as f:
            json.dump(dst, f, indent=4, separators=(",", ":"), ensure_ascii=False)


class Grapher(object):

    console: typing.Optional["Console"] = Console()

    @staticmethod
    def active(log_level: str) -> None:
        logger.remove()
        logger.add(
            RichHandler(console=Grapher.console, show_level=False, show_path=False, show_time=False),
            level=log_level, format=const.LOG_FORMAT
        )

    @staticmethod
    def view(msg: typing.Any) -> None:
        Grapher.console.print(
            f"{const.APP_DESC} {time.strftime('%Y-%m-%d %H:%M:%S')} | [#00D787]VIEW[/] | {msg}"
        )


class Pid(object):

    def __init__(self, member: typing.Optional[dict] = None):
        self.__member = member

    @property
    def member(self) -> typing.Optional[dict]:
        return self.__member


class Ram(object):

    def __init__(self, details: dict[str, dict]):
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
    def memory_vms(self) -> typing.Optional[dict]:
        return self.__details.get("memory_vms", None)


class Config(object):

    configs = {
        "Memory": {
            "speed": 1,
            "label": "应用名称"
        },
        "Script": {
            "group": "mission"
        },
        "Report": {
            "fg_max": 0.0,
            "fg_avg": 0.0,
            "bg_max": 0.0,
            "bg_avg": 0.0,
            "headline": "标题",
            "criteria": "标准"
        }
    }

    def __init__(self, config_file: typing.Any):
        self.load_config(config_file)

    def __getstate__(self):
        return self.configs

    def __setstate__(self, state):
        self.configs = state

    @property
    def speed(self):
        return self.configs["Memory"]["speed"]

    @property
    def label(self):
        return self.configs["Memory"]["label"]

    @property
    def group(self):
        return self.configs["Script"]["group"]

    @property
    def fg_max(self):
        return self.configs["Report"]["fg_max"]

    @property
    def fg_avg(self):
        return self.configs["Report"]["fg_avg"]

    @property
    def bg_max(self):
        return self.configs["Report"]["bg_max"]

    @property
    def bg_avg(self):
        return self.configs["Report"]["bg_avg"]

    @property
    def headline(self):
        return self.configs["Report"]["headline"]

    @property
    def criteria(self):
        return self.configs["Report"]["criteria"]

    @speed.setter
    def speed(self, value: typing.Any):
        self.configs["Memory"]["speed"] = Parser.parse_integer(value)

    @label.setter
    def label(self, value: typing.Any):
        self.configs["Memory"]["label"] = value

    @group.setter
    def group(self, value: typing.Any):
        self.configs["Script"]["group"] = value

    @fg_max.setter
    def fg_max(self, value: typing.Any):
        self.configs["Report"]["fg_max"] = Parser.parse_decimal(value)

    @fg_avg.setter
    def fg_avg(self, value: typing.Any):
        self.configs["Report"]["fg_avg"] = Parser.parse_decimal(value)

    @bg_max.setter
    def bg_max(self, value: typing.Any):
        self.configs["Report"]["bg_max"] = Parser.parse_decimal(value)

    @bg_avg.setter
    def bg_avg(self, value: typing.Any):
        self.configs["Report"]["bg_avg"] = Parser.parse_decimal(value)

    @headline.setter
    def headline(self, value: typing.Any):
        self.configs["Report"]["headline"] = value

    @criteria.setter
    def criteria(self, value: typing.Any):
        self.configs["Report"]["criteria"] = value

    def load_config(self, config_file: typing.Any) -> None:
        try:
            user_config = FileAssist.read_yaml(config_file)
            for key, value in self.configs.items():
                for k, v in value.items():
                    setattr(self, k, user_config.get(key, {}).get(k, v))
        except (FileNotFoundError, yaml.YAMLError):
            self.dump_config(config_file)

    def dump_config(self, config_file: typing.Any) -> None:
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        FileAssist.dump_yaml(config_file, self.configs)


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
            vmrss: dict
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

                vmrss["vms"]
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
