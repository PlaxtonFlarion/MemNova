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
from bokeh.plotting import save
from bokeh.models import Spacer
from bokeh.io import output_file
from bokeh.layouts import column
from jinja2 import (
    Environment, FileSystemLoader
)
from engine.tinker import Period
from memcore.cubicle import Cubicle
from memcore.design import Design
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

        self.background_tasks: list["asyncio.Task"] = []

    @staticmethod
    async def make_report(template: str, destination: str, *args, **kwargs) -> None:
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

        Design.build_file_tree(html_file)

    # Workflow: ======================== MEM & I/O ========================

    @staticmethod
    def __mean_of_field(compilation: list[dict], keys: list[str]) -> typing.Optional[float]:
        for key in keys:
            # 提取所有 compilation 里的 fields 并找 label 以 key 结尾的值
            vals = [
                float(field["value"])
                for item in compilation if "tags" in item for tag in item["tags"] for field in tag["fields"]
                if field["label"].endswith(f"{key}: ") and field.get("value") not in (None, "", "nan")
            ]
            # 计算均值
            if vals:
                return round(float(np.mean(vals)), 2)
        return None

    async def __classify_rendering(
            self,
            db: "aiosqlite.Connection",
            templater: "Templater",
            data_dir: str,
            baseline: bool,
    ) -> dict:

        os.makedirs(
            group := os.path.join(templater.download, const.SUMMARY, data_dir), exist_ok=True
        )

        union_data_list, (joint, *_) = await asyncio.gather(
            Cubicle.query_mem_data(db, data_dir), Cubicle.query_joint_data(db, data_dir)
        )
        metadata, (title, timestamp) = {}, joint

        io_data, *_ = await Cubicle.query_io_data(db, data_dir)
        io, rss, block = io_data.values()

        head = f"{title}_{Period.compress_time(timestamp)}" if title else data_dir
        ionic_loc = Path(group) / f"{head}_ionic.png"

        df = pd.DataFrame(
            union_data_list,
            columns=["timestamp", "rss", "pss", "uss", "opss", "activity", "adj", "mode"]
        )

        ionic_task = asyncio.create_task(
            Painter.draw_io_metrics(metadata, io, rss, block, str(ionic_loc)), name="draw io metrics"
        )
        self.background_tasks.append(ionic_task)

        if baseline:
            image_loc = None
            group_stats = (
                df.groupby("mode")["pss"].agg(avg_pss="mean", max_pss="max", count="count")
                .reindex(["FG", "BG"]).reset_index().dropna(subset=["mode"])
            )

            gs, all_ok = group_stats.set_index("mode"), True
            if "FG" in gs.index:
                all_ok &= gs.loc["FG", "max_pss"] < self.align.fg_max
                all_ok &= gs.loc["FG", "avg_pss"] < self.align.fg_avg
            if "BG" in gs.index:
                all_ok &= gs.loc["BG", "max_pss"] < self.align.bg_max
                all_ok &= gs.loc["BG", "avg_pss"] < self.align.bg_avg

            evaluate = [
                {
                    "fields": [
                        {"text": "Pass" if all_ok else "Fail", "class": "expiry-pass" if all_ok else "expiry-fail"}
                    ]
                }
            ]

            tag_lines = [
                {
                    "fields": [
                        {"label": f"{row['mode']}-MAX: ", "value": f"{row['max_pss']:.2f}", "unit": "MB"},
                        {"label": f"{row['mode']}-AVG: ", "value": f"{row['avg_pss']:.2f}", "unit": "MB"}
                    ]
                } for _, row in group_stats.iterrows()
            ]

        else:
            image_loc = Path(group) / f"{head}_image.png"
            leak = Scores.analyze_mem_trend(df["pss"])
            evaluate = [
                {
                    "fields": [
                        {"text": f"Trend: {leak['trend']}", "class": "refer"},
                        {"text": f"Score: {leak['trend_score']}", "class": "refer"}
                    ]
                },
                {
                    "fields": [
                        {"text": f"Shake: {leak['jitter_index']}", "class": "refer"},
                        {"text": f"Slope: {leak['slope']}", "class": "refer"}
                    ]
                }
            ]

            image_task = asyncio.create_task(
                Painter.draw_mem_metrics(df, str(image_loc), **leak), name="draw mem metrics"
            )
            self.background_tasks.append(image_task)

            mem_max_pss, mem_avg_pss = df["pss"].max(), df["pss"].mean()

            tag_lines = [
                {
                    "fields": [
                        {"label": f"MEM-MAX: ", "value": f"{mem_max_pss:.2f}", "unit": "MB"},
                        {"label": f"MEM-AVG: ", "value": f"{mem_avg_pss:.2f}", "unit": "MB"}
                    ]
                }
            ]

        plot = await templater.plot_mem_analysis(df)
        output_file(output_path := os.path.join(group, f"{data_dir}.html"))

        viewer_div = templater.generate_viewers(image_loc, ionic_loc)
        save(column(viewer_div, Spacer(height=10), plot, sizing_mode="stretch_both"))
        logger.info(f"{data_dir} Handler Done ...")

        return {
            "subtitle": title or data_dir,
            "subtitle_link": str(Path(const.SUMMARY) / data_dir / Path(output_path).name),
            "evaluate": evaluate,
            "tags": tag_lines
        }

    async def mem_rendition(
            self,
            db: "aiosqlite.Connection",
            templater: "Templater",
            team_data: dict,
            baseline: bool,
            *_
    ) -> dict:

        cur_time, cur_data = team_data.get("time", "Unknown"), team_data["file"]

        compilation = await asyncio.gather(
            *(self.__classify_rendering(db, templater, d, baseline) for d in cur_data)
        )

        major_summary = [
            {"label": "测试时间", "value": [{"text": cur_time, "class": "time"}]}
        ]
        minor_summary = []

        if baseline:
            headline = self.align.base_headline
            fg = {k: self.__mean_of_field(compilation, [k]) for k in ["FG-MAX", "FG-AVG"]}
            bg = {k: self.__mean_of_field(compilation, [k]) for k in ["BG-MAX", "BG-AVG"]}
            conclusion = [
                ("FG-MAX HIGH", fg["FG-MAX"], self.align.fg_max),
                ("FG-AVG HIGH", fg["FG-AVG"], self.align.fg_avg),
                ("BG-MAX HIGH", bg["BG-MAX"], self.align.bg_max),
                ("BG-AVG HIGH", bg["BG-AVG"], self.align.bg_avg),
            ]
            high = [desc for desc, val, limit in conclusion if val and val > limit]
            expiry = {
                "text": "Fail" if high else "Pass", "class": "expiry-fail" if high else "expiry-pass"
            }

            major_summary += [
                {"label": "测试结论", "value": [expiry] + [{"text": c, "class": "highlight"} for c in high]},
                {"label": "参考标准", "value": [
                    {"text": f"FG-MAX: {self.align.fg_max:.2f} MB", "class": "max-threshold"},
                    {"text": f"FG-AVG: {self.align.fg_avg:.2f} MB", "class": "avg-threshold"},
                    {"text": f"BG-MAX: {self.align.bg_max:.2f} MB", "class": "max-threshold"},
                    {"text": f"BG-AVG: {self.align.bg_avg:.2f} MB", "class": "avg-threshold"},
                ]},
                {"label": "准出标准", "value": [{"text": self.align.base_criteria, "class": "criteria"}]}
            ]
            minor_summary += [
                {"value": [f"{k}: {v:.2f} MB" for k, v in fg.items() if v], "class": "fg-copy"},
                {"value": [f"{k}: {v:.2f} MB" for k, v in bg.items() if v], "class": "bg-copy"}
            ]

        else:
            headline = self.align.leak_headline
            union = {k: self.__mean_of_field(compilation, [k]) for k in ["MEM-MAX", "MEM-AVG"]}
            major_summary += [
                {"label": "准出标准", "value": [{"text": self.align.leak_criteria, "class": "criteria"}]}
            ]
            minor_summary += [{"value": [f"{k}: {v:.2f} MB" for k, v in union.items() if v]}]

        return {
            "title": f"{const.APP_DESC} Information",
            "headline": headline,
            "major_summary_items": major_summary,
            "minor_summary_items": minor_summary,
            "report_list": compilation
        }

    # Workflow: ======================== GFX & I/O ========================

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

    async def __gfx_rendering(
            self,
            db: "aiosqlite.Connection",
            templater: "Templater",
            data_dir: str,
            *_,
    ) -> dict:

        os.makedirs(
            group := os.path.join(templater.download, const.SUMMARY, data_dir), exist_ok=True
        )

        (gfx_data, *_), (joint, *_) = await asyncio.gather(
            Cubicle.query_gfx_data(db, data_dir), Cubicle.query_joint_data(db, data_dir)
        )
        raw_frames, vsync_sys, vsync_app, roll_ranges, drag_ranges, jank_ranges = gfx_data.values()
        metadata, (title, timestamp) = {}, joint

        io_data, *_ = await Cubicle.query_io_data(db, data_dir)
        io, rss, block = io_data.values()

        head = f"{title}_{Period.compress_time(timestamp)}" if title else data_dir
        image_loc = Path(group) / f"{head}_image.png"
        ionic_loc = Path(group) / f"{head}_ionic.png"

        image_task = asyncio.create_task(
            Painter.draw_gfx_metrics(
                metadata, raw_frames, vsync_sys, vsync_app, roll_ranges, drag_ranges, jank_ranges, str(image_loc),
            ), name="draw gfx metrics"
        )
        self.background_tasks.append(image_task)

        ionic_task = asyncio.create_task(
            Painter.draw_io_metrics(metadata, io, rss, block, str(ionic_loc)), name="draw io metrics"
        )
        self.background_tasks.append(ionic_task)

        # 平均帧
        avg_fps = round(
            sum(fps for f in raw_frames if (fps := f["fps_app"])) / (total_frames := len(raw_frames)), 2
        )
        # 掉帧率
        jnk_fps = round(
            sum(1 for f in raw_frames if f.get("is_jank")) / total_frames * 100, 2
        )
        # 最低帧率
        min_fps = round(
            min(fps for f in raw_frames if (fps := f["fps_app"])), 2
        )
        # 95分位帧率
        p95_fps = round(
            float(np.percentile([fps for f in raw_frames if (fps := f["fps_app"])], 95)), 2
        )

        conspiracy, segments = [], self.__split_frames_with_ranges(
            raw_frames, roll_ranges, drag_ranges, jank_ranges
        )

        for idx, (segment, roll, drag, jank, x_start, x_close) in enumerate(segments, start=1):
            padding = (x_close - x_start) * 0.05

            if not (mk := Scores.score_segment(segment, roll, drag, jank, fps_key="fps_app")):
                continue

            p = await templater.plot_gfx_analysis(
                frames=segment,
                x_start=x_start - padding,
                x_close=x_close + padding,
                roll_ranges=roll,
                drag_ranges=drag,
                jank_ranges=jank
            )
            p.title.text = f"[Range {idx:02}] - [{mk['score']}] - [{mk['level']}] - [{mk['label']}]"
            p.title.text_color = mk["color"]
            conspiracy.append(p)

        if not conspiracy:
            return {}

        mkt = Scores.score_segment(
            raw_frames, roll_ranges, drag_ranges, jank_ranges, fps_key="fps_app"
        )

        output_file(output_path := os.path.join(group, f"{data_dir}.html"))

        viewer_div = templater.generate_viewers(image_loc, ionic_loc)
        save(column(viewer_div, *conspiracy, Spacer(height=10), sizing_mode="stretch_width"))
        logger.info(f"{data_dir} Handler Done ...")

        return {
            "subtitle": title or data_dir,
            "subtitle_link": str(Path(const.SUMMARY) / data_dir / Path(output_path).name),
            "evaluate": [
                {
                    "fields": [
                        {"text": f"Score: {mkt['score'] * 100:.2f}", "class": "refer"},
                        {"text": f"Level: {mkt['level']}", "class": "refer"}
                    ]
                }
            ],
            "tags": [
                {
                    "fields": [
                        {"label": "MIN: ", "value": min_fps, "unit": "FPS"},
                        {"label": "AVG: ", "value": avg_fps, "unit": "FPS"}
                    ]
                },
                {
                    "fields": [
                        {"label": "JNK: ", "value": jnk_fps, "unit": "%"},
                        {"label": "P95: ", "value": p95_fps, "unit": "FPS"}
                    ]
                }
            ]
        }

    async def gfx_rendition(
            self,
            db: "aiosqlite.Connection",
            templater: "Templater",
            team_data: dict,
            *_
    ) -> typing.Optional[dict]:

        cur_time, cur_data = team_data.get("time"), team_data["file"]

        compilation = await asyncio.gather(
            *(self.__gfx_rendering(db, templater, d) for d in cur_data)
        )

        return {
            "title": f"{const.APP_DESC} Information",
            "headline": self.align.gfx_headline,
            "major_summary_items": [
                {"label": "测试时间", "value": [{"text": cur_time or "Unknown", "class": "time"}]},
                {"label": "准出标准", "value": [{"text": self.align.gfx_criteria, "class": "criteria"}]}
            ],
            "report_list": compilation
        }


if __name__ == '__main__':
    pass
