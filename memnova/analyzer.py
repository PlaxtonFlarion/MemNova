#      _                _
#     / \   _ __   __ _| |_   _ _______ _ __
#    / _ \ | '_ \ / _` | | | | |_  / _ \ '__|
#   / ___ \| | | | (_| | | |_| |/ /  __/ |
#  /_/   \_\_| |_|\__,_|_|\__, /___\___|_|
#                         |___/
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import os
import json
import random
import string
import typing
import asyncio
import aiofiles
import aiosqlite
import statistics
import numpy as np
import pandas as pd
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
from jinja2 import (
    Environment, FileSystemLoader
)
from memcore.cubicle import Cubicle
from memcore.design import Design
from memnova import const


class Analyzer(object):

    def __init__(self, db: "aiosqlite.Connection", download: str):
        self.db = db
        self.download = download

    async def make_report(self, template: str, *args, **kwargs) -> None:
        template_dir, template_file = os.path.dirname(template), os.path.basename(template)
        loader = FileSystemLoader(template_dir)
        environment = Environment(loader=loader)
        template = environment.get_template(template_file)
        html = template.render(*args, **kwargs)

        salt: "typing.Callable" = lambda: "".join(
            random.choices(string.ascii_uppercase + string.digits, k=5)
        )
        html_file = os.path.join(self.download, f"{const.APP_DESC}_Inform_{salt()}.html")

        async with aiofiles.open(html_file, "w", encoding=const.CHARSET) as f:
            await f.write(html)
            logger.info(html_file)

        Design.build_file_tree(html_file)

    async def draw_memory(self, data_dir: str) -> dict[str, str]:

        async def draw(file_name: str, data_list: list[tuple]) -> dict:
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
                "activity": [
                    (act.split("/")[-1] if "/" in act else act) if act else act for act in activity
                ],
            }

            avg_value, max_value, min_value = float(np.mean(pss)), max(pss), min(pss)

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
            p.xaxis.major_label_orientation = 30 * np.pi / 180
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

            file_path = os.path.join(group, f"{file_name.upper()}_{data_dir}.html")
            output_file(file_path)
            save(p)

            return {
                f"{file_name}_max": f"{float(max_value):.2f}",
                f"{file_name}_avg": f"{float(avg_value):.2f}",
                f"{file_name}_loc": os.path.join(const.SUMMARY, data_dir, os.path.basename(file_path))
            }

        fg_list, bg_list = await Cubicle.query_mem_data(self.db, data_dir)
        os.makedirs(group := os.path.join(self.download, const.SUMMARY, data_dir), exist_ok=True)

        fg_data_dict, bg_data_dict = await asyncio.gather(
            draw("fg", fg_list), draw("bg", bg_list)
        )

        logger.info(f"{data_dir} Handler Done ...")

        return fg_data_dict | bg_data_dict | {"minor_title": data_dir}

    @staticmethod
    async def score_segment(
            frames: list[dict],
            roll_ranges: list[dict],
            drag_ranges: list[dict],
            jank_ranges: list[dict],
            fps_key: str
    ) -> typing.Optional[float]:

        if len(frames) < 5:
            return None

        if (duration := frames[-1]["timestamp_ms"] - frames[0]["timestamp_ms"]) <= 0:
            return None

        # 🟩 Jank 比例
        jank_total = sum(r["end_ts"] - r["start_ts"] for r in jank_ranges)
        jank_score = 1.0 - min(jank_total / duration, 1.0)

        # 🟩 帧延迟：超过理想帧时长的占比（如16.67ms）
        ideal_frame_time = 1000 / 60
        over_threshold = sum(1 for f in frames if f["duration_ms"] > ideal_frame_time)
        latency_score = 1.0 - over_threshold / len(frames)

        # 🟩 FPS 波动越大越扣分；越稳定越高分
        fps_values = [f.get(fps_key) for f in frames if f.get(fps_key)]
        if len(fps_values) >= 2:
            fps_std = statistics.stdev(fps_values)
            fps_stability = max(1.0 - min(fps_std / 10, 1.0), 0.0)
        else:
            fps_stability = 1.0  # 缺失帧率不扣分

        # 🔸 额外考虑平均FPS较低的情况
        fps_avg = sum(fps_values) / len(fps_values) if fps_values else 60
        fps_penalty = min(fps_avg / 60, 1.0)
        fps_score = fps_stability * fps_penalty

        # 🟩 有滑动/拖拽越多说明有交互，不能因为空白区域得高分
        motion_total = sum(r["end_ts"] - r["start_ts"] for r in roll_ranges + drag_ranges)
        motion_score = min(motion_total / duration, 1.0)

        # ✅ 综合得分：越高越流畅
        final_score = (
            jank_score * 0.4 +
            latency_score * 0.2 +
            fps_score * 0.2 +
            motion_score * 0.2
        )

        return round(final_score, 3)

    @staticmethod
    async def plot_analysis(
            frames: list[dict],
            x_start: int | float,
            x_close: int | float,
            roll_ranges: typing.Optional[list[dict]],
            drag_ranges: typing.Optional[list[dict]],
            jank_ranges: list[dict]
    ) -> typing.Any:

        for frame in frames:
            frame["color"] = "#FF4D4D" if frame.get("is_jank") else "#32CD32"

        source = ColumnDataSource(pd.DataFrame(frames))

        p = figure(
            x_range=Range1d(x_start, x_close),
            x_axis_label="时间 (ms)",
            y_axis_label="帧耗时 (ms)",
            height=700,
            sizing_mode="stretch_width",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            toolbar_location="above"
        )

        p.xaxis.major_label_orientation = 0.5  # 约30度
        align_start = min(f["timestamp_ms"] for f in frames)
        p.xaxis.axis_label = f"时间 (ms) - 起点 {align_start}ms"

        # 主帧折线图与散点
        p.line(
            "timestamp_ms", "duration_ms",
            source=source, line_width=2, color="#A9A9A9", alpha=0.6
        )
        p.scatter(
            "timestamp_ms", "duration_ms",
            source=source, size=6, color="color", alpha=0.8, legend_label="帧耗时"
        )

        # Hover 显示信息
        p.add_tools(HoverTool(tooltips=[
            ("时间", "@timestamp_ms ms"),
            ("耗时", "@duration_ms ms"),
            ("掉帧", "@is_jank"),
            ("类型", "@frame_type"),
            ("GPU合成", "@gpu_composition"),
            ("按时呈现", "@on_time_finish"),
            ("FPS系统", "@fps_sys"),
            ("FPS应用", "@fps_app"),
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

    async def plot_segments(self, data_dir: str) -> typing.Optional[dict]:

        def split_frames_by_time(frames: list[dict], segment_ms: int = 30000) -> list[list[dict]]:
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

        def quality_label(score: float) -> dict:
            if score >= 0.85:
                return {
                    "level": "A+",
                    "color": "#007E33",  # 深绿
                    "label": "极其流畅，无明显波动"
                }
            elif score >= 0.7:
                return {
                    "level": "A",
                    "color": "#3FAD00",  # 草绿
                    "label": "流畅稳定，仅偶尔波动"
                }
            elif score >= 0.55:
                return {
                    "level": "B",
                    "color": "#F4B400",  # 鲜黄
                    "label": "有部分抖动，整体尚可"
                }
            elif score >= 0.4:
                return {
                    "level": "C",
                    "color": "#FF8C00",  # 深橙
                    "label": "波动明显，体验一般"
                }
            elif score >= 0.25:
                return {
                    "level": "D",
                    "color": "#E04B00",  # 红橙
                    "label": "卡顿较多，影响操作"
                }
            else:
                return {
                    "level": "E",
                    "color": "#B00020",  # 深红
                    "label": "严重卡顿，建议优化"
                }

        frame_data, *_ = await Cubicle.query_gfx_data(self.db, data_dir)
        raw_frames, *_, roll_ranges, drag_ranges, jank_ranges = frame_data
        raw_frames = json.loads(raw_frames)
        roll_ranges = json.loads(roll_ranges)
        drag_ranges = json.loads(drag_ranges)
        jank_ranges = json.loads(jank_ranges)
        os.makedirs(group := os.path.join(self.download, const.SUMMARY, data_dir), exist_ok=True)

        segment_list = split_frames_by_time(raw_frames)

        conspiracy = []

        for idx, segment in enumerate(segment_list, start=1):
            x_start, x_close = segment[0]["timestamp_ms"], segment[-1]["timestamp_ms"]
            padding = (x_close - x_start) * 0.05

            seg_score = await self.score_segment(
                segment, roll_ranges, drag_ranges, jank_ranges, fps_key="fps_app"
            )
            if seg_score is None:
                continue
            labels = quality_label(seg_score)

            p = await self.plot_analysis(
                frames=segment,
                x_start=x_start - padding,
                x_close=x_close + padding,
                roll_ranges=None,
                drag_ranges=None,
                jank_ranges=jank_ranges,
            )
            p.title.text = f"[Frame Range {idx:02}] - [{labels['level']}] {labels['label']}"
            p.title.text_color = labels["color"]
            conspiracy.append(p)

        if not conspiracy:
            return None

        file_path = os.path.join(group, f"{data_dir}.html")
        output_file(file_path)
        save(column(*conspiracy, sizing_mode="stretch_width"))

        return {
            "frame_loc": os.path.join(const.SUMMARY, data_dir, os.path.basename(file_path)),
            "minor_title": data_dir
        }


if __name__ == '__main__':
    pass
