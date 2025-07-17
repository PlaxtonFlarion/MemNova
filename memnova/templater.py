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
import numpy
import pandas
import typing
import asyncio
import aiosqlite
from pathlib import Path
from loguru import logger
from bokeh.layouts import column
from bokeh.io import (
    curdoc, output_file
)
from bokeh.plotting import (
    save, figure
)
from bokeh.models import (
    ColumnDataSource, HoverTool, Spacer, Span, Div,
    DatetimeTickFormatter, BoxAnnotation, Range1d
)
from memcore.cubicle import Cubicle
from memnova.scores import Scores
from memnova import const


class Templater(object):

    def __init__(self, db: "aiosqlite.Connection", download: str):
        self.db = db
        self.download = download

    def generate_viewers(self) -> "Div":
        traces_path = Path(self.download).parent.resolve() / const.TRACES_DIR
        images_path = Path(self.download).parent.resolve() / const.IMAGES_DIR
        ionics_path = Path(self.download).parent.resolve() / const.IONICS_DIR

        viewers = [
            {
                "label": "➤ Traces 查看",
                "url": f"file:///{traces_path.as_posix()}",
                "color": "#4CAF50"
            },
            {
                "label": "➤ Images 查看",
                "url": f"file:///{images_path.as_posix()}",
                "color": "#4CAF50"
            },
            {
                "label": "➤ Ionics 查看",
                "url": f"file:///{ionics_path.as_posix()}",
                "color": "#4CAF50"
            },
            {
                "label": "➤ UI.Perfetto.dev 查看",
                "url": f"https://ui.perfetto.dev",
                "color": "#1E90FF"
            }
        ]

        buttons_html = "".join([
            f"""
            <a href="{v['url']}" target="_blank" style="
                display: inline-block;
                padding: 10px 20px;
                margin: 10px;
                background-color: {v['color']};
                color: white;
                text-decoration: none;
                font-weight: bold;
                border-radius: 6px;
                font-size: 15px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                {v['label']}
            </a>
            """ for v in viewers
        ])

        return Div(text=f"""
        <div style="margin-top: 40px; text-align: center;">
            {buttons_html}
        </div>
        """)

    # Notes: ======================== MEM ========================

    async def plot_mem_analysis(
            self,
            file_name: str,
            data_list: list[tuple],
            group: str
    ) -> dict:

        def extract_mode_blocks(df: "pandas.DataFrame") -> list[tuple["pandas.Timestamp", "pandas.Timestamp", str]]:
            """根据 foreground 字段，提取所有连续前台/后台区块的 [start, end, label] 列表"""
            blocks = []
            if df.empty:
                return blocks
            
            start_idx, cur_status = 0, df["foreground"].iloc[0]
            
            for i in range(1, len(df)):
                if (v := df["foreground"].iloc[i]) != cur_status:
                    blocks.append((df["x"].iloc[start_idx], df["x"].iloc[i-1], cur_status))
                    start_idx, cur_status = i, v
            blocks.append((df["x"].iloc[start_idx], df["x"].iloc[-1], cur_status))
            return blocks

        if not data_list:
            return {}

        # 数据处理
        df = pandas.DataFrame(
            data_list,
            columns=["timestamp", "rss", "pss", "uss", "opss", "activity", "adj", "foreground"]
        )

        # 处理异常时间格式
        df["x"] = pandas.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df = df.dropna(subset=["x"])
        df["activity"] = df["activity"].fillna("")

        # 区块分色（你可自定义）
        fg_color = "#D6ECFA"  # 前台区块淡蓝
        bg_color = "#F4F6FB"  # 后台区块淡灰

        # ...数据处理...
        if blocks := extract_mode_blocks(df):
            lefts = [b[0] for b in blocks]
            rights = [b[1] for b in blocks]
            colors = [fg_color if b[2] == "前台" else bg_color for b in blocks]
            p.quad(
                left=lefts, right=rights,
                bottom=y_start, top=y_end,
                fill_color=colors,
                fill_alpha=0.10,
                line_alpha=0
            )
        # ...后续 PSS/RSS/USS 主线等...

        y = df["pss"]
        max_value, min_value, avg_value = y.max(), y.min(), y.mean()

        value_span = max_value - min_value

        if value_span < 1e-6:
            pad = max(20, 0.05 * max_value)
            y_start = max(0, min_value - pad)
            y_end = max_value + pad
        else:
            pad = max(10, 0.12 * value_span)
            y_start = max(0, min_value - pad)
            y_end = max_value + pad

        # 配色与视觉分区
        pss_color = "#4074B4"  # 主线 PSS（深蓝，突出）
        rss_color = "#E07B39"  # RSS 辅助线（橙色）
        uss_color = "#6BCB77"  # USS 辅助线（草绿色）
        avg_color = "#6A4C93"  # 均值线（紫色）
        max_color = "#FF1D58"  # 峰值线（红色）
        min_color = "#009FFD"  # 谷值线（亮蓝）
        tie_color = "#ECF8FF"  # 区间高亮（极淡蓝）

        df["colors"] = df["pss"].apply(
            lambda v: max_color if v == max_value else (min_color if v == min_value else pss_color)
        )
        df["sizes"] = df["pss"].apply(lambda v: 7 if v in (max_value, min_value) else 3)
        source = ColumnDataSource(df)

        # 绘图主对象
        p = figure(
            sizing_mode="stretch_both",
            x_axis_type="datetime",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            title="Memory Usage over Time",
            y_range=Range1d(y_start, y_end),
        )

        # 主线PSS
        p.line(
            "x", "pss",
            source=source, line_width=2, color=pss_color, legend_label="PSS"
        )

        # 辅助线（RSS/USS）
        p.line(
            "x", "rss",
            source=source, line_width=1, color=rss_color, alpha=0.6, legend_label="RSS", line_dash="dashed"
        )
        p.line(
            "x", "uss",
            source=source, line_width=1, color=uss_color, alpha=0.6, legend_label="USS", line_dash="dotted"
        )

        # 极值点
        p.scatter(
            "x", "pss",
            source=source, size="sizes", color="colors", alpha=0.95
        )

        # 均值/极值线
        p.add_layout(
            Span(location=avg_value, dimension="width", line_color=avg_color, line_dash="dotted", line_width=2)
        )
        p.add_layout(
            Span(location=max_value, dimension="width", line_color=max_color, line_dash="dotted", line_width=2)
        )
        p.add_layout(
            Span(location=min_value, dimension="width", line_color=min_color, line_dash="dotted", line_width=2)
        )

        # 区间高亮
        p.add_layout(
            BoxAnnotation(bottom=min_value, top=max_value, fill_alpha=0.10, fill_color=tie_color)
        )

        # 悬浮提示
        tooltips = [
            ("时间", "@timestamp{%H:%M:%S}"),
            ("PSS", "@pss{0.00} MB"),
            ("RSS", "@rss{0.00} MB"),
            ("USS", "@uss{0.00} MB"),
            ("当前页", "@activity"),
            ("优先级", "@foreground"),
        ]
        hover = HoverTool(tooltips=tooltips, formatters={"@timestamp": "datetime"})
        p.add_tools(hover)

        # 网格/坐标轴/主题
        p.xgrid.grid_line_color = "#E3E3E3"
        p.ygrid.grid_line_color = "#E3E3E3"
        p.xgrid.grid_line_alpha = 0.25
        p.ygrid.grid_line_alpha = 0.25
        p.xaxis.axis_label = "时间轴"
        p.yaxis.axis_label = "内存用量 (MB)"
        p.xaxis.major_label_orientation = 30 * numpy.pi / 180
        p.xaxis.formatter = DatetimeTickFormatter(
            seconds="%H:%M:%S",
            minsec="%H:%M:%S",
            minutes="%H:%M",
            hourmin="%H:%M",
            hours="%H:%M",
            days="%m-%d",
            months="%m-%d",
            years="%Y-%m"
        )
        p.legend.location = "top_left"
        p.legend.click_policy = "hide"
        p.legend.border_line_alpha = 0.1
        p.legend.background_fill_alpha = 0.07
        p.background_fill_color = "#FBFCFD"
        p.background_fill_alpha = 0.2
        curdoc().theme = "caliber"

        # 文件导出与布局
        file_path = os.path.join(group, f"{file_name}_{Path(group).name}.html")
        output_file(file_path)

        viewer_div = self.generate_viewers()
        save(
            column(viewer_div, Spacer(height=10), p, sizing_mode="stretch_both")
        )

        # 结果结构
        return {
            "name": file_name,
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
                    "link": str(Path(group) / Path(file_path).name)
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
                Cubicle.query_mem_data(self.db, data_dir, union_query=True), Cubicle.query_joint_data(self.db, data_dir)
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

    # Notes: ======================== GFX ========================

    @staticmethod
    async def plot_gfx_analysis(
            frames: list[dict],
            x_start: int | float,
            x_close: int | float,
            roll_ranges: typing.Optional[list[dict]],
            drag_ranges: typing.Optional[list[dict]],
            jank_ranges: list[dict]
    ):

        # 🟢 颜色预处理
        for frame in frames:
            frame["color"] = "#FF4D4D" if frame.get("is_jank") else "#32CD32"

        df = pandas.DataFrame(frames)
        df["timestamp_s"] = df["timestamp_ms"] / 1000
        source = ColumnDataSource(df)
   
        # 🟢 动态 Y 轴范围
        y_avg = df["duration_ms"].mean()
        y_min = df["duration_ms"].min()
        y_max = df["duration_ms"].max()
        y_range = y_max - y_min
        y_start = max(0, y_min - 0.05 * y_range)
        y_end = y_max + 0.1 * y_range

        p = figure(
            x_range=Range1d(x_start, x_close),
            y_range=Range1d(y_start, y_end),
            x_axis_label="Time (ms)",
            y_axis_label="Frame Duration (ms)",
            height=700,
            sizing_mode="stretch_width",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            toolbar_location="above",
            output_backend="webgl"
        )

        align_start = int(df["timestamp_ms"].min())
        p.xaxis.axis_label = f"Time (ms) - Start {align_start}ms"
        p.xaxis.major_label_orientation = 0.5

        # 🟢 主折线
        p.line(
            "timestamp_ms", "duration_ms", 
            source=source, line_width=2, color="#A9A9A9", alpha=0.6, legend_label="Main Line"
        )

        # 🟢 点图（已预填色）
        spot = p.scatter("timestamp_ms", "duration_ms", source=source, size=4, color="color", alpha=0.8)

        # 🟢 Hover 信息
        p.add_tools(HoverTool(tooltips="""
            <div style="padding: 5px;">
                <b>时间:</b> @timestamp_s{0.0} s<br/>
                <b>耗时:</b> @duration_ms{0.000} ms<br/>
                <b>掉帧:</b> @is_jank<br/>
                <b>类型:</b> @frame_type<br/>
                <b>系统FPS:</b> @fps_sys<br/>
                <b>应用FPS:</b> @fps_app<br/>
                <b>图层:</b> @layer_name
            </div>
        """, mode="mouse", renderers=[spot]))

        # 🟢 阈值线 + 平均线 + 最大值线
        p.line(
            [x_start, x_close], [16.67, 16.67],
            line_color="#1E90FF", line_dash="dashed", line_width=1.5, legend_label="16.67ms / 60 FPS"
        )
        if "duration_ms" in df:
            p.line(
                [x_start, x_close], [y_avg, y_avg],
                line_color="#8700FF", line_dash="dotted", line_width=1, legend_label="Avg Duration"
            )
            p.line(
                [x_start, x_close], [y_max, y_max],
                line_color="#FF69B4", line_dash="dashed", line_width=1, legend_label="Max Duration"
            )

        # 🟢 用 Quad 绘制背景区间
        quad_top, quad_bottom = y_end, y_start
        quad_types = [
            ("Roll Region", roll_ranges, "#ADD8E6", 0.30),
            ("Drag Region", drag_ranges, "#FFA500", 0.25),
            ("Jank Region", jank_ranges, "#FF0000", 0.15),
        ]

        for label, ranges, color, alpha in quad_types:
            if ranges:
                quad_source = ColumnDataSource({
                    "left": [r["start_ts"] for r in ranges],
                    "right": [r["end_ts"] for r in ranges],
                    "top": [quad_top] * len(ranges),
                    "bottom": [quad_bottom] * len(ranges),
                })
                p.quad(
                    left="left", right="right", top="top", bottom="bottom",
                    source=quad_source, fill_color=color, fill_alpha=alpha, line_alpha=0,
                    legend_label=label
                )

        # 🟢 图例设置
        p.legend.location = "top_right"
        p.legend.click_policy = "hide"
        p.legend.label_text_font_size = "10pt"
        
        # 🟢 样式设定        
        p.title.text_font_size = "16pt"

        return p

    async def plot_gfx_segments(self, data_dir: str) -> typing.Optional[dict]:

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

        os.makedirs(
            group := os.path.join(self.download, const.SUMMARY, data_dir), exist_ok=True
        )

        (frame_data, *_), (joint, *_) = await asyncio.gather(
            Cubicle.query_gfx_data(self.db, data_dir), Cubicle.query_joint_data(self.db, data_dir)
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

        conspiracy, segments = [], split_frames_by_time(raw_frames)

        for idx, segment in enumerate(segments, start=1):
            x_start, x_close = segment[0]["timestamp_ms"], segment[-1]["timestamp_ms"]
            padding = (x_close - x_start) * 0.05

            if not (mk := Scores.score_segment(segment, roll_ranges, drag_ranges, jank_ranges, fps_key="fps_app")):
                continue

            p = await self.plot_gfx_analysis(
                frames=segment,
                x_start=x_start - padding,
                x_close=x_close + padding,
                roll_ranges=roll_ranges,  # todo 测试绘图性能
                drag_ranges=drag_ranges,  # todo 测试绘图性能
                jank_ranges=jank_ranges,
            )
            p.title.text = f"[Range {idx:02}] - [{mk['score']}] - [{mk['level']}] - [{mk['label']}]"
            p.title.text_color = mk["color"]
            conspiracy.append(p)

        if not conspiracy:
            return None

        file_path = os.path.join(group, f"{data_dir}.html")
        output_file(file_path)

        viewer_div = self.generate_viewers()
        save(
            column(viewer_div, *conspiracy, Spacer(height=10), sizing_mode="stretch_width")
        )

        logger.info(f"{data_dir} Handler Done ...")

        return {
            "subtitle": title or data_dir,
            "tags": [
                {
                    "fields": [
                        {"label": "掉帧率", "value": jank_rate, "unit": "%"},
                        {"label": "平均帧", "value": avg_fps, "unit": "FPS"}
                    ],
                    "link": str(Path(const.SUMMARY) / data_dir / Path(file_path).name),
                }
            ]
        }


if __name__ == '__main__':
    pass
