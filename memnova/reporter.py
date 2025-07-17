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
from memcore.cubicle import Cubicle
from memcore.design import Design
from memcore.profile import Align
from memnova.scores import Scores
from memnova.templater import Templater
from memnova import const


class Reporter(object):

    def __init__(self, src_total_place: str, vault: str, classify_type: str, align: "Align"):
        self.total_dir = os.path.join(src_total_place, const.TOTAL_DIR)
        self.before_time = time.time()

        self.align = align

        vault = vault or time.strftime("%Y%m%d%H%M%S", time.localtime(self.before_time))

        self.group_dir = os.path.join(self.total_dir, const.TREE_DIR, f"{classify_type}_{vault}")
        if not (group_dir := Path(self.group_dir)).exists():
            group_dir.mkdir(parents=True, exist_ok=True)

        self.db_file = os.path.join(self.total_dir, const.DB_FILE)
        self.log_file = os.path.join(self.group_dir, f"{const.APP_NAME}_log_{vault}.log")
        self.team_file = os.path.join(self.group_dir, f"{const.APP_NAME}_team_{vault}.yaml")

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

    @staticmethod
    def mean_of_field(compilation: list[dict], keys: list[str]) -> dict:
        result = {}
        for key in keys:
            # 提取所有 compilation 里的 fields 并找 label 以 key 结尾的值
            vals = [
                float(field["value"])
                for item in compilation if "tags" in item for tag in item["tags"] for field in tag["fields"]
                if field["label"].endswith(f"{key}: ") and field.get("value") not in (None, "", "nan")
            ]
            # 计算均值
            if vals:
                result[key] = float(np.mean(vals))
        return result

    @staticmethod
    def split_frames_by_time(frames: list[dict], segment_ms: int = 60000) -> list[list[dict]]:
        frames = sorted(frames, key=lambda f: f["timestamp_ms"])
        segment_list = []

        start_ts, close_ts = frames[0]["timestamp_ms"], frames[-1]["timestamp_ms"]
        cur_start = start_ts
        while cur_start < close_ts:
            cur_end = cur_start + segment_ms
            if seg := [f for f in frames if cur_start <= f["timestamp_ms"] < cur_end]:
                segment_list.append(seg)
            cur_start = cur_end

        return segment_list

    # Workflow: ======================== Track ========================

    @staticmethod
    async def track_rendering(
            db: "aiosqlite.Connection",
            templater: "Templater",
            data_dir: str
    ) -> dict:

        os.makedirs(
            group := os.path.join(templater.download, const.SUMMARY, data_dir), exist_ok=True
        )

        union_data_list, (joint, *_) = await asyncio.gather(
            Cubicle.query_mem_data(db, data_dir), Cubicle.query_joint_data(db, data_dir)
        )
        title, timestamp = joint

        df = pd.DataFrame(
            union_data_list,
            columns=["timestamp", "rss", "pss", "uss", "opss", "activity", "adj", "mode"]
        )
        group_stats = (
            df.groupby("mode")["pss"].agg(avg_pss="mean", max_pss="max", count="count").reset_index()
        )

        bokeh_link = await templater.plot_mem_analysis(df, str(Path(group) / f"{data_dir}.html"))
        logger.info(f"{data_dir} Handler Done ...")

        return {
            "subtitle": title or data_dir,
            "subtitle_link": str(Path(const.SUMMARY) / data_dir / Path(bokeh_link).name),
            "tags": [
                {
                    "fields": [
                        {"label": f"{row['mode']}-MAX: ", "value": f"{row['max_pss']:.2f}", "unit": "MB"},
                        {"label": f"{row['mode']}-AVG: ", "value": f"{row['avg_pss']:.2f}", "unit": "MB"}
                    ]
                } for _, row in group_stats.iterrows()
            ]
        }

    async def track_rendition(
            self,
            db: "aiosqlite.Connection",
            templater: "Templater",
            data_list: str,
            team_data: dict
    ) -> dict:

        compilation = await asyncio.gather(
            *(self.track_rendering(db, templater, data_dir) for data_dir in data_list)
        )

        fg_final = {
            "前台峰值": (avg_fg_max := self.mean_of_field(compilation, ["FG_MAX"])),
            "前台均值": (avg_fg_avg := self.mean_of_field(compilation, ["FG_AVG"])),
        }
        bg_final = {
            "后台峰值": (avg_bg_max := self.mean_of_field(compilation, ["BG_MAX"])),
            "后台均值": (avg_bg_avg := self.mean_of_field(compilation, ["BG_AVG"])),
        }

        conclusion = []
        if avg_fg_max and avg_fg_max > self.align.fg_max:
            conclusion.append("前台峰值超标")
        if avg_fg_avg and avg_fg_avg > self.align.fg_avg:
            conclusion.append("前台均值超标")
        if avg_bg_max and avg_bg_max > self.align.bg_max:
            conclusion.append("后台峰值超标")
        if avg_bg_avg and avg_bg_avg > self.align.bg_avg:
            conclusion.append("后台均值超标")
        expiry = ["Fail"] if conclusion else ["Pass"]

        return {
            "title": f"{const.APP_DESC} Information",
            "headline": self.align.headline,
            "major_summary_items": [
                {
                    "label": "测试时间",
                    "value": [team_data.get("time", "Unknown")]
                },
                {
                    "label": "测试结论",
                    "value": expiry + conclusion,
                },
                {
                    "label": "参考标准",
                    "value": [
                        f"FG-MAX: {self.align.fg_max:.2f} MB",
                        f"FG-AVG: {self.align.fg_avg:.2f} MB",
                        f"BG-MAX: {self.align.bg_max:.2f} MB",
                        f"BG-AVG: {self.align.bg_avg:.2f} MB",
                    ]
                },
                {
                    "label": "准出标准",
                    "value": [self.align.criteria]
                }
            ],
            "minor_summary_items": [
                {
                    "value": [f"{k}: {v} MB" for k, v in fg_final.items() if v],
                    "class": "fg-copy"
                },
                {
                    "value": [f"{k}: {v} MB" for k, v in bg_final.items() if v],
                    "class": "bg-copy"
                }
            ],
            "report_list": compilation
        }

    # Workflow: ======================== Lapse ========================

    @staticmethod
    async def lapse_rendering(
            db: "aiosqlite.Connection",
            templater: "Templater",
            data_dir: str
    ) -> dict:

        os.makedirs(
            group := os.path.join(templater.download, const.SUMMARY, data_dir), exist_ok=True
        )

        union_data_list, (joint, *_) = await asyncio.gather(
            Cubicle.query_mem_data(db, data_dir), Cubicle.query_joint_data(db, data_dir)
        )
        title, timestamp = joint

        df = pd.DataFrame(
            union_data_list,
            columns=["timestamp", "rss", "pss", "uss", "opss", "activity", "adj", "mode"]
        )

        mem_max_pss, mem_avg_pss = df["pss"].max(), df["pss"].mean()

        bokeh_link = await templater.plot_mem_analysis(df, str(Path(group) / f"{data_dir}.html"))
        logger.info(f"{data_dir} Handler Done ...")

        return {
            "subtitle": title or data_dir,
            "subtitle_link": str(Path(const.SUMMARY) / data_dir / Path(bokeh_link).name),
            "tags": [
                {
                    "fields": [
                        {"label": f"MEM-MAX: ", "value": f"{mem_max_pss:.2f}", "unit": "MB"},
                        {"label": f"MEM-AVG: ", "value": f"{mem_avg_pss:.2f}", "unit": "MB"}
                    ]
                }
            ]
        }

    async def lapse_rendition(
            self,
            db: "aiosqlite.Connection",
            templater: "Templater",
            data_list: str,
            team_data: dict,
    ) -> dict:

        compilation = await asyncio.gather(
            *(self.lapse_rendering(db, templater, data_dir) for data_dir in data_list)
        )

        union_final = {
            "内存峰值": self.mean_of_field(compilation, ["MEM_MAX"]),
            "内存均值": self.mean_of_field(compilation, ["MEM_AVG"]),
        }

        return {
            "title": f"{const.APP_DESC} Information",
            "headline": self.align.headline,
            "major_summary_items": [
                {
                    "label": "测试时间",
                    "value": [team_data.get("time", "Unknown")]
                },
                {
                    "label": "准出标准",
                    "value": [self.align.criteria]
                }
            ],
            "minor_summary_items": [
                {
                    "value": [f"{k}: {v} MB" for k, v in union_final.items() if v]
                }
            ],
            "report_list": compilation
        }

    # Workflow: ======================== Sleek ========================

    async def sleek_rendering(
            self,
            db: "aiosqlite.Connection",
            templater: "Templater",
            data_dir: str
    ) -> dict:

        os.makedirs(
            group := os.path.join(templater.download, const.SUMMARY, data_dir), exist_ok=True
        )

        (frame_data, *_), (joint, *_) = await asyncio.gather(
            Cubicle.query_gfx_data(db, data_dir), Cubicle.query_joint_data(db, data_dir)
        )
        raw_frames, vsync_sys, vsync_app, roll_ranges, drag_ranges, jank_ranges = frame_data.values()
        title, timestamp = joint

        # 平均帧
        avg_fps = round(
            sum(fps for f in raw_frames if (fps := f["fps_app"])) / (total_frames := len(raw_frames)), 2
        )
        # 掉帧率
        jank_rate = round(
            sum(1 for f in raw_frames if f.get("is_jank")) / total_frames * 100, 2
        )

        conspiracy, segments = [], self.split_frames_by_time(raw_frames)

        for idx, segment in enumerate(segments, start=1):
            x_start, x_close = segment[0]["timestamp_ms"], segment[-1]["timestamp_ms"]
            padding = (x_close - x_start) * 0.05

            if not (mk := Scores.score_segment(segment, roll_ranges, drag_ranges, jank_ranges, fps_key="fps_app")):
                continue

            p = await templater.plot_gfx_analysis(
                frames=segment,
                x_start=x_start - padding,
                x_close=x_close + padding,
                roll_ranges=roll_ranges,
                drag_ranges=drag_ranges,
                jank_ranges=jank_ranges
            )
            p.title.text = f"[Range {idx:02}] - [{mk['score']}] - [{mk['level']}] - [{mk['label']}]"
            p.title.text_color = mk["color"]
            conspiracy.append(p)

        if not conspiracy:
            return {}

        output_file(output_path := os.path.join(group, f"{data_dir}.html"))

        viewer_div = templater.generate_viewers()
        save(column(viewer_div, *conspiracy, Spacer(height=10), sizing_mode="stretch_width"))
        logger.info(f"{data_dir} Handler Done ...")

        return {
            "subtitle": title or data_dir,
            "subtitle_link": str(Path(const.SUMMARY) / data_dir / Path(output_path).name),
            "tags": [
                {
                    "fields": [
                        {"label": "掉帧率", "value": jank_rate, "unit": "%"},
                        {"label": "平均帧", "value": avg_fps, "unit": "FPS"}
                    ]
                }
            ]
        }

    # 流畅度
    async def sleek_rendition(
            self,
            db: "aiosqlite.Connection",
            templater: "Templater",
            data_list: str,
            team_data: dict,
    ) -> typing.Optional[dict]:

        compilation = await asyncio.gather(
            *(self.sleek_rendering(db, templater, data_dir) for data_dir in data_list)
        )

        return {
            "title": f"{const.APP_DESC} Information",
            "headline": self.align.headline,
            "major_summary_items": [
                {
                    "label": "测试时间",
                    "value": [team_data.get("time", "Unknown")]
                },
                {
                    "label": "准出标准",
                    "value": [self.align.criteria]
                }
            ],
            "report_list": compilation
        }


if __name__ == '__main__':
    pass
