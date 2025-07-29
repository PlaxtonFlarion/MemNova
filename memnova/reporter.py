#   ____                       _
#  |  _ \ ___ _ __   ___  _ __| |_ ___ _ __
#  | |_) / _ \ '_ \ / _ \| '__| __/ _ \ '__|
#  |  _ <  __/ |_) | (_) | |  | ||  __/ |
#  |_| \_\___| .__/ \___/|_|   \__\___|_|
#            |_|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import os
import time
import random
import string
import typing
import asyncio
import aiofiles
import aiosqlite
import numpy as np
import pandas as pd
from pathlib import Path
from loguru import logger
from functools import partial
from bokeh.plotting import save
from bokeh.models import Spacer
from bokeh.io import output_file
from bokeh.layouts import column
from jinja2 import (
    Environment, FileSystemLoader
)
from concurrent.futures import ProcessPoolExecutor
from engine.tinker import Period
from memcore.cubicle import Cubicle
from memcore.profile import Align
from memnova.painter import Painter
from memnova.scores import Scores
from memnova.templater import Templater
from memnova import const


class Reporter(object):

    def __init__(self, src_total_place: str, nodes: str, classify_type: str, align: "Align"):
        self.total_dir = os.path.join(src_total_place, const.TOTAL_DIR)
        self.before_time = time.time()

        self.align = align

        nodes = nodes or time.strftime("%Y%m%d%H%M%S", time.localtime(self.before_time))

        self.group_dir = os.path.join(self.total_dir, const.TREE_DIR, f"{nodes}_{classify_type}")
        if not (group_dir := Path(self.group_dir)).exists():
            group_dir.mkdir(parents=True, exist_ok=True)

        self.db_file = os.path.join(self.total_dir, const.DB_FILE)
        self.log_file = os.path.join(self.group_dir, f"{const.APP_NAME}_log_{nodes}.log")
        self.team_file = os.path.join(self.group_dir, f"{const.APP_NAME}_team_{nodes}.yaml")

        logger.add(self.log_file, level=const.NOTE_LEVEL, format=const.WRITE_FORMAT)

        self.background_tasks: list = []

    @staticmethod
    async def make_report(template: str, destination: str, *args, **kwargs) -> str:
        template_dir, template_file = os.path.dirname(template), os.path.basename(template)
        loader = FileSystemLoader(template_dir)
        environment = Environment(loader=loader)
        template = environment.get_template(template_file)
        html = template.render(*args, **kwargs)

        salt: typing.Callable[[], str] = lambda: "".join(
            random.choices(string.ascii_uppercase + string.digits, k=5)
        )
        html_file = os.path.join(destination, f"{const.APP_DESC}_Inform_{salt()}.html")

        async with aiofiles.open(html_file, "w", encoding=const.CHARSET) as f:
            await f.write(html)
            logger.info(html_file)

        return html_file

    async def begin_render(self, team_data: dict) -> tuple:
        cur_time = team_data.get(
            "time", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.before_time))
        )

        cur_mark = (list(mark.values()) if isinstance(
            mark, dict
        ) else None) if (mark := team_data.get("mark")) else None

        cur_data = team_data["file"]

        return cur_time, cur_mark, cur_data

    async def final_render(self, memories: dict, start_time: float) -> None:
        memories.update({"MSG": f"Wait background tasks"})
        await asyncio.gather(*self.background_tasks)
        memories.update({"TMS": f"{time.time() - start_time:.1f} s"})

    # Workflow: ======================== MEM & I/O ========================

    @staticmethod
    def __mean_of_field(compilation: list[dict], group: str, field: str) -> typing.Optional[float]:
        vals = [
            float(c[group][field]) for c in compilation
            if group in c and c[group] not in (None, "", "nan")
        ]
        return round(float(np.mean(vals)), 2) if vals else None

    async def __mem_rendering(
        self,
        db: "aiosqlite.Connection",
        loop: "asyncio.AbstractEventLoop",
        executor: "ProcessPoolExecutor",
        templater: "Templater",
        memories: dict,
        start_time: float,
        data_dir: str,
        baseline: bool,
    ) -> typing.Optional[dict]:

        # 🟡 ==== 数据查询 ====
        os.makedirs(
            group := os.path.join(templater.download, const.SUMMARY, data_dir), exist_ok=True
        )

        mem_data, (joint, *_) = await asyncio.gather(
            Cubicle.query_mem_data(db, data_dir), Cubicle.query_joint_data(db, data_dir)
        )
        if not mem_data:
            return logger.info(f"MEM data not found for {data_dir}")
        title, timestamp, *_ = joint

        df = pd.DataFrame(mem_data)

        head = f"{title}_{Period.compress_time(timestamp)}" if title else data_dir
        trace_loc = None
        leak_loc = None
        gfx_loc = None
        io_loc = Path(group) / f"{head}_io.png"

        # 🔵 ==== I/O 绘图 ====
        draw_io_future = loop.run_in_executor(
            executor, Painter.draw_io_metrics, mem_data, str(io_loc)
        )
        self.background_tasks.append(draw_io_future)

        # 🟡 ==== 内存基线 ====
        if baseline:
            evaluate, tag_lines, group_stats = [], [], (
                df.groupby("mode")["pss"].agg(avg_pss="mean", max_pss="max", count="count")
                .reindex(["FG", "BG"]).reset_index().dropna(subset=["mode"])
            )

            # 🟡 ==== 分组统计 ====
            score_group = {}
            for _, row in group_stats.iterrows():
                part_df = df[df["mode"] == (mode := row["mode"])]
                score = Scores.analyze_mem_score(part_df, column="pss")
                logger.info(f"{mode}-Score: {score}")

                # 🟡 ==== 数据校验 ====
                if not row["count"] or pd.isna(row["avg_pss"]):
                    continue
                score_group[mode] = score

                trend = score["trend"]
                style = "expiry-fail" if trend.lower().startwith("up") else "baseline"

                # 🟡 ==== 评价部分 ====
                evaluate += [
                    {
                        "fields": [
                            {"text": f"{mode}: {trend}", "class": style},
                            {"text": f"{mode} Jitter: {score['jitter_index']:.2f}", "class": "baseline"}
                        ]
                    }
                ]

                # 🟡 ==== 指标部分 ====
                tag_lines += [
                    {
                        "fields": [
                            {"label": f"{mode}-MAX: ", "value": f"{score['max']:.2f}", "unit": "MB"},
                            {"label": f"{mode}-AVG: ", "value": f"{score['avg']:.2f}", "unit": "MB"}
                        ]
                    }
                ]

        # 🟡 ==== 内存泄漏 ====
        else:
            leak_loc = Path(group) / f"{head}_leak.png"

            # 🟨 ==== MEM 评分 ====
            score = Scores.analyze_mem_score(df, column="pss")
            logger.info(f"Score: {score}")
            score_group = {"MEM": score}

            # 🟡 ==== MEM 绘图 ====
            paint_func = partial(Painter.draw_mem_metrics, **score)
            draw_leak_future = loop.run_in_executor(
                executor, paint_func, mem_data, str(leak_loc)
            )
            self.background_tasks.append(draw_leak_future)

            trend = score["trend"]
            style = "expiry-fail" if trend.lower().startwith("up") else "leak"

            # 🟡 ==== 评价部分 ====
            evaluate = [
                {
                    "fields": [
                        {"text": trend, "class": style},
                        {"text": score['poly_trend'], "class": "leak"},
                        {"text": f"Score: {score['trend_score']:.2f}", "class": "leak"}
                    ]
                },
                {
                    "fields": [
                        {"text": f"Jitter: {score['jitter_index']:.2f}", "class": "leak"},
                        {"text": f"Slope: {score['slope']:.2f}", "class": "leak"},
                        {"text": f"R²: {score['r_squared']:.2f}", "class": "leak"}
                    ]
                }
            ]

            # 🟡 ==== 指标部分 ====
            tag_lines = [
                {
                    "fields": [
                        {"label": "MAX: ", "value": f"{score['max']:.2f}", "unit": "MB"},
                        {"label": "AVG: ", "value": f"{score['avg']:.2f}", "unit": "MB"}
                    ]
                }
            ]

        # 🟡 ==== MEM 渲染 ====
        plot = await templater.plot_mem_analysis(df)
        output_file(output_path := os.path.join(group, f"{data_dir}.html"))
        viewer_div = templater.generate_viewers(trace_loc, leak_loc, gfx_loc, io_loc)
        save(column(viewer_div, Spacer(height=10), plot, sizing_mode="stretch_both"))

        # 🟡 ==== MEM 进度 ====
        memories.update({
            "MSG": (msg := f"{data_dir} Handler Done ..."),
            "CUR": memories.get("CUR", 0) + 1,
            "TMS": f"{time.time() - start_time:.1f} s",
        })
        logger.info(msg)

        return {
            **score_group,
            "subtitle": {
                "text": title or data_dir,
                "link": str(Path(const.SUMMARY) / data_dir / Path(output_path).name)
            },
            "evaluate": evaluate,
            "tags": tag_lines
        }

    async def mem_rendition(
        self,
        db: "aiosqlite.Connection",
        loop: "asyncio.events.AbstractEventLoop",
        executor: "ProcessPoolExecutor",
        templater: "Templater",
        memories: dict,
        start_time: float,
        team_data: dict,
        baseline: bool,
        *_
    ) -> dict:

        cur_time, cur_mark, cur_data = await self.begin_render(team_data)

        compilation = await asyncio.gather(
            *(self.__mem_rendering(db, loop, executor, templater, memories, start_time, d, baseline)
              for d in cur_data)
        )
        if not (compilation := [c for c in compilation if c]):
            return {}

        major_summary_items = [
            {"title": "基础信息", "class": "general", "value": cur_mark}
        ] if cur_mark else []
        minor_summary_items = []

        # 🟡 ==== 内存基线 ====
        if baseline:
            headline = self.align.get_headline("mem", "base")

            key_tuples = [
                ("FG-MAX", "FG", "max"), ("FG-AVG", "FG", "avg"), ("BG-MAX", "BG", "max"), ("BG-AVG", "BG", "avg")
            ]

            grouped = {k: self.__mean_of_field(compilation, group, field) for k, group, field in key_tuples}
            fg = {k: grouped[k] for k in ["FG-MAX", "FG-AVG"]}
            bg = {k: grouped[k] for k in ["BG-MAX", "BG-AVG"]}

            # 🟡 ==== 主要容器 ====
            assemble = [
                f"{k} HIGH" for k, v in grouped.items()
                if v and (
                    standard := self.align.get_standard("mem", k.lower())
                ) is not None and v > standard
            ]
            if assemble:
                major_summary_items += [{"title": "特征信息", "class": "highlight", "value": assemble}]

            major_summary_items += self.align.get_sections("mem", "base")

            # 🟡 ==== 次要容器 ====
            minor_summary_items += [
                {"value": [f"MEAN-{k}: {v:.2f} MB" for k, v in fg.items() if v], "class": "fg-copy"},
                {"value": [f"MEAN-{k}: {v:.2f} MB" for k, v in bg.items() if v], "class": "bg-copy"}
            ]

        # 🟡 ==== 内存泄漏 ====
        else:
            headline = self.align.get_headline("mem", "leak")

            key_tuples = [
                ("MAX", "MEM", "max"), ("AVG", "MEM", "avg")
            ]

            grouped = {k: self.__mean_of_field(compilation, group, field) for k, group, field in key_tuples}
            union = {k: grouped[k] for k in ["MAX", "AVG"]}

            # 🟡 ==== 主要容器 ====
            major_summary_items += self.align.get_sections("mem", "leak")

            # 🟡 ==== 次要容器 ====
            minor_summary_items += [
                {"value": [f"MEAN-{k}: {v:.2f} MB" for k, v in union.items() if v]}
            ]

        await self.final_render(memories, start_time)

        return {
            "report_list": compilation,
            "title": f"{const.APP_DESC} Information",
            "time": cur_time,
            "headline": headline,
            "major_summary_items": major_summary_items,
            "minor_summary_items": minor_summary_items,
        }

    # Workflow: ======================== GFX ========================

    @staticmethod
    def __split_frames_with_ranges(
        frames: list[dict],
        roll_ranges: list[dict],
        drag_ranges: list[dict],
        jank_ranges: list[dict],
        segment_ms: int = 60000
    ) -> list[tuple]:

        frames = sorted(frames, key=lambda f: f["timestamp_ms"])
        start_ts, close_ts = frames[0]["timestamp_ms"], frames[-1]["timestamp_ms"]

        segment_list = []

        cur_start = start_ts
        while cur_start < close_ts:
            cur_end = cur_start + segment_ms
            segment_frames = [f for f in frames if cur_start <= f["timestamp_ms"] < cur_end]
            if segment_frames:
                roll_in = [
                    {**r, "start_ts": max(r["start_ts"], cur_start), "end_ts": min(r["end_ts"], cur_end)}
                    for r in roll_ranges if r["end_ts"] > cur_start and r["start_ts"] < cur_end
                ]
                drag_in = [
                    {**r, "start_ts": max(r["start_ts"], cur_start), "end_ts": min(r["end_ts"], cur_end)}
                    for r in drag_ranges if r["end_ts"] > cur_start and r["start_ts"] < cur_end
                ]
                jank_in = [
                    {**r, "start_ts": max(r["start_ts"], cur_start), "end_ts": min(r["end_ts"], cur_end)}
                    for r in jank_ranges if r["end_ts"] > cur_start and r["start_ts"] < cur_end
                ]
                segment_list.append((segment_frames, roll_in, drag_in, jank_in, cur_start, cur_end))
            cur_start = cur_end
        return segment_list

    @staticmethod
    def __merge_alignment_frames(frames: list[dict]) -> dict:
        # ==== 先提取所有 normalize ====
        normalize_list = [
            record.get("metadata", {}).get("normalize", 0) for record in frames
        ]

        # ==== 以最早的 normalize 作为基准 ====
        normalize_start_ts = min(normalize_list)

        # ==== 初始化合并结构 ====
        merged = {key: [] for key in frames[0]}

        for record in frames:
            logger.info(f"Meta: {record.get('metadata', 'Unknown')}")
            # ==== 原始帧数据 [ms] ====
            for frame in record["raw_frames"]:
                frame["timestamp_ms"] -= normalize_start_ts

            # ==== 系统FPS / 应用FPS [ms] ====
            for point in record["vsync_sys"]:
                point["ts"] -= normalize_start_ts
            for point in record["vsync_app"]:
                point["ts"] = normalize_start_ts

            # ==== 滑动区域 / 拖拽区域 / 掉帧区域 [ms] ====
            for r in record["roll_ranges"]:
                r["start_ts"] -= normalize_start_ts
                r["end_ts"] -= normalize_start_ts
            for d in record["drag_ranges"]:
                d["start_ts"] -= normalize_start_ts
                d["end_ts"] -= normalize_start_ts
            for j in record["jank_ranges"]:
                j["start_ts"] -= normalize_start_ts
                j["end_ts"] -= normalize_start_ts

            # ==== 合并数据 ====
            for key, value in record.items():
                if isinstance(value, list):
                    merged[key].extend(value)
                else:
                    merged[key].append(value)

        return merged

    async def __gfx_rendering(
        self,
        db: "aiosqlite.Connection",
        loop: "asyncio.AbstractEventLoop",
        executor: "ProcessPoolExecutor",
        templater: "Templater",
        memories: dict,
        start_time: float,
        data_dir: str,
        *_,
    ) -> typing.Optional[dict]:

        # 🟢 ==== 数据查询 ====
        os.makedirs(
            group := os.path.join(templater.download, const.SUMMARY, data_dir), exist_ok=True
        )

        gfx_data, (joint, *_) = await asyncio.gather(
            Cubicle.query_gfx_data(db, data_dir), Cubicle.query_joint_data(db, data_dir)
        )
        if not gfx_data:
            return logger.info(f"GFX data not found for {data_dir}")
        title, timestamp, *_ = joint

        frame_merged = self.__merge_alignment_frames(gfx_data)
        _, raw_frames, vsync_sys, vsync_app, roll_ranges, drag_ranges, jank_ranges = frame_merged.values()

        head = f"{title}_{Period.compress_time(timestamp)}" if title else data_dir
        trace_loc = Path(templater.download).parent / const.TRACES_DIR / data_dir
        leak_loc = None
        gfx_loc = Path(group) / f"{head}_gfx.png"
        io_loc = None

        # 🟩 ==== GFX 评分 ====
        score = Scores.analyze_gfx_score(raw_frames, roll_ranges, drag_ranges, jank_ranges, fps_key="fps_app")
        logger.info(f"Score: {score}")
        score_group = {"GFX": score}

        # 🟢 ==== GFX 绘图 ====
        paint_func = partial(Painter.draw_gfx_metrics, **score)
        draw_future = loop.run_in_executor(
            executor, paint_func,
            raw_frames, vsync_sys, vsync_app, roll_ranges, drag_ranges, jank_ranges, str(gfx_loc)
        )
        self.background_tasks.append(draw_future)

        roll_avg_fps = score["roll_avg_fps"]
        is_scroll = f"Roll FPS: {roll_avg_fps:.2f} FPS" if roll_avg_fps else score["level"]

        standard_std = self.align.get_standard("gfx", "std-fps")
        std_class = "fluency" if standard_std and score["fps_std"] <= standard_std else "expiry-fail"
        standard_jnk = self.align.get_standard("gfx", "jnk")
        jnk_class = "fluency" if standard_jnk and score["jank_ratio"] <= standard_jnk else "expiry-fail"

        # 🟢 ==== 评价部分 ====
        evaluate = [
            {
                "fields": [
                    {"text": f"STD: {score['fps_std']:.2f}", "class": std_class},
                    {"text": f"JNK: {score['jank_ratio']:.2f} %", "class": jnk_class},
                    {"text": f"Score: {score['score'] * 100:.2f}", "class": "fluency"}
                ]
            },
            {
                "fields": [
                    {"text": is_scroll, "class": "fluency"},
                    {"text": f"Low-FPS MAX: {score['longest_low_fps']} s", "class": "fluency"},
                    {"text": f"Hi-Lat: {score['high_latency_ratio']:.2f} %", "class": "fluency"}
                ]
            }
        ]

        # 🟢 ==== 指标部分 ====
        tag_lines = [
            {
                "fields": [
                    {"label": "MIN: ", "value": f"{score['min_fps']:.2f}", "unit": "FPS"},
                    {"label": "AVG: ", "value": f"{score['avg_fps']:.2f}", "unit": "FPS"}
                ]
            }
        ]

        # 🟢 ==== 分段切割 ====
        segments = self.__split_frames_with_ranges(raw_frames, roll_ranges, drag_ranges, jank_ranges)

        # 🟢 ==== GFX 渲染 ====
        plots = await asyncio.gather(
            *(templater.plot_gfx_analysis(segment, roll, drag, jank)
              for segment, roll, drag, jank, *_ in segments)
        )
        output_file(output_path := os.path.join(group, f"{data_dir}.html"))
        viewer_div = templater.generate_viewers(trace_loc, leak_loc, gfx_loc, io_loc)
        save(column(viewer_div, *plots, Spacer(height=10), sizing_mode="stretch_width"))

        # 🟢 ==== GFX 进度 ====
        memories.update({
            "MSG": (msg := f"{data_dir} Handler Done ..."),
            "CUR": memories.get("CUR", 0) + 1,
            "TMS": f"{time.time() - start_time:.1f} s",
        })
        logger.info(msg)

        return {
            **score_group,
            "subtitle": {
                "text": title or data_dir,
                "link": str(Path(const.SUMMARY) / data_dir / Path(output_path).name),
            },
            "evaluate": evaluate,
            "tags": tag_lines
        }

    async def gfx_rendition(
        self,
        db: "aiosqlite.Connection",
        loop: "asyncio.events.AbstractEventLoop",
        executor: "ProcessPoolExecutor",
        templater: "Templater",
        memories: dict,
        start_time: float,
        team_data: dict,
        *_
    ) -> typing.Optional[dict]:

        cur_time, cur_mark, cur_data = await self.begin_render(team_data)

        compilation = await asyncio.gather(
            *(self.__gfx_rendering(db, loop, executor, templater, memories, start_time, d)
              for d in cur_data)
        )
        if not (compilation := [c for c in compilation if c]):
            return {}

        headline = self.align.get_headline("gfx", "base")

        key_tuples = [
            ("MIN", "GFX", "min_fps"), ("AVG", "GFX", "avg_fps")
        ]

        grouped = {k: self.__mean_of_field(compilation, group, field) for k, group, field in key_tuples}
        union = {k: grouped[k] for k in ["MIN", "AVG"]}

        major_summary_items = [
            {"title": "基础信息", "class": "general", "value": cur_mark}
        ] if cur_mark else []
        minor_summary_items = []

        major_summary_items += self.align.get_sections("gfx", "base")
        minor_summary_items += [
            {"value": [f"MEAN-{k}: {v:.2f} FPS" for k, v in union.items() if v]}
        ]

        await self.final_render(memories, start_time)

        return {
            "report_list": compilation,
            "title": f"{const.APP_DESC} Information",
            "time": cur_time,
            "headline": headline,
            "major_summary_items": major_summary_items,
            "minor_summary_items": minor_summary_items
        }


if __name__ == '__main__':
    pass
