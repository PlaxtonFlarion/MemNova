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

import typing
import numpy as np
import pandas as pd
from pathlib import Path
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource, Span, Div,
    DatetimeTickFormatter, Range1d, HoverTool
)
from memnova.scores import Scores


class Templater(object):
    """Templater"""

    def __init__(self, download: str):
        self.download = download

    def generate_viewers(
        self,
        trace_path: typing.Optional["Path"] = None,
        leak_path: typing.Optional["Path"] = None,
        gfx_path: typing.Optional["Path"] = None,
        io_path: typing.Optional["Path"] = None
    ) -> "Div":

        log_list = [f for f in Path(self.download).parent.resolve().glob("*.log") if f.is_file()]

        """
        Traces      #38BDF8 亮天蓝
        Leak        #F472B6 亮粉
        Gfx         #A78BFA 淡紫
        I/O         #34D399 鲜绿色
        日志         #6366F1 靛蓝
        Perfetto UI #FB923C 橙色
        """

        viewers = [
            {**({
                    "label": "➤ 🛰️Traces 查看",
                    "url": f"file:///{trace_path.as_posix()}",
                    "color": "#38BDF8"
                } if trace_path else {})},
            {**({
                    "label": "➤ 🧬Leak 查看",
                    "url": f"file:///{leak_path.as_posix()}",
                    "color": "#F43F5E"
                } if leak_path else {})},
            {**({
                    "label": "➤ 🌊Gfx 查看",
                    "url": f"file:///{gfx_path.as_posix()}",
                    "color": "#A78BFA"
                } if gfx_path else {})},
            {**({
                    "label": "➤ 📈I/O 查看",
                    "url": f"file:///{io_path.as_posix()}",
                    "color": "#10B981"
                } if io_path else {})},
            {**({
                     "label": "➤ 📄日志 查看",
                     "url": f"file:///{log_list[0].as_posix()}",
                     "color": "#6366F1"
                 } if log_list else {})},
            {
                "label": "➤ 🌐UI.Perfetto.dev 查看",
                "url": f"https://ui.perfetto.dev",
                "color": "#F59E42"
            }
        ]

        buttons_html = "".join([
            f"""
            <a href="{v['url']}" target="_blank" style="
                display: inline-block;
                padding: 14px 28px;
                margin: 12px 8px 24px 8px;
                background: linear-gradient(120deg, {v['color']} 60%, #1E293B 100%);
                color: #fff;
                text-decoration: none;
                font-weight: 600;
                border-radius: 14px;
                font-size: 17px;
                box-shadow: 0 4px 14px 0 rgba(30,41,59,0.12);
                letter-spacing: 0.04em;
                transition: all 0.22s cubic-bezier(.34,1.56,.64,1);
                will-change: transform;
            " onmouseover="this.style.transform='scale(1.01)';this.style.boxShadow='0 6px 18px 0 rgba(34,139,230,0.22)';"
              onmouseout="this.style.transform='';this.style.boxShadow='0 4px 14px 0 rgba(30,41,59,0.12)';"
            >
                {v['label']}
            </a>
            """ for v in viewers if v
        ])

        return Div(text=f"""
        <div style="margin-top: 48px; text-align: center; font-family: 'Segoe UI', 'Inter', 'Arial', sans-serif;">
            {buttons_html}
        </div>
        """)

    # Workflow: ======================== MEM ========================

    @staticmethod
    async def plot_mem_analysis(df: "pd.DataFrame") -> "figure":
        # 🟡 ==== 数据处理 ====
        df = df.copy()
        df["x"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df = df.dropna(subset=["x"])
        for col in ["summary_java_heap", "summary_native_heap", "summary_graphics", "pss", "rss", "uss"]:
            df[col] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0)
        df["activity"] = df["activity"].fillna("")

        # 🟡 ==== 滑动窗口均值 ====
        window_size = max(3, len(df) // 20)
        df["pss_sliding_avg"] = df["pss"].rolling(window=window_size, min_periods=1).mean()

        # 🟡 ==== 区块分组 ====
        df["block_id"] = (df["mode"] != df["mode"].shift()).cumsum()

        # 🟡 ==== 主统计 ====
        max_value, min_value, avg_value = df["pss"].max(), df["pss"].min(), df["pss"].mean()
        value_span = max_value - min_value
        if value_span < 1e-6:
            padding = max(20, 0.05 * max_value)
            y_start = max(0, min_value - padding)
            y_close = max_value + padding
        else:
            padding = max(10, 0.12 * value_span)
            y_start = max(0, min_value - padding)
            y_close = max_value + padding

        # 🟡 ==== 前后台区块统计 ====
        block_stats = df.groupby(["block_id", "mode"]).agg(
            start_time=("x", "first"),
            end_time=("x", "last"),
        ).reset_index()

        # 🟡 ==== 主线折线 & 极值 ====
        pss_color = "#3564B0"  # 主线深蓝
        rss_color = "#FEB96B"  # RSS淡橙
        uss_color = "#90B2C8"  # USS淡蓝灰
        avg_color = "#BDB5D5"  # 均值灰紫
        max_color = "#FF5872"  # 峰值桃红
        min_color = "#54E3AF"  # 谷值薄荷绿
        sld_color = "#A8BFFF"

        # 🟡 ==== 区块色 ====
        fg_color = "#8FE9FC"  # 前台湖蓝
        bg_color = "#F1F1F1"  # 后台淡灰
        fg_alpha = 0.15
        bg_alpha = 0.35

        # 🟡 ==== 堆叠配色（马卡龙/莫兰迪风）====
        stack_fields = ["summary_java_heap", "summary_native_heap", "summary_graphics"]
        stack_colors = [
            "#FFD6E0",  # Java Heap   淡粉
            "#D4E7FF",  # Native Heap 淡蓝
            "#CAE7E1",  # Graphics    淡青
        ]
        stack_labels = ["Java Heap", "Native Heap", "Graphics"]

        # 🟡 ==== 堆叠数据 ====
        stack_source = ColumnDataSource(df)

        # 🟡 === 绘图主对象 ===
        p = figure(
            sizing_mode="stretch_both",
            x_axis_type="datetime",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            title="Memory Usage over Time"
        )

        # 🟡 ==== 前后台分区底色 ====
        for _, row in block_stats.iterrows():
            color = fg_color if row["mode"] == "FG" else bg_color
            alpha = fg_alpha if row["mode"] == "FG" else bg_alpha
            p.quad(
                left=row["start_time"], right=row["end_time"],
                bottom=y_start, top=y_close,
                fill_color=color, fill_alpha=alpha, line_alpha=0
            )

        # 🟡 ==== 面积堆叠 ====
        p.varea_stack(
            stackers=stack_fields,
            x="x",
            color=stack_colors,
            legend_label=stack_labels,
            source=stack_source,
            alpha=0.4
        )

        # 🟡 ==== 折线 / 极值点 ====
        df["colors"] = df["pss"].apply(
            lambda v: max_color if v == max_value else (min_color if v == min_value else pss_color)
        )
        df["sizes"] = df["pss"].apply(lambda v: 7 if v in (max_value, min_value) else 3)
        source = ColumnDataSource(df)

        # 🟡 ==== PSS 主线 ====
        p.line(
            "x", "pss",
            source=source, line_width=2.5, color=pss_color, legend_label="PSS"
        )

        # 🟡 ==== RSS 辅助线 ====
        p.line(
            "x", "rss",
            source=source, line_width=1.2, color=rss_color, alpha=0.7, legend_label="RSS", line_dash="dashed"
        )

        # 🟡 ==== USS 辅助线 ====
        p.line(
            "x", "uss",
            source=source, line_width=1.2, color=uss_color, alpha=0.7, legend_label="USS", line_dash="dotted"
        )

        # 🟡 ==== 滑窗均值线 ====
        p.line(
            "x", "pss_sliding_avg",
            source=source, line_width=1.5, color=sld_color, alpha=0.7, legend_label="Sliding Avg", line_dash="dotdash"
        )

        # 🟡 ==== 均值线 ====
        p.add_layout(
            Span(location=avg_value, dimension="width", line_color=avg_color, line_dash="dotted", line_width=2)
        )

        # 🟡 ==== 极值点 ====
        pss_spot = p.scatter(
            "x", "pss",
            source=source, size="sizes", color="colors", alpha=0.98
        )

        # 🟡 ==== 悬浮提示 ====
        tooltips = [
            ("时间", "@timestamp{%H:%M:%S}"),
            ("滑窗均值", "@pss_sliding_avg{0.00} MB"),
            ("PSS", "@pss{0.00} MB"),
            ("RSS", "@rss{0.00} MB"),
            ("USS", "@uss{0.00} MB"),
            ("Java Heap", "@summary_java_heap{0.00} MB"),
            ("Native Heap", "@summary_native_heap{0.00} MB"),
            ("Graphics", "@summary_graphics{0.00} MB"),
            ("当前页", "@activity"),
            ("优先级", "@mode"),
        ]
        hover = HoverTool(
            tooltips=tooltips, formatters={"@timestamp": "datetime"}, mode="mouse", renderers=[pss_spot]
        )
        p.add_tools(hover)

        # 🟡 ==== 主题 & 坐标轴 ====
        p.xgrid.grid_line_color = "#E3E3E3"
        p.ygrid.grid_line_color = "#E3E3E3"
        p.xgrid.grid_line_alpha = 0.25
        p.ygrid.grid_line_alpha = 0.25
        p.xaxis.axis_label = "时间轴"
        p.yaxis.axis_label = "内存用量 (MB)"
        p.xaxis.major_label_orientation = np.pi / 6
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
        p.background_fill_alpha = 0.24
        curdoc().theme = "caliber"

        return p

    # Workflow: ======================== GFX ========================

    @staticmethod
    async def plot_gfx_analysis(
        frames: list[dict],
        roll_ranges: typing.Optional[list[dict]],
        drag_ranges: typing.Optional[list[dict]],
        jank_ranges: typing.Optional[list[dict]]
    ) -> "figure":

        # 🟢 ==== 汇总所有区间时间 ====
        all_starts, all_closes = [], []

        all_starts.append(frames[0]["timestamp_ms"])
        all_closes.append(frames[-1]["timestamp_ms"])

        for sequence in [roll_ranges, drag_ranges, jank_ranges]:
            if sequence:
                all_starts += [r["start_ts"] for r in sequence]
                all_closes += [r["end_ts"] for r in sequence]

        x_start, x_close = min(all_starts) / 1000, max(all_closes) / 1000

        # 🟢 ==== 掉帧颜色预处理 ====
        for frame in frames:
            frame["color"] = "#FF4D4D" if frame.get("is_jank") else "#32CD32"

        df = pd.DataFrame(frames)
        df["timestamp_s"] = df["timestamp_ms"] / 1000
        source = ColumnDataSource(df)

        # 🟢 ==== 动态 Y 轴范围 ====
        y_avg = df["duration_ms"].mean()
        y_min = df["duration_ms"].min()
        y_max = df["duration_ms"].max()
        y_range = y_max - y_min
        y_start = max(0, y_min - 0.05 * y_range)
        y_close = y_max + 0.1 * y_range

        p = figure(
            y_range=Range1d(y_start, y_close),
            x_axis_label="Time (s)",
            y_axis_label="Frame Duration (ms)",
            height=700,
            sizing_mode="stretch_width",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            toolbar_location="above",
            output_backend="webgl"
        )

        align_start = int(df["timestamp_s"].min())
        p.xaxis.axis_label = f"Time (s) - Start {align_start}s"
        p.xaxis.major_label_orientation = 0.5

        # 🟢 ==== 颜色定义 ====
        main_color = "#A9A9A9"
        avg_color = "#8700FF"
        max_color = "#FF69B4"

        # 🟢 ==== 主折线 ====
        p.line(
            "timestamp_s", "duration_ms",
            source=source, line_width=2, color=main_color, alpha=0.6, legend_label="Frame Duration"
        )

        # 🟢 ==== 点图 ====
        spot = p.scatter(
            "timestamp_s", "duration_ms",
            source=source, size=4, color="color", alpha=0.8
        )

        # 🟢 ==== 平均线 + 最高线 + 阈值线 ====
        p.line(
            [x_start, x_close], [y_avg, y_avg],
            line_color=avg_color, line_dash="dotted", line_width=1, legend_label=f"Avg: {y_avg:.1f}ms"
        )
        p.line(
            [x_start, x_close], [y_max, y_max],
            line_color=max_color, line_dash="dashed", line_width=1, legend_label=f"Max: {y_max:.1f}ms"
        )
        p.line(
            [x_start, x_close], [16.67, 16.67],
            line_color="#1E90FF", line_dash="dashed", line_width=1.5, legend_label="16.67ms / 60 FPS"
        )

        # 🟢 ==== Quad 绘制背景区间 ====
        quad_top, quad_bottom = y_close, y_start
        quad_types = [
            ("Scroll Region", roll_ranges, "#ADD8E6", 0.30),
            ("Drag Region", drag_ranges, "#FFA500", 0.25),
            ("Jank Region", jank_ranges, "#FF0000", 0.15),
        ]
        for label, ranges, color, alpha in quad_types:
            if ranges:
                quad_source = ColumnDataSource({
                    "left": [r["start_ts"] / 1000 for r in ranges],
                    "right": [r["end_ts"] / 1000 for r in ranges],
                    "top": [quad_top] * len(ranges),
                    "bottom": [quad_bottom] * len(ranges),
                })
                p.quad(
                    left="left", right="right", top="top", bottom="bottom",
                    source=quad_source, fill_color=color, fill_alpha=alpha, line_alpha=0, legend_label=label
                )

        # 🟢 ==== Hover 信息 ====
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

        # 🟢 ==== 图例设置 ====
        p.legend.location = "top_right"
        p.legend.click_policy = "hide"
        p.legend.label_text_font_size = "10pt"

        # 🟢 ==== 标题设置 ====
        p.title.text_font_size = "16pt"
        p.title.text = "[Frame Range]"
        p.title.text_color = "#FFAF5F"

        return p


if __name__ == '__main__':
    pass
