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

import numpy
import typing
import pandas as pd
from pathlib import Path
from bokeh.layouts import column
from bokeh.io import (
    curdoc, output_file
)
from bokeh.plotting import (
    save, figure
)
from bokeh.models import (
    ColumnDataSource, Spacer, Span, Div,
    DatetimeTickFormatter, Range1d, HoverTool
)
from memnova import const


class Templater(object):

    def __init__(self, download: str):
        self.download = download

    def generate_viewers(self) -> "Div":
        parent = Path(self.download).parent.resolve()

        traces_path = parent / const.TRACES_DIR
        images_path = parent / const.IMAGES_DIR
        ionics_path = parent / const.IONICS_DIR

        logs = [f for f in parent.glob("*.log") if f.is_file()]

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
            {**({
                     "label": "➤ 日志 查看",
                     "url": f"file:///{logs[0].as_posix()}",
                     "color": "#4CAF50"
                 } if logs else {})},
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

    # Workflow: ======================== MEM ========================

    async def plot_mem_analysis(
            self,
            df: "pd.DataFrame",
            output_path: str
    ) -> str:

        # 数据处理
        df["x"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df = df.dropna(subset=["x"])
        df["pss"] = pd.to_numeric(df["pss"], errors="coerce")
        df["rss"] = pd.to_numeric(df["rss"], errors="coerce")
        df["uss"] = pd.to_numeric(df["uss"], errors="coerce")
        df["activity"] = df["activity"].fillna("")

        # 滑动窗口平均
        window_size = max(3, len(df) // 20)
        df["pss_sliding_avg"] = df["pss"].rolling(window=window_size, min_periods=1).mean()

        # 区块分组
        df["block_id"] = (df["mode"] != df["mode"].shift()).cumsum()

        # 主统计
        max_value, min_value, avg_value = df["pss"].max(), df["pss"].min(), df["pss"].mean()
        value_span = max_value - min_value
        if value_span < 1e-6:
            pad = max(20, 0.05 * max_value)
            y_start = max(0, min_value - pad)
            y_end = max_value + pad
        else:
            pad = max(10, 0.12 * value_span)
            y_start = max(0, min_value - pad)
            y_end = max_value + pad

        # 区块统计
        block_stats = df.groupby(["block_id", "mode"]).agg(
            start_time=("x", "first"),
            end_time=("x", "last"),
            avg_pss=("pss", "mean"),
            max_pss=("pss", "max"),
            min_pss=("pss", "min"),
            count=("pss", "size"),
        ).reset_index()

        # 配色与视觉分区
        pss_color = "#3A5C83"   # 主线 PSS（深蓝灰）
        rss_color = "#6C7A89"   # RSS 辅助线（灰蓝/亚麻灰）
        uss_color = "#8EABDD"   # USS 辅助线（淡蓝紫/天青）
        avg_color = "#BD93F9"   # 均值线（淡紫/莫兰迪紫）
        max_color = "#FFB86C"   # 峰值线（温暖橙/沙金色）
        min_color = "#50FA7B"   # 谷值线（绿色/薄荷绿）
        # 区块分色
        fg_color = "#5BB8FF"  # 深蓝（前台）
        bg_color = "#BDBDBD"  # 深灰（后台）
        fg_alpha = 0.22
        bg_alpha = 0.18

        # 绘图主对象
        p = figure(
            sizing_mode="stretch_both",
            x_axis_type="datetime",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            title="Memory Usage over Time",
            y_range=Range1d(y_start, y_end),
        )

        # 分区底色
        for _, row in block_stats.iterrows():
            color = fg_color if row["mode"] == "FG" else bg_color
            alpha = fg_alpha if row["mode"] == "FG" else bg_alpha
            p.quad(
                left=row["start_time"], right=row["end_time"],
                bottom=y_start, top=y_end,
                fill_color=color, fill_alpha=alpha, line_alpha=0
            )

        df["colors"] = df["pss"].apply(
            lambda v: max_color if v == max_value else (min_color if v == min_value else pss_color)
        )
        df["sizes"] = df["pss"].apply(lambda v: 7 if v in (max_value, min_value) else 3)
        source = ColumnDataSource(df)

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

        p.line(
            "x", "pss_sliding_avg",
            source=source, line_width=2, color="#A8BFFF", line_dash="dotdash", alpha=0.85, legend_label="Sliding Avg"
        )

        # 极值点
        pss_spot = p.scatter(
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

        # 悬浮提示
        tooltips = [
            ("时间", "@timestamp{%H:%M:%S}"),
            ("滑窗均值", "@pss_sliding_avg{0.00} MB"),
            ("PSS", "@pss{0.00} MB"),
            ("RSS", "@rss{0.00} MB"),
            ("USS", "@uss{0.00} MB"),
            ("当前页", "@activity"),
            ("优先级", "@mode"),
        ]
        hover = HoverTool(
            tooltips=tooltips, formatters={"@timestamp": "datetime"}, mode="mouse", renderers=[pss_spot]
        )
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
        output_file(output_path)

        viewer_div = self.generate_viewers()
        save(column(viewer_div, Spacer(height=10), p, sizing_mode="stretch_both"))

        return output_path

    # Workflow: ======================== GFX ========================

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

        df = pd.DataFrame(frames)
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


if __name__ == '__main__':
    pass
