#    ____      _     _      _
#   / ___|   _| |__ (_) ___| | ___
#  | |  | | | | '_ \| |/ __| |/ _ \
#  | |__| |_| | |_) | | (__| |  __/
#   \____\__,_|_.__/|_|\___|_|\___|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import typing
import asyncio
import aiosqlite


class Cubicle(object):
    """
    内存数据数据库操作类，提供异步持久化能力。
    """

    mem_data_table = "mem_data"
    gfx_data_table = "gfx_data"

    @staticmethod
    async def find_data(db: "aiosqlite.Connection", sql: str) -> typing.Any:
        async with db.execute(sql) as cursor:
            return await cursor.fetchall()

    @staticmethod
    async def create_mem_table(db: "aiosqlite.Connection") -> None:
        """
        创建内存采样数据表，如果表不存在则自动创建。
        """
        await db.execute(f'''CREATE TABLE IF NOT EXISTS {Cubicle.mem_data_table} (
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
    async def insert_mem_data(
            db: "aiosqlite.Connection",
            data_dir: str,
            label: str,
            remark_map: dict,
            resume_map: dict,
            memory_map: dict,
            vmrss: dict
    ) -> None:
        """
        将一轮内存采样结果写入数据库。
        """
        await db.execute(f'''INSERT INTO {Cubicle.mem_data_table} (
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
    async def query_mem_data(db: "aiosqlite.Connection", data_dir: str) -> tuple[list, list]:
        """
        查询指定数据目录（轮次）下的前台与后台内存采样数据。
        """
        fg_sql = f"""
        SELECT
            timestamp, rss, pss, uss, opss, activity, adj, foreground
        FROM {Cubicle.mem_data_table}
        WHERE foreground = '前台' and data_dir = '{data_dir}' and pss != ''
        """

        bg_sql = f"""
        SELECT
            timestamp, rss, pss, uss, opss, activity, adj, foreground
        FROM {Cubicle.mem_data_table}
        WHERE foreground = '后台' and data_dir = '{data_dir}' and pss != ''
        """

        fg_list, bg_list =  await asyncio.gather(
            Cubicle.find_data(db, fg_sql), Cubicle.find_data(db, bg_sql)
        )

        return fg_list, bg_list

    @staticmethod
    async def create_gfx_table(db: "aiosqlite.Connection") -> None:
        await db.execute(f'''CREATE TABLE IF NOT EXISTS {Cubicle.gfx_data_table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_dir TEXT,
            label TEXT,
            timestamp INTEGER,
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
            gfx_info: dict
    ) -> None:

        await db.execute(f'''INSERT INTO {Cubicle.gfx_data_table} (
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
                gfx_info["raw_frames"],
                gfx_info["vsync_sys"],
                gfx_info["vsync_app"],
                gfx_info["roll_ranges"],
                gfx_info["drag_ranges"],
                gfx_info["jank_ranges"]
            )
        )
        await db.commit()

    @staticmethod
    async def query_gfx_data(db: "aiosqlite.Connection", data_dir: str) -> tuple[list]:
        sql = f"""
        SELECT
            raw_frames, vsync_sys, vsync_app, roll_ranges, drag_ranges, jank_ranges
        FROM {Cubicle.gfx_data_table}
        WHERE data_dir = '{data_dir}'
        """
        return await Cubicle.find_data(db, sql)

if __name__ == '__main__':
    pass
