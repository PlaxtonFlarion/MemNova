#    ____      _     _      _
#   / ___|   _| |__ (_) ___| | ___
#  | |  | | | | '_ \| |/ __| |/ _ \
#  | |__| |_| | |_) | | (__| |  __/
#   \____\__,_|_.__/|_|\___|_|\___|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import json
import typing
import asyncio
import aiosqlite
from memnova import const


class Cubicle(object):
    """Cubicle"""

    @staticmethod
    async def initialize_tables(
        db: "aiosqlite.Connection",
        data_dir: str,
        title: str,
        timestamp: str,
        payload: dict
    ) -> typing.Any:
        """
        初始化四类数据表并写入联合元信息的首条记录。

        Parameters
        ----------
        db : aiosqlite.Connection
            已连接的异步 SQLite 连接。

        data_dir : str
            任务数据目录名（同一任务的分组键）。

        title : str
            任务标题或显示名称。

        timestamp : str
            任务起始时间，建议使用 YYYY-MM-DD HH:MM:SS。

        payload : dict
            设备元信息字典，需包含 brand、model、release、serialno 等键。

        Returns
        -------
        Any
            插入联合表后的执行结果（通常为 None，取决于执行器行为）。
        """
        await asyncio.gather(
            Cubicle.joint_table(db), Cubicle.mem_table(db), Cubicle.gfx_table(db), Cubicle.io_table(db)
        )
        return await Cubicle.insert_joint(db, data_dir, title, timestamp, payload)

    @staticmethod
    async def joint_table(db: "aiosqlite.Connection") -> typing.Any:
        """
        创建联合元信息表，若不存在则新建。

        Parameters
        ----------
        db : aiosqlite.Connection
            已连接的异步 SQLite 连接。

        Returns
        -------
        Any
            执行结果（提交成功后通常为 None）。
        """
        await db.execute(f'''CREATE TABLE IF NOT EXISTS {const.JOINT_DATA_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_dir TEXT,
            title TEXT,
            timestamp TEXT,
            brand TEXT,
            model TEXT,
            release TEXT,
            serialno TEXT)''')
        return await db.commit()

    @staticmethod
    async def insert_joint(
        db: "aiosqlite.Connection",
        data_dir: str,
        title: str,
        timestamp: str,
        payload: dict,
    ) -> typing.Any:
        """
        向联合元信息表插入一条任务级元信息记录。

        Parameters
        ----------
        db : aiosqlite.Connection
            异步数据库连接。

        data_dir : str
            任务数据目录名。

        title : str
            任务标题。

        timestamp : str
            任务时间戳（YYYY-MM-DD HH:MM:SS）。

        payload : dict
            设备信息：brand、model、release、serialno。

        Returns
        -------
        Any
            执行结果（提交成功后通常为 None）。
        """
        await db.execute(f'''INSERT INTO {const.JOINT_DATA_TABLE} (
            data_dir,
            title,
            timestamp,
            brand,
            model,
            release,
            serialno) VALUES (?, ?, ?, ?, ?, ?, ?)''', (
                data_dir,
                title,
                timestamp,
                payload["brand"],
                payload["model"],
                payload["release"],
                payload["serialno"]
            )
        )
        return await db.commit()

    @staticmethod
    async def query_joint(db: "aiosqlite.Connection", data_dir: str) -> list[tuple]:
        """
        按 data_dir 查询联合元信息，返回任务级元数据。

        Parameters
        ----------
        db : aiosqlite.Connection
            异步数据库连接。

        data_dir : str
            任务数据目录名。

        Returns
        -------
        list of tuple
            包含 (title, timestamp, brand, model, release, serialno) 的结果集。
        """
        sql = f"""
            SELECT
                title,
                timestamp,
                brand,
                model,
                release,
                serialno
            FROM {const.JOINT_DATA_TABLE}
            WHERE data_dir = ?
        """
        async with db.execute(sql, (data_dir,)) as cursor:
            return await cursor.fetchall()

    # Notes: ======================== MEM ========================

    @staticmethod
    async def mem_table(db: "aiosqlite.Connection") -> typing.Any:
        """
        创建内存明细表，若不存在则新建。

        Parameters
        ----------
        db : aiosqlite.Connection
            异步数据库连接。

        Returns
        -------
        Any
            执行结果（提交成功后通常为 None）。
        """
        await db.execute(f'''CREATE TABLE IF NOT EXISTS {const.MEM_DATA_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_dir TEXT,
            label TEXT,
            timestamp TEXT,
            pid INTEGER,
            adj INTEGER,
            activity TEXT,
            mode TEXT,
            summary_java_heap REAL,
            summary_native_heap REAL,
            summary_graphics REAL,
            pss REAL,
            rss REAL,
            uss REAL,
            swap REAL,
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
            unknown REAL)''')
        return await db.commit()

    @staticmethod
    async def insert_mem(
        db: "aiosqlite.Connection",
        data_dir: str,
        label: str,
        payload: dict
    ) -> typing.Any:
        """
        插入一条内存采样记录（包含标注与明细分区）。

        Parameters
        ----------
        db : aiosqlite.Connection
            异步数据库连接。

        data_dir : str
            任务数据目录名。

        label : str
            任务或应用标签。

        payload : dict
            结构化内存数据，包含 mark/summary/meminfo 子字典。

        Returns
        -------
        Any
            执行结果（提交成功后通常为 None）。
        """
        await db.execute(f'''INSERT INTO {const.MEM_DATA_TABLE} (
            data_dir,
            label,
            timestamp,
            pid,
            adj,
            activity,
            mode,
            summary_java_heap,
            summary_native_heap,
            summary_graphics,
            pss,
            rss,
            uss,
            swap,
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
            unknown) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                data_dir,
                label,

                payload["mark"]["tms"],
                payload["mark"]["pid"],
                payload["mark"]["adj"],
                payload["mark"]["act"],
                payload["mark"]["mode"],

                payload["summary"]["Java Heap"],
                payload["summary"]["Native Heap"],
                payload["summary"]["Graphics"],
                payload["summary"]["TOTAL PSS"],
                payload["summary"]["TOTAL RSS"],
                payload["meminfo"]["TOTAL USS"],
                payload["summary"]["TOTAL SWAP"],

                payload["meminfo"]["Native Heap"],
                payload["meminfo"]["Dalvik Heap"],
                payload["meminfo"]["Dalvik Other"],
                payload["meminfo"]["Stack"],
                payload["meminfo"]["Ashmem"],
                payload["meminfo"]["Other dev"],
                payload["meminfo"][".so mmap"],
                payload["meminfo"][".jar mmap"],
                payload["meminfo"][".apk mmap"],
                payload["meminfo"][".ttf mmap"],
                payload["meminfo"][".dex mmap"],
                payload["meminfo"][".oat mmap"],
                payload["meminfo"][".art mmap"],
                payload["meminfo"]["Other mmap"],
                payload["meminfo"]["GL mtrack"],
                payload["meminfo"]["Unknown"]
            )
        )
        return await db.commit()

    @staticmethod
    async def query_mem(db: "aiosqlite.Connection", data_dir: str) -> list[dict]:
        """
        按 data_dir 查询内存采样核心字段，按时间升序返回。

        Parameters
        ----------
        db : aiosqlite.Connection
            异步数据库连接。

        data_dir : str
            任务数据目录名。

        Returns
        -------
        list of dict
            每条记录包含 timestamp、adj、activity、mode、summary_*、pss/rss/uss/swap 等。
        """
        sql = f"""
            SELECT
                timestamp,
                adj,
                activity,
                mode,
                summary_java_heap,
                summary_native_heap,
                summary_graphics,
                pss,
                rss,
                uss,
                swap
            FROM {const.MEM_DATA_TABLE}
            WHERE data_dir = ? AND pss != ''
            ORDER BY timestamp ASC
        """
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, (data_dir,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # Notes: ======================== GFX ========================

    @staticmethod
    async def gfx_table(db: "aiosqlite.Connection") -> typing.Any:
        """
        创建图形帧数据表，若不存在则新建。

        Parameters
        ----------
        db : aiosqlite.Connection
            异步数据库连接。

        Returns
        -------
        Any
            执行结果（提交成功后通常为 None）。
        """
        await db.execute(f'''CREATE TABLE IF NOT EXISTS {const.GFX_DATA_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_dir TEXT,
            label TEXT,
            timestamp TEXT,
            metadata TEXT,
            raw_frames TEXT,
            vsync_sys TEXT,
            vsync_app TEXT,
            roll_ranges TEXT,
            drag_ranges TEXT,
            jank_ranges TEXT)''')
        return await db.commit()

    @staticmethod
    async def insert_gfx(
        db: "aiosqlite.Connection",
        data_dir: str,
        label: str,
        timestamp: str,
        payload: dict
    ) -> typing.Any:
        """
        插入一条图形时序记录（含帧、VSYNC、滚动/拖拽/掉帧区间）。

        Parameters
        ----------
        db : aiosqlite.Connection
            异步数据库连接。

        data_dir : str
            任务数据目录名。

        label : str
            任务或应用标签。

        timestamp : str
            采样时间（YYYY-MM-DD HH:MM:SS）。

        payload : dict
            已序列化为 JSON 的字段：metadata/raw_frames/vsync_sys/vsync_app/roll/drag/jank。

        Returns
        -------
        Any
            执行结果（提交成功后通常为 None）。
        """
        await db.execute(f'''INSERT INTO {const.GFX_DATA_TABLE} (
            data_dir,
            label,
            timestamp,
            metadata,
            raw_frames,
            vsync_sys,
            vsync_app,
            roll_ranges,
            drag_ranges,
            jank_ranges) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                data_dir,
                label,
                timestamp,
                payload["metadata"],
                payload["raw_frames"],
                payload["vsync_sys"],
                payload["vsync_app"],
                payload["roll_ranges"],
                payload["drag_ranges"],
                payload["jank_ranges"]
            )
        )
        return await db.commit()

    @staticmethod
    async def query_gfx(db: "aiosqlite.Connection", data_dir: str) -> list[dict]:
        """
        按 data_dir 查询图形时序数据，并将 JSON 字段反序列化为 Python 对象。

        Parameters
        ----------
        db : aiosqlite.Connection
            异步数据库连接。

        data_dir : str
            任务数据目录名。

        Returns
        -------
        list of dict
            每条包含 metadata、raw_frames、vsync_sys、vsync_app、roll_ranges、drag_ranges、jank_ranges。
        """
        sql = f"""
            SELECT
                metadata,
                raw_frames,
                vsync_sys,
                vsync_app,
                roll_ranges,
                drag_ranges,
                jank_ranges
            FROM {const.GFX_DATA_TABLE}
            WHERE data_dir = ?
        """
        async with db.execute(sql, (data_dir,)) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "metadata": json.loads(md),
                    "raw_frames": json.loads(rf),
                    "vsync_sys": json.loads(vs),
                    "vsync_app": json.loads(va),
                    "roll_ranges": json.loads(rr),
                    "drag_ranges": json.loads(dr),
                    "jank_ranges": json.loads(jr),
                }
                for md, rf, vs, va, rr, dr, jr in rows
            ]

    # Notes: ======================== I/O ========================

    @staticmethod
    async def io_table(db: "aiosqlite.Connection") -> typing.Any:
        """
        创建 I/O 数据表，若不存在则新建。

        Parameters
        ----------
        db : aiosqlite.Connection
            异步数据库连接。

        Returns
        -------
        Any
            执行结果（提交成功后通常为 None）。
        """
        await db.execute(f'''CREATE TABLE IF NOT EXISTS {const.IO_DATA_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_dir TEXT,
            label TEXT,
            timestamp TEXT,
            swap REAL,
            rchar INTEGER,
            wchar INTEGER,
            syscr INTEGER,
            syscw INTEGER,
            read_bytes INTEGER,
            write_bytes INTEGER,
            cancelled_write_bytes INTEGER)''')
        return await db.commit()

    @staticmethod
    async def insert_io(
        db: "aiosqlite.Connection",
        data_dir: str,
        label: str,
        timestamp: str,
        payload: dict
    ) -> typing.Any:
        """
        插入一条 I/O 采样记录。

        Parameters
        ----------
        db : aiosqlite.Connection
            异步数据库连接。

        data_dir : str
            任务数据目录名。

        label : str
            任务或应用标签。

        timestamp : str
            采样时间（YYYY-MM-DD HH:MM:SS）。

        payload : dict
            I/O 指标字典：swap、rchar、wchar、syscr、syscw、read_bytes、write_bytes、cancelled_write_bytes。

        Returns
        -------
        Any
            执行结果（提交成功后通常为 None）。
        """
        await db.execute(f'''INSERT INTO {const.IO_DATA_TABLE} (
            data_dir,
            label,
            timestamp,
            swap,
            rchar,
            wchar,
            syscr,
            syscw,
            read_bytes,
            write_bytes,
            cancelled_write_bytes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                data_dir,
                label,
                timestamp,
                payload["swap"],
                payload["rchar"],
                payload["wchar"],
                payload["syscr"],
                payload["syscw"],
                payload["read_bytes"],
                payload["write_bytes"],
                payload["cancelled_write_bytes"]
            )
        )
        return await db.commit()

    @staticmethod
    async def query_io(db: "aiosqlite.Connection", data_dir: str) -> list[dict]:
        """
        按 data_dir 查询 I/O 序列数据，按时间升序返回。

        Parameters
        ----------
        db : aiosqlite.Connection
            异步数据库连接。

        data_dir : str
            任务数据目录名。

        Returns
        -------
        list of dict
            每条记录包含 timestamp、swap、rchar、wchar、syscr、syscw、read_bytes、write_bytes。
        """
        sql = f"""
            SELECT
                timestamp,
                swap,
                rchar,
                wchar,
                syscr,
                syscw,
                read_bytes,
                write_bytes
            FROM {const.IO_DATA_TABLE}
            WHERE data_dir = ?
            ORDER BY timestamp ASC
        """
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, (data_dir,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


if __name__ == '__main__':
    pass
