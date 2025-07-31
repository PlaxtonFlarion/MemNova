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


class Cubicle(object):
    """Cubicle"""

    __joint_table = "joint_table"
    __mem_data_table = "mem_data"
    __gfx_data_table = "gfx_data"
    __io_data_table = "io_data"

    @staticmethod
    async def initialize_tables(
        db: "aiosqlite.Connection",
        data_dir: str,
        title: str,
        timestamp: str,
        payload: dict
    ) -> typing.Any:

        await asyncio.gather(
            Cubicle.__create_joint_table(db), 
            Cubicle.__create_mem_table(db), 
            Cubicle.__create_gfx_table(db),
            Cubicle.__create_io_table(db)
        )
        return await Cubicle.insert_joint_data(db, data_dir, title, timestamp, payload)

    @staticmethod
    async def __create_joint_table(db: "aiosqlite.Connection") -> typing.Any:
        await db.execute(f'''CREATE TABLE IF NOT EXISTS {Cubicle.__joint_table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_dir TEXT,
            title TEXT,
            timestamp TEXT,
            brand TEXT,
            model TEXT,
            release TEXT,
            serialno TEXT)''')
        await db.commit()

    @staticmethod
    async def insert_joint_data(
        db: "aiosqlite.Connection",
        data_dir: str,
        title: str,
        timestamp: str,
        payload: dict,
    ):
        await db.execute(f'''INSERT INTO {Cubicle.__joint_table} (
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
        await db.commit()

    @staticmethod
    async def query_joint_data(db: "aiosqlite.Connection", data_dir: str) -> list[tuple]:
        sql = f"""
            SELECT
                title,
                timestamp,
                brand,
                model,
                release,
                serialno
            FROM {Cubicle.__joint_table}
            WHERE data_dir = ?
        """
        async with db.execute(sql, (data_dir,)) as cursor:
            return await cursor.fetchall()

    # Notes: ======================== MEM ========================

    @staticmethod
    async def __create_mem_table(db: "aiosqlite.Connection") -> None:
        await db.execute(f'''CREATE TABLE IF NOT EXISTS {Cubicle.__mem_data_table} (
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
        await db.commit()

    @staticmethod
    async def insert_mem_data(
        db: "aiosqlite.Connection",
        data_dir: str,
        label: str,
        payload: dict
    ) -> None:

        await db.execute(f'''INSERT INTO {Cubicle.__mem_data_table} (
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
        await db.commit()

    @staticmethod
    async def query_mem_data(db: "aiosqlite.Connection", data_dir: str) -> list[dict]:
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
            FROM {Cubicle.__mem_data_table}
            WHERE data_dir = ? AND pss != ''
            ORDER BY timestamp ASC
        """
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, (data_dir,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # Notes: ======================== GFX ========================

    @staticmethod
    async def __create_gfx_table(db: "aiosqlite.Connection") -> None:
        await db.execute(f'''CREATE TABLE IF NOT EXISTS {Cubicle.__gfx_data_table} (
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
        await db.commit()

    @staticmethod
    async def insert_gfx_data(
        db: "aiosqlite.Connection",
        data_dir: str,
        label: str,
        timestamp: str,
        payload: dict
    ) -> None:

        await db.execute(f'''INSERT INTO {Cubicle.__gfx_data_table} (
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
        await db.commit()

    @staticmethod
    async def query_gfx_data(db: "aiosqlite.Connection", data_dir: str) -> list[dict]:
        sql = f"""
            SELECT
                metadata,
                raw_frames,
                vsync_sys,
                vsync_app,
                roll_ranges,
                drag_ranges,
                jank_ranges
            FROM {Cubicle.__gfx_data_table}
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
    async def __create_io_table(db: "aiosqlite.Connection") -> None:
        await db.execute(f'''CREATE TABLE IF NOT EXISTS {Cubicle.__io_data_table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_dir TEXT,
            label TEXT,
            timestamp TEXT,
            rchar INTEGER,
            wchar INTEGER,
            syscr INTEGER,
            syscw INTEGER,
            read_bytes INTEGER,
            write_bytes INTEGER,
            cancelled_write_bytes INTEGER)''')
        await db.commit()

    @staticmethod
    async def insert_io_data(
        db: "aiosqlite.Connection",
        data_dir: str,
        label: str,
        timestamp: str,
        payload: dict
    ) -> None:

        await db.execute(f'''INSERT INTO {Cubicle.__io_data_table} (
            data_dir,
            label,
            timestamp,
            rchar,
            wchar,
            syscr,
            syscw,
            read_bytes,
            write_bytes,
            cancelled_write_bytes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                data_dir,
                label,
                timestamp,
                payload["io"]["rchar"],
                payload["io"]["wchar"],
                payload["io"]["syscr"],
                payload["io"]["syscw"],
                payload["io"]["read_bytes"],
                payload["io"]["write_bytes"],
                payload["io"]["cancelled_write_bytes"]
            )
        )
        await db.commit()

    @staticmethod
    async def query_io_data(db: "aiosqlite.Connection", data_dir: str) -> list[dict]:
        sql = f"""
            SELECT
                timestamp,
                rchar,
                wchar,
                syscr,
                syscw,
                read_bytes,
                write_bytes
            FROM {Cubicle.__mem_data_table}
            WHERE data_dir = ?
            ORDER BY timestamp ASC
        """
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, (data_dir,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]





if __name__ == '__main__':
    pass
