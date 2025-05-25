#    ____      _     _      _
#   / ___|   _| |__ (_) ___| | ___
#  | |  | | | | '_ \| |/ __| |/ _ \
#  | |__| |_| | |_) | | (__| |  __/
#   \____\__,_|_.__/|_|\___|_|\___|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import asyncio
import aiosqlite


class DataBase(object):
    """
    内存数据数据库操作类，提供异步持久化能力。

    基于 aiosqlite 提供的异步接口，实现数据表创建、内存数据插入与采集结果查询。
    所有操作基于统一结构的 memory_data 表，支持前后台筛选与图表构建数据输出。
    """

    @staticmethod
    async def create_table(db: "aiosqlite.Connection") -> None:
        """
        创建内存采样数据表，如果表不存在则自动创建。

        表结构涵盖基础信息（时间戳、PID、UID）、前后台状态、内存汇总值与详细内存段字段，
        可用于图表展示、报告分析与任务回溯。

        Parameters
        ----------
        db : aiosqlite.Connection
            异步 SQLite 数据库连接对象。
        """

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
    ) -> None:
        """
        将一轮内存采样结果写入数据库。

        参数由 `Ram` 对象构建而成，拆解为 remark（基础）、resume（汇总）、
        memory（明细）和 vmrss（估值）四部分。

        Parameters
        ----------
        db : aiosqlite.Connection
            异步 SQLite 数据库连接对象。

        data_dir : str
            当前任务的目录标识（轮次标记）。

        label : str
            当前测试任务的标签名称。

        remark_map : dict
            应用运行状态数据，如时间戳、PID、UID、Activity、是否前台等。

        resume_map : dict
            汇总内存数据，如 PSS、USS、RSS、SWAP、Graphics 等。

        memory_map : dict
            详细内存段数据，如 Native Heap、.dex、.so、Stack 等。

        vmrss : dict
            虚拟内存估值，如 VmRSS。
        """
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
        """
        查询指定数据目录（轮次）下的前台与后台内存采样数据。

        输出结果格式为用于图表展示的有序列表，按时间排序，字段结构如下：
        (timestamp, rss, pss, uss, opss, activity, adj, foreground)

        Parameters
        ----------
        db : aiosqlite.Connection
            异步 SQLite 数据库连接对象。

        data_dir : str
            数据采样轮次标识（对应插入时的 data_dir 字段）。

        Returns
        -------
        tuple[list, list]
            两个列表分别为：
            - 前台数据列表（foreground = '前台'）
            - 后台数据列表（foreground = '后台'）
        """

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
