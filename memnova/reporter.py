#  ____                       _
# |  _ \ ___ _ __   ___  _ __| |_ ___ _ __
# | |_) / _ \ '_ \ / _ \| '__| __/ _ \ '__|
# |  _ <  __/ |_) | (_) | |  | ||  __/ |
# |_| \_\___| .__/ \___/|_|   \__\___|_|
#           |_|
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
from memnova.lumix import Lumix
from memnova.orbis import Orbis
from memnova.templater import Templater
from memnova import const


class Reporter(object):
    """Reporter"""

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
        self.assemblage = os.path.join(self.group_dir, f"Report_{Path(self.group_dir).name}")

        logger.add(self.log_file, level=const.NOTE_LEVEL, format=const.WRITE_FORMAT)

        self.background_tasks: list = []

    async def make_report(self, template: str, *args, **kwargs) -> str:
        template_dir, template_file = os.path.dirname(template), os.path.basename(template)
        loader = FileSystemLoader(template_dir)
        environment = Environment(loader=loader)
        template = environment.get_template(template_file)
        html = template.render(*args, **kwargs)

        salt: typing.Callable[[], str] = lambda: "".join(
            random.choices(string.ascii_uppercase + string.digits, k=5)
        )
        html_file = os.path.join(self.assemblage, f"{const.APP_DESC}_Inform_{salt()}.html")

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

    async def final_render(self, memories: dict) -> None:
        memories.update({
            "MSG": (msg := f"Wait background tasks")
        })
        logger.info(msg)
        await asyncio.gather(*self.background_tasks)
        memories.update({
            "TMS": f"{time.time() - self.before_time:.1f} s"
        })

    # Workflow: ======================== MEM / GFX ========================

    @staticmethod
    def mean_of_field(compilation: list[dict], group: str, field: str) -> typing.Optional[float]:
        vals = [
            float(c[group][field]) for c in compilation
            if group in c and c[group] not in (None, "", "nan")
        ]
        return round(float(np.mean(vals)), 2) if vals else None

    @staticmethod
    def build_minor_items(key_tuples: list, groups: list, grouped: dict) -> list:
        minor_items = []
        for group_cfg in groups:
            keys = [k for k, g, f in key_tuples if g == group_cfg["name"]]
            values = [
                f"MEAN-{k}: {grouped[k]:.2f} {group_cfg['unit']}"
                for k in keys if grouped.get(k) is not None
            ]
            if values:
                minor_items.append({"value": values, "class": group_cfg["class"]})
        return minor_items

    @staticmethod
    def score_classes(score: dict, standard: dict, d_cls: str) -> dict:
        fail_cls, invalid_cls = "expiry-fail", "expiry-none"

        op_map = {
            "le": lambda x, y: x <= y,
            "lt": lambda x, y: x < y,
            "ge": lambda x, y: x >= y,
            "gt": lambda x, y: x > y,
            "eq": lambda x, y: x == y,
            "ne": lambda x, y: x != y
        }

        calc: typing.Callable[
            [float, float], bool
        ] = lambda x, y: x is not None and y is not None and op(x, y)

        result = {k: d_cls for k in score.keys()}
        for key, cfg in standard.items():
            value = score.get(key)
            threshold, direction = cfg.get("threshold"), cfg.get("direction", "ge")
            if threshold is not None and direction is not None:
                op = op_map.get(direction, op_map["ge"])
                result[key] = invalid_cls if value is None else (d_cls if calc(value, threshold) else fail_cls)
            else:
                result[key] = d_cls
        return result

    @staticmethod
    def split_ranges(frames: list[dict], *args, **kwargs) -> list[tuple]:

        (roll_ranges, drag_ranges, jank_ranges, *_), segment_ms = args, kwargs.get("segment_ms", 60000)

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
    def merge_alignment_frames(frames: list[dict]) -> dict:
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

    @staticmethod
    def format_score(score: dict, standard: dict, classes: dict, cfg: dict, exclude: set = None) -> list:
        formatted, exclude = [], exclude or set()
        for k in standard:
            if k in exclude:
                logger.info(f"{k} is default key, skipped cfg ...")
                continue
            if k in score and k in cfg:
                field = cfg[k]
                prefix = f"{prefix}: " if (prefix := field.get("prefix", k)) else ""
                val, fmt, unit = score[k], field.get("format", "{}"), field.get("unit", "")
                factor = field.get("factor", 1)
                text_val = f"{prefix}-" if val is None else fmt.format(val * factor)
                formatted.append({
                    "text": f"{prefix}{text_val}{unit}", "class": classes.get(k, ""), **standard[k]
                })
        return formatted

    @staticmethod
    def build_evaluate(formatted: list, g_limit: int, f_limit: int, pg: list = None, sg: list = None) -> list:
        if pg:
            formatted = pg + formatted
        if sg:
            formatted = formatted + sg

        # 按 f_limit 切分
        field_groups = [formatted[i:i+f_limit] for i in range(0, len(formatted), f_limit)]
        # 保留 g_limit 组
        evaluate = [{"fields": group} for group in field_groups[:g_limit]]

        return evaluate

    # Workflow: ======================== Rendering ========================

    async def mem_rendering(
        self,
        db: "aiosqlite.Connection",
        loop: "asyncio.events.AbstractEventLoop",
        executor: "ProcessPoolExecutor",
        memories: dict,
        data_dir: str,
        baseline: bool,
    ) -> typing.Optional[dict]:

        os.makedirs(
            group := os.path.join(self.assemblage, const.SUMMARY, data_dir), exist_ok=True
        )

        # 🟡 ==== 数据查询 ====
        mem_data, io_data, (joint, *_) = await asyncio.gather(
            Cubicle.query_mem(db, data_dir), Cubicle.query_io(db, data_dir), Cubicle.query_joint(db, data_dir)
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
            executor, Lumix.draw_io_metrics, io_data, str(io_loc)
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
                score = Orbis.analyze_mem_score(part_df, column="pss")
                logger.info(f"{mode}-Score: {score}")

                # 🟡 ==== 数据校验 ====
                if not row["count"] or pd.isna(row["avg_pss"]):
                    continue
                score_group[mode] = score

                # 🟡 ==== 定制评价 ====
                standard = self.align.get_standard("mem", "base")
                classes = self.score_classes(score, standard, "baseline")

                # 🟡 ==== 趋势标签 ====
                trend = score["trend"]
                match trend[0]:
                    case "I" | "F" | "A" | "C": trend_cls = "expiry-none"
                    case "U": trend_cls = "expiry-fail"
                    case _: trend_cls = "baseline"

                td = [{
                    "text": f"{mode}: {trend}", "class": trend_cls, **standard.get("trend", {
                        "desc": "趋势判定",
                        "tooltip": "自动识别内存趋势类型（如泄漏、平稳、波动、U型等），结合斜率和拟合优度辅助泄漏判断。"
                    })
                }]

                # 🟡 ==== 评价部分 ====
                formatted = self.format_score(
                    score, standard, classes, Orbis.mem_fields_cfg(), exclude={"trend"}
                )
                evaluate += self.build_evaluate(td + formatted, 1, 3)

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
            score = Orbis.analyze_mem_score(df, column="pss")
            logger.info(f"Score: {score}")
            score_group = {"MEM": score}

            # 🟡 ==== MEM 绘图 ====
            paint_func = partial(Lumix.draw_mem_metrics, **score)
            draw_leak_future = loop.run_in_executor(
                executor, paint_func, mem_data, str(leak_loc)
            )
            self.background_tasks.append(draw_leak_future)

            # 🟡 ==== 定制评价 ====
            standard = self.align.get_standard("mem", "leak")
            classes = self.score_classes(score, standard, "leak")

            # 🟡 ==== 趋势标签 ====
            trend = score["trend"]
            match trend[0]:
                case "I" | "F" | "A" | "C": trend_cls = "expiry-none"
                case "U": trend_cls = "expiry-fail"
                case _: trend_cls = "leak"

            td = [{
                "text": trend, "class": trend_cls, **standard.get("trend", {
                    "desc": "趋势判定",
                    "tooltip": "自动识别内存趋势类型（如泄漏、平稳、波动、U型等），结合斜率和拟合优度辅助泄漏判断。"
                })
            }]

            # 🟡 ==== 评价部分 ====
            formatted = self.format_score(
                score, standard, classes, Orbis.mem_fields_cfg(), exclude={"trend"}
            )
            evaluate = self.build_evaluate(td + formatted, 2, 3)

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
        plot = await Templater.plot_mem_analysis(df)
        output_file(output_path := os.path.join(group, f"{data_dir}.html"))
        viewer_div = Templater.generate_viewers(trace_loc, leak_loc, gfx_loc, io_loc, Path(self.log_file))
        save(column(viewer_div, Spacer(height=10), plot, sizing_mode="stretch_both"))

        # 🟡 ==== MEM 进度 ====
        memories.update({
            "MSG": (msg := f"{data_dir} Handler Done ..."),
            "CUR": memories.get("CUR", 0) + 1,
            "TMS": f"{time.time() - self.before_time:.1f} s"
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

    async def gfx_rendering(
        self,
        db: "aiosqlite.Connection",
        loop: "asyncio.events.AbstractEventLoop",
        executor: "ProcessPoolExecutor",
        memories: dict,
        data_dir: str,
    ) -> typing.Optional[dict]:

        os.makedirs(
            group := os.path.join(self.assemblage, const.SUMMARY, data_dir), exist_ok=True
        )

        # 🟢 ==== 数据查询 ====
        gfx_data, (joint, *_) = await asyncio.gather(
            Cubicle.query_gfx(db, data_dir), Cubicle.query_joint(db, data_dir)
        )
        if not gfx_data:
            return logger.info(f"GFX data not found for {data_dir}")
        title, timestamp, *_ = joint

        frame_merged = self.merge_alignment_frames(gfx_data)
        _, raw_frames, vsync_sys, vsync_app, roll_ranges, drag_ranges, jank_ranges = frame_merged.values()

        head = f"{title}_{Period.compress_time(timestamp)}" if title else data_dir
        trace_loc = Path(self.assemblage).parent / const.TRACES_DIR / data_dir
        leak_loc = None
        gfx_loc = Path(group) / f"{head}_gfx.png"
        io_loc = None

        # 🟩 ==== GFX 评分 ====
        score = Orbis.analyze_gfx_score(raw_frames, roll_ranges, drag_ranges, jank_ranges, fps_key="fps_app")
        logger.info(f"Score: {score}")
        score_group = {"GFX": score}

        # 🟢 ==== GFX 绘图 ====
        paint_func = partial(Lumix.draw_gfx_metrics, **score)
        draw_future = loop.run_in_executor(
            executor, paint_func,
            raw_frames, vsync_sys, vsync_app, roll_ranges, drag_ranges, jank_ranges, str(gfx_loc)
        )
        self.background_tasks.append(draw_future)

        # 🟢 ==== 定制评价 ====
        standard = self.align.get_standard("gfx", "base")
        classes = self.score_classes(score, standard, "fluency")

        # 🟢 ==== 评价部分 ====
        formatted = self.format_score(score, standard, classes, Orbis.gfx_fields_cfg())
        evaluate = self.build_evaluate(formatted, 2, 3)

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
        segments = self.split_ranges(raw_frames, roll_ranges, drag_ranges, jank_ranges)

        # 🟢 ==== GFX 渲染 ====
        plots = await asyncio.gather(
            *(Templater.plot_gfx_analysis(segment, roll, drag, jank)
              for segment, roll, drag, jank, *_ in segments)
        )
        output_file(output_path := os.path.join(group, f"{data_dir}.html"))
        viewer_div = Templater.generate_viewers(trace_loc, leak_loc, gfx_loc, io_loc, Path(self.log_file))
        save(column(viewer_div, *plots, Spacer(height=10), sizing_mode="stretch_width"))

        # 🟢 ==== GFX 进度 ====
        memories.update({
            "MSG": (msg := f"{data_dir} Handler Done ..."),
            "CUR": memories.get("CUR", 0) + 1,
            "TMS": f"{time.time() - self.before_time:.1f} s"
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

    # Workflow: ======================== Rendition ========================

    async def mem_rendition(
        self,
        db: "aiosqlite.Connection",
        loop: "asyncio.events.AbstractEventLoop",
        executor: "ProcessPoolExecutor",
        memories: dict,
        team_data: dict,
        baseline: bool,
        *_,
        **__
    ) -> dict:

        cur_time, cur_mark, cur_data = await self.begin_render(team_data)

        compilation = await asyncio.gather(
            *(self.mem_rendering(db, loop, executor, memories, d, baseline)
              for d in cur_data)
        )
        if not (compilation := [c for c in compilation if c]):
            return {}

        # 🟡 ==== 定义容器 ====
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
            groups = [
                {"name": "FG", "unit": "MB", "class": "fg-copy"},
                {"name": "BG", "unit": "MB", "class": "bg-copy"}
            ]
            grouped = {
                k: self.mean_of_field(compilation, group, field) for k, group, field in key_tuples
            }
            sync_layout = {k.lower(): v for k, v in grouped.items() if v is not None}

            # 🟡 ==== 定制评价 ====
            standard = self.align.get_standard("mem", "base")
            classes = self.score_classes(sync_layout, standard, "expiry-pass")

            # 🟡 ==== 主要容器 ====
            assemble = [
                f"{k.upper()} HIGH" for k, v in sync_layout.items() if classes.get(k) == "expiry-fail"
            ]
            if assemble:
                major_summary_items += [{"title": "特征信息", "class": "highlight", "value": assemble}]
            major_summary_items += self.align.get_sections("mem", "base")

            # 🟡 ==== 次要容器 ====
            minor_summary_items += self.build_minor_items(key_tuples, groups, grouped)

        # 🟡 ==== 内存泄漏 ====
        else:
            headline = self.align.get_headline("mem", "leak")

            key_tuples = [
                ("MAX", "MEM", "max"), ("AVG", "MEM", "avg")
            ]
            groups = [
                {"name": "MEM", "unit": "MB", "class": None}
            ]
            grouped = {
                k: self.mean_of_field(compilation, group, field) for k, group, field in key_tuples
            }

            # 🟡 ==== 主要容器 ====
            major_summary_items += self.align.get_sections("mem", "leak")

            # 🟡 ==== 次要容器 ====
            minor_summary_items += self.build_minor_items(key_tuples, groups, grouped)

        await self.final_render(memories)

        return {
            "report_list": compilation,
            "title": f"{const.APP_DESC} Information",
            "time": cur_time,
            "headline": headline,
            "major_summary_items": major_summary_items,
            "minor_summary_items": minor_summary_items
        }

    async def gfx_rendition(
        self,
        db: "aiosqlite.Connection",
        loop: "asyncio.events.AbstractEventLoop",
        executor: "ProcessPoolExecutor",
        memories: dict,
        team_data: dict,
        *_,
        **__
    ) -> typing.Optional[dict]:

        cur_time, cur_mark, cur_data = await self.begin_render(team_data)

        compilation = await asyncio.gather(
            *(self.gfx_rendering(db, loop, executor, memories, d)
              for d in cur_data)
        )
        if not (compilation := [c for c in compilation if c]):
            return {}

        headline = self.align.get_headline("gfx", "base")

        key_tuples = [
            ("MIN", "GFX", "min_fps"), ("AVG", "GFX", "avg_fps")
        ]
        groups = [
            {"name": "GFX", "unit": "FPS", "class": None}
        ]
        grouped = {
            k: self.mean_of_field(compilation, group, field) for k, group, field in key_tuples
        }

        # 🟢 ==== 定义容器 ====
        major_summary_items = [
            {"title": "基础信息", "class": "general", "value": cur_mark}
        ] if cur_mark else []
        minor_summary_items = []

        # 🟢 ==== 主要容器 ====
        major_summary_items += self.align.get_sections("gfx", "base")

        # 🟢 ==== 次要容器 ====
        minor_summary_items += self.build_minor_items(key_tuples, groups, grouped)

        await self.final_render(memories)

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
