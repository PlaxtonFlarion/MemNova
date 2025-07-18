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
    __ion_data_table = "ion_data"

    @staticmethod
    async def create_tables(db: "aiosqlite.Connection") -> None:
        await asyncio.gather(
            Cubicle.__create_joint_table(db),
            Cubicle.__create_mem_table(db),
            Cubicle.__create_gfx_table(db),
            Cubicle.__create_ion_table(db)
        )

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
            uid INTEGER,
            adj INTEGER,
            activity TEXT,
            mode TEXT,
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
    async def insert_mem_data(
            db: "aiosqlite.Connection",
            data_dir: str,
            label: str,
            remark_map: dict,
            resume_map: dict,
            memory_map: dict,
            vmrss: dict
    ) -> None:

        await db.execute(f'''INSERT INTO {Cubicle.__mem_data_table} (
            data_dir,
            label,
            timestamp,
            pid,
            uid,
            adj,
            activity,
            mode,
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
                remark_map["mode"],

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
    async def query_mem_data(db: "aiosqlite.Connection", data_dir: str) -> list[tuple]:
        sql = f"""
            SELECT timestamp, rss, pss, uss, opss, activity, adj, mode
            FROM {Cubicle.__mem_data_table}
            WHERE data_dir = ? AND pss != ''
            ORDER BY timestamp ASC
        """
        async with db.execute(sql, (data_dir,)) as cursor:
            return await cursor.fetchall()

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

    # Notes: ======================== I/O ========================

    @staticmethod
    async def __create_ion_table(db: "aiosqlite.Connection") -> None:
        await db.execute(f'''CREATE TABLE IF NOT EXISTS {Cubicle.__ion_data_table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_dir TEXT,
            label TEXT,
            timestamp TEXT,
            io TEXT,
            rss TEXT,
            block TEXT)''')
        await db.commit()

    @staticmethod
    async def insert_ion_data(
            db: "aiosqlite.Connection",
            data_dir: str,
            label: str,
            timestamp: str,
            payload: dict
    ) -> None:

        await db.execute(f'''INSERT INTO {Cubicle.__ion_data_table} (
            data_dir,
            label,
            timestamp,
            io,
            rss,
            block) VALUES (?, ?, ?, ?, ?, ?)''', (
                data_dir,
                label,
                timestamp,
                payload["io"],
                payload["rss"],
                payload["block"]
            )
        )
        await db.commit()

    @staticmethod
    async def query_ion_data(db: "aiosqlite.Connection", data_dir: str) -> list[dict]:
        sql = f"""
            SELECT
                io,
                rss,
                block
            FROM {Cubicle.__ion_data_table}
            WHERE data_dir = ?
        """
        async with db.execute(sql, (data_dir,)) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "io": json.loads(io),
                    "rss": json.loads(rss),
                    "block": json.loads(block),
                }
                for io, rss, block in rows
            ]

if __name__ == '__main__':
    pass
