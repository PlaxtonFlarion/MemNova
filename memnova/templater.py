#   _____                    _       _
#  |_   _|__ _ __ ___  _ __ | | __ _| |_ ___ _ __
#    | |/ _ \ '_ ` _ \| '_ \| |/ _` | __/ _ \ '__|
#    | |  __/ | | | | | |_) | | (_| | ||  __/ |
#    |_|\___|_| |_| |_| .__/|_|\__,_|\__\___|_|
#                     |_|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import os
import json
import numpy
import pandas
import typing
import asyncio
import aiosqlite
from pathlib import Path
from loguru import logger
from datetime import datetime
from bokeh.layouts import column
from bokeh.io import (
    curdoc, output_file
)
from bokeh.plotting import (
    save, figure
)
from bokeh.models import (
    ColumnDataSource, Span, HoverTool,
    DatetimeTickFormatter, BoxAnnotation, Range1d
)
from memcore.cubicle import Cubicle
from memnova.scores import Scores
from memnova import const


class Templater(object):

    def __init__(self, db: "aiosqlite.Connection", download: str):
        self.db = db
        self.download = download

    @staticmethod
    async def plot_mem_analysis(
            file_name: str,
            data_list: list[tuple],
            group: str
    ) -> dict:

        if not data_list:
            return {}

        try:
            timestamp, rss, pss, uss, opss, activity, adj, foreground = list(zip(*data_list))
        except ValueError:
            return {}

        data = {
            "x": [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in timestamp],
            "y": pss,
            "rss": rss,
            "uss": uss,
            "adj": adj,
            "foreground": foreground,
            "activity": [a for a in activity if a],
        }

        avg_value, max_value, min_value = float(numpy.mean(pss)), max(pss), min(pss)

        data["colors"] = [
            "#FF4B00" if y == max_value else ("#00FF85" if y == min_value else "#FFBC00") for y in data["y"]
        ]
        data["sizes"] = [
            5 if y == max_value else (5 if y == min_value else 2) for y in data["y"]
        ]

        source = ColumnDataSource(data=data)
        p = figure(
            sizing_mode="stretch_both",
            x_axis_type="datetime",
            title="Memory Usage over Time",
            y_range=Range1d(min_value - 100 if min_value >= 100 else 0, max_value + 150)
        )
        p.line(
            "x", "y",
            source=source, line_width=1, alpha=0.8, color="#FFBC00", legend_label=file_name.upper()
        )

        p.scatter(
            "x", "y",
            source=source, size="sizes", color="colors", hover_fill_color="#DF9911", hover_alpha=0.5
        )

        p.scatter(color="#FF4B00", legend_label=f"峰值: {max_value:.2f} MB")
        p.scatter(color="#F900FF", legend_label=f"均值: {avg_value:.2f} MB")

        # 范围
        mid_box = BoxAnnotation(
            bottom=min_value, top=max_value, fill_alpha=0.1, fill_color="#0072B2"
        )
        p.add_layout(mid_box)

        # 平均线
        avg_line = Span(
            location=avg_value, dimension="width", line_color="#F900FF", line_dash="dotted", line_width=1
        )
        p.add_layout(avg_line)

        # 最大值
        max_line = Span(
            location=max_value, dimension="width", line_color="#FF4B00", line_dash="dotted", line_width=1
        )
        p.add_layout(max_line)

        # 最小值
        min_line = Span(
            location=min_value, dimension="width", line_color="#00FF85", line_dash="dotted", line_width=1
        )
        p.add_layout(min_line)

        # 悬浮提示
        tooltips = """
            <div style="background: linear-gradient(to bottom, #B6FBFF, #83A4D4); padding: 5px 10px;">
                <div>
                    <span style="font-size: 17px;">PSS:</span>
                    <span style="font-size: 17px; font-weight: bold; color: #4B4B4B;">@y{0.00} MB</span>
                </div>
                <div>
                    <span style="font-size: 17px;">RSS:</span>
                    <span style="font-size: 17px; font-weight: bold; color: #4B4B4B;">@rss{0.00} MB</span>
                </div>
                <div>
                    <span style="font-size: 17px;">USS:</span>
                    <span style="font-size: 17px; font-weight: bold; color: #4B4B4B;">@uss{0.00} MB</span>
                </div>

                <hr style="border: 0; height: 1px; background-image: repeating-linear-gradient(to right, rgba(0,0,0,0.75), rgba(0,0,0,0.75) 1px, rgba(0,0,0,0) 1px, rgba(0,0,0,0) 5px);">

                <div>
                    <span style="font-size: 17px;">时间轴:</span>
                    <span style="font-size: 17px; font-weight: bold; color: #9400D3;">@x{%H:%M:%S}</span>
                </div>
                <div>
                    <span style="font-size: 17px;">优先级:</span>
                    <span style="font-size: 17px; font-weight: bold; color: #483D8B;">@foreground</span>
                </div>
                <div>
                    <span style="font-size: 17px;">当前页:</span>
                    <span style="font-size: 17px; font-weight: bold; color: #006400;">@activity</span>
                </div>
            </div>
        """

        hover = HoverTool(
            tooltips=tooltips, formatters={"@x": "datetime"}
        )
        p.add_tools(hover)

        p.xgrid.grid_line_color = "gray"
        p.ygrid.grid_line_color = "gray"
        p.xgrid.grid_line_alpha = 0.2
        p.ygrid.grid_line_alpha = 0.2

        p.xaxis.axis_label = "时间轴"
        p.yaxis.axis_label = "内存用量 (MB)"
        p.xaxis.major_label_orientation = 30 * numpy.pi / 180
        p.xaxis.formatter = DatetimeTickFormatter(
            microseconds="%H:%M:%S", milliseconds="%H:%M:%S", seconds="%H:%M:%S",
            minsec="%H:%M:%S", minutes="%Y-%m-%d %H:%M:%S",
            hourmin="%Y-%m-%d %H:%M:%S", hours="%Y-%m-%d %H:%M:%S",
            days="%Y-%m-%d %H:%M:%S", months="%Y-%m-%d %H:%M:%S", years="%Y-%m-%d %H:%M:%S"
        )

        p.legend.location = "top_left"
        p.legend.click_policy = "hide"
        p.legend.border_line_width = 2
        p.legend.border_line_color = "#11D2DF"
        p.legend.border_line_alpha = 0.1
        p.legend.background_fill_color = "#DFC911"
        p.legend.background_fill_alpha = 0.1
        p.background_fill_color = "#ECE9E6"
        p.background_fill_alpha = 0.2

        # 主题
        curdoc().theme = "light_minimal"

        file_path = os.path.join(group, f"{file_name}_{Path(group).name}.html")
        output_file(file_path)
        save(p)

        return {
            "name": file_name,  # FG / BG / MEM
            "metrics": {
                "MAX": round(float(max_value), 2),
                "AVG": round(float(avg_value), 2),
            },
            "tags": [
                {
                    "fields": [
                        {"label": f"{file_name}-MAX: ", "value": f"{float(max_value):.2f}", "unit": "MB"},
                        {"label": f"{file_name}-AVG: ", "value": f"{float(avg_value):.2f}", "unit": "MB"},
                    ],
                    "link": str(Path(const.SUMMARY) / Path(group).name / Path(file_path).name)
                }
            ]
        }

    async def plot_mem_segments(self, data_dir: str) -> dict[str, str]:
        os.makedirs(
            group := os.path.join(self.download, const.SUMMARY, data_dir), exist_ok=True
        )

        if data_dir.startswith(const.TRACK_TREE_DIR.split("_")[0]):
            (fg_list, bg_list), (joint, *_) = await asyncio.gather(
                Cubicle.query_mem_data(self.db, data_dir), Cubicle.query_joint_data(self.db, data_dir)
            )
            title, timestamp = joint

            fg_upshot, bg_upshot = await asyncio.gather(
                *(self.plot_mem_analysis(name, data, group) for name, data in [("FG", fg_list), ("BG", bg_list)])
            )

            compilation = {
                "subtitle": title or data_dir,
                "tags": fg_upshot.get("tags", []) + bg_upshot.get("tags", []),
                "metrics": {
                    **({
                           f"{fg_upshot['name']}-MAX": fg_upshot["metrics"]["MAX"],
                           f"{fg_upshot['name']}-AVG": fg_upshot["metrics"]["AVG"]
                       } if fg_upshot and fg_upshot.get("metrics") else {}),
                    **({
                           f"{bg_upshot['name']}-MAX": bg_upshot["metrics"]["MAX"],
                           f"{bg_upshot['name']}-AVG": bg_upshot["metrics"]["AVG"]
                       } if bg_upshot and bg_upshot.get("metrics") else {})
                }
            }

        else:
            union_list, (joint, *_) = await asyncio.gather(
                Cubicle.query_mem_data(self.db, data_dir, True), Cubicle.query_joint_data(self.db, data_dir)
            )
            title, timestamp = joint

            union_upshot = await self.plot_mem_analysis("MEM", union_list, group)

            compilation = {
                "subtitle": title or data_dir,
                "tags": union_upshot.get("tags", []),
                "metrics": {
                    **({
                           f"{union_upshot['name']}-MAX": union_upshot["metrics"]["MAX"],
                           f"{union_upshot['name']}-AVG": union_upshot["metrics"]["AVG"]
                       } if union_upshot and union_upshot.get("metrics") else {})
                }
            }

        logger.info(f"{data_dir} Handler Done ...")
        return compilation

    @staticmethod
    async def plot_gfx_analysis(
            frames: list[dict],
            x_start: int | float,
            x_close: int | float,
            roll_ranges: typing.Optional[list[dict]],
            drag_ranges: typing.Optional[list[dict]],
            jank_ranges: list[dict]
    ) -> typing.Any:

        for frame in frames:
            frame["color"] = "#FF4D4D" if frame.get("is_jank") else "#32CD32"

        source = ColumnDataSource(pandas.DataFrame(frames))

        p = figure(
            x_range=Range1d(x_start, x_close),
            x_axis_label="时间 (ms)",
            y_axis_label="帧耗时 (ms)",
            height=700,
            sizing_mode="stretch_width",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            toolbar_location="above"
        )

        align_start = min(f["timestamp_ms"] for f in frames)
        p.xaxis.axis_label = f"时间 (ms) - 起点 {align_start}ms"
        p.xaxis.major_label_orientation = 0.5  # 约30度

        # 主帧折线图与散点
        p.line(
            "timestamp_ms", "duration_ms",
            source=source, line_width=2, color="#A9A9A9", alpha=0.6
        )
        p.scatter(
            "timestamp_ms", "duration_ms",
            source=source, size=2, color="color", alpha=0.8, legend_label="帧耗时"
        )

        # Hover 显示信息
        p.add_tools(HoverTool(tooltips=[
            ("时间", "@timestamp_ms ms"),
            ("耗时", "@duration_ms ms"),
            ("掉帧", "@is_jank"),
            ("类型", "@frame_type"),
            ("GPU合成", "@gpu_composition"),
            ("按时呈现", "@on_time_finish"),
            ("系统FPS", "@fps_sys"),
            ("应用FPS", "@fps_app"),
            ("图层", "@layer_name"),
        ]))

        # 16.67ms 阈值线
        threshold_line = Span(
            location=16.67, dimension="width", line_color="#1E90FF", line_dash="dashed", line_width=1.5
        )
        p.add_layout(threshold_line)

        # 背景区间：滑动
        for rng in roll_ranges or []:
            p.add_layout(BoxAnnotation(
                left=rng["start_ts"],
                right=rng["end_ts"],
                fill_color="#ADD8E6",
                fill_alpha=0.3
            ))

        # 背景区间：拖拽
        for rng in drag_ranges or []:
            p.add_layout(BoxAnnotation(
                left=rng["start_ts"],
                right=rng["end_ts"],
                fill_color="#FFA500",
                fill_alpha=0.25
            ))

        # 背景区间：连续掉帧
        for rng in jank_ranges or []:
            p.add_layout(BoxAnnotation(
                left=rng["start_ts"],
                right=rng["end_ts"],
                fill_color="#FF0000",
                fill_alpha=0.15
            ))

        p.legend.label_text_font_size = "10pt"
        p.title.text_font_size = "16pt"

        return p

    async def plot_gfx_segments(self, data_dir: str) -> typing.Optional[dict]:

        def split_frames_by_time(frames: list[dict], segment_ms: int = 60000) -> list[list[dict]]:
            frames = sorted(frames, key=lambda f: f["timestamp_ms"])
            segments = []
            start_ts = frames[0]["timestamp_ms"]
            close_ts = frames[-1]["timestamp_ms"]

            cur_start = start_ts
            while cur_start < close_ts:
                cur_end = cur_start + segment_ms
                if seg := [f for f in frames if cur_start <= f["timestamp_ms"] < cur_end]:
                    segments.append(seg)
                cur_start = cur_end

            return segments

        os.makedirs(
            group := os.path.join(self.download, const.SUMMARY, data_dir), exist_ok=True
        )

        (frame_data, *_), (title, *_) = await asyncio.gather(
            Cubicle.query_gfx_data(self.db, data_dir), Cubicle.query_joint_data(self.db, data_dir)
        )
        raw_frames, vsync_sys, vsync_app, roll_ranges, drag_ranges, jank_ranges = frame_data

        raw_frames = json.loads(raw_frames)
        roll_ranges = json.loads(roll_ranges)
        drag_ranges = json.loads(drag_ranges)
        jank_ranges = json.loads(jank_ranges)

        # 平均帧
        avg_fps = round(
            sum(fps for f in raw_frames if (fps := f["fps_app"])) / (total_frames := len(raw_frames)), 2
        )
        # 掉帧率
        jank_rate = round(
            sum(1 for f in raw_frames if f.get("is_jank")) / total_frames * 100, 2
        )

        segment_list = split_frames_by_time(raw_frames)

        conspiracy = []

        for idx, segment in enumerate(segment_list, start=1):
            x_start, x_close = segment[0]["timestamp_ms"], segment[-1]["timestamp_ms"]
            padding = (x_close - x_start) * 0.05

            seg_score = Scores.score_segment(
                segment, roll_ranges, drag_ranges, jank_ranges, fps_key="fps_app"
            )
            if seg_score is None:
                continue
            mk = Scores.quality_label(seg_score)

            p = await self.plot_gfx_analysis(
                frames=segment,
                x_start=x_start - padding,
                x_close=x_close + padding,
                roll_ranges=None,
                drag_ranges=None,
                jank_ranges=jank_ranges,
            )
            p.title.text = f"[Range {idx:02}] - [{seg_score}] - [{mk['level']}] - [{mk['label']}]"
            p.title.text_color = mk["color"]
            conspiracy.append(p)

        if not conspiracy:
            return None

        file_path = os.path.join(group, f"{data_dir}.html")
        output_file(file_path)
        save(column(*conspiracy, sizing_mode="stretch_width"))

        logger.info(f"{data_dir} Handler Done ...")

        return {
            "subtitle": title or data_dir,
            "tags": [
                {
                    "fields": [
                        {"label": "平均帧", "value": avg_fps, "unit": "FPS"},
                        {"label": "掉帧率", "value": jank_rate, "unit": "%"}
                    ],
                    "link": str(Path(const.SUMMARY) / data_dir / Path(file_path).name),
                }
            ]
        }


if __name__ == '__main__':
    pass
