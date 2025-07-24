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

    @staticmethod
    async def initialize_tables(
            db: "aiosqlite.Connection",
            data_dir: str,
            title: str,
            timestamp: str,
    ) -> typing.Any:

        await asyncio.gather(
            Cubicle.__create_joint_table(db), Cubicle.__create_mem_table(db), Cubicle.__create_gfx_table(db)
        )
        return await Cubicle.insert_joint_data(db, data_dir, title, timestamp)

    @staticmethod
    async def __create_joint_table(db: "aiosqlite.Connection") -> typing.Any:
        await db.execute(f'''CREATE TABLE IF NOT EXISTS {Cubicle.__joint_table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_dir TEXT,
            title TEXT,
            timestamp TEXT)''')
        await db.commit()

    @staticmethod
    async def insert_joint_data(
            db: "aiosqlite.Connection",
            data_dir,
            title,
            timestamp
    ):
        await db.execute(f'''INSERT INTO {Cubicle.__joint_table} (
            data_dir,
            title,
            timestamp) VALUES (?, ?, ?)''', (
                data_dir,
                title,
                timestamp
            )
        )
        await db.commit()

    @staticmethod
    async def query_joint_data(db: "aiosqlite.Connection", data_dir: str) -> list[tuple]:
        sql = f"""
            SELECT title, timestamp
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
            java_heap REAL,
            graphics REAL,
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
            unknown REAL,
            rchar INTEGER,
            wchar INTEGER,
            syscr INTEGER,
            syscw INTEGER,
            read_bytes INTEGER,
            write_bytes INTEGER,
            cancelled_write_bytes INTEGER)''')
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
            java_heap,
            graphics,
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
            unknown,
            rchar,
            wchar,
            syscr,
            syscw,
            read_bytes,
            write_bytes,
            cancelled_write_bytes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                data_dir,
                label,

                payload["mark"]["tms"],
                payload["mark"]["pid"],
                payload["mark"]["adj"],
                payload["mark"]["act"],
                payload["mark"]["mode"],

                payload["mem"]["Java Heap"],
                payload["mem"]["Graphics"],
                payload["mem"]["TOTAL PSS"],
                payload["mem"]["TOTAL RSS"],
                payload["mem"]["TOTAL USS"],
                payload["mem"]["TOTAL SWAP"],

                payload["mem"]["Native Heap"],
                payload["mem"]["Dalvik Heap"],
                payload["mem"]["Dalvik Other"],
                payload["mem"]["Stack"],
                payload["mem"]["Ashmem"],
                payload["mem"]["Other dev"],
                payload["mem"][".so mmap"],
                payload["mem"][".jar mmap"],
                payload["mem"][".apk mmap"],
                payload["mem"][".ttf mmap"],
                payload["mem"][".dex mmap"],
                payload["mem"][".oat mmap"],
                payload["mem"][".art mmap"],
                payload["mem"]["Other mmap"],
                payload["mem"]["GL mtrack"],
                payload["mem"]["Unknown"],

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
    async def query_mem_data(db: "aiosqlite.Connection", data_dir: str) -> list[dict]:
        sql = f"""
            SELECT
                timestamp,
                pss,
                rss,
                uss,
                activity,
                adj,
                mode,
                native_heap,
                dalvik_heap,
                java_heap,
                graphics,
                rchar,
                wchar,
                syscr,
                syscw,
                read_bytes,
                write_bytes
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
            raw_frames,
            vsync_sys,
            vsync_app,
            roll_ranges,
            drag_ranges,
            jank_ranges) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                data_dir,
                label,
                timestamp,
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
                    "raw_frames": json.loads(rf),
                    "vsync_sys": json.loads(vs),
                    "vsync_app": json.loads(va),
                    "roll_ranges": json.loads(rr),
                    "drag_ranges": json.loads(dr),
                    "jank_ranges": json.loads(jr),
                }
                for rf, vs, va, rr, dr, jr in rows
            ]


if __name__ == '__main__':
    pass
