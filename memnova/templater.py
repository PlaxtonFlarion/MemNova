#  _____                    _       _
# |_   _|__ _ __ ___  _ __ | | __ _| |_ ___ _ __
#   | |/ _ \ '_ ` _ \| '_ \| |/ _` | __/ _ \ '__|
#   | |  __/ | | | | | |_) | | (_| | ||  __/ |
#   |_|\___|_| |_| |_| .__/|_|\__,_|\__\___|_|
#                    |_|
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


class Templater(object):
    """Templater"""

    @staticmethod
    def generate_viewers(
        trace_loc: "Path", leak_loc: "Path", gfx_loc: "Path", io_loc: "Path", log_loc: "Path"
    ) -> "Div":
        """
        生成可视化报告入口按钮的 HTML 视图。

        根据传入的各类分析文件路径，动态生成跳转按钮集合，供用户在报告页面中快速访问
        Trace、Leak、Gfx、I/O、日志等分析结果，同时提供在线 Perfetto UI 入口。
        按钮样式包含渐变背景、阴影与悬停缩放效果，整体居中排布，提升可视化交互体验。

        Parameters
        ----------
        trace_loc : Path
            Trace 分析文件路径对象，若为空则不生成对应按钮。

        leak_loc : Path
            内存泄漏分析文件路径对象，若为空则不生成对应按钮。

        gfx_loc : Path
            图形渲染分析文件路径对象，若为空则不生成对应按钮。

        io_loc : Path
            I/O 性能分析文件路径对象，若为空则不生成对应按钮。

        log_loc : Path
            日志文件路径对象，若为空则不生成对应按钮。

        Returns
        -------
        Div
            `bokeh.models.Div` HTML 元素，包含一个或多个跳转按钮：
            - 每个按钮对应一种分析文件或在线工具。
            - 所有按钮采用统一的渐变配色和悬停交互效果。
            - 按钮以居中方式展示，便于用户快速导航。

        Notes
        -----
        - 所有按钮均在新标签页中打开。
        - 当路径对象为 None 或空时，不会生成对应按钮。
        """
        viewers = [
            {**({"label": "➤ 🛰️Traces 查看", "url": trace_loc.name, "color": "#38BDF8"} if trace_loc else {})},
            {**({"label": "➤ 🧬Leak 查看",   "url": leak_loc.name,  "color": "#F43F5E"} if leak_loc  else {})},
            {**({"label": "➤ 🌊Gfx 查看",    "url": gfx_loc.name,   "color": "#A78BFA"} if gfx_loc   else {})},
            {**({"label": "➤ 📈I/O 查看",    "url": io_loc.name,    "color": "#10B981"} if io_loc    else {})},
            {**({"label": "➤ 📄Log 查看",    "url": log_loc.name,   "color": "#6366F1"} if log_loc   else {})},
            {
                "label": "➤ 🌐UI.Perfetto.dev 查看", "url": f"https://ui.perfetto.dev", "color": "#F59E42"
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
    def plot_mem_analysis(
        mem_data: list[dict], extreme: bool = False
    ) -> "figure":
        """
        绘制内存用量随时间变化的分析图。

        将内存采集数据转换为时间序列可视化，支持 PSS 主线、RSS/USS 辅助线、
        Java/Native/Graphics 堆叠面积图，以及前后台模式分区底色。可选地标注前台、
        后台及全局的极值点，以便快速定位异常。

        Parameters
        ----------
        mem_data : list of dict
            内存采集数据列表，每个元素包含时间戳、内存统计值、模式信息等字段。

        extreme : bool, default=False
            是否启用极值标记模式：
            - True  ：分别标注前台最大值、后台最大值。
            - False ：仅标注全局最大值。

        Returns
        -------
        figure
            `bokeh.plotting.figure` 对象，包含以下绘制元素：
            - 堆叠面积图（Java Heap、Native Heap、Graphics）。
            - PSS 主线及滑动均值、RSS 与 USS 辅助线。
            - 前后台分区底色，透明度区分模式。
            - 极值点标记及悬浮提示（HoverTool）。
            - 自适应坐标轴、时间格式化和交互工具。

        Notes
        -----
        - 横轴为时间，纵轴为内存用量（MB）。
        - 前后台区分使用不同底色：前台湖蓝，后台浅灰。
        - 悬浮提示提供多维度信息（时间、滑窗均值、堆统计、模式等）。
        - 适合内存趋势分析、异常检测及多模式性能对比。
        """

        # 🟡 ==== 数据处理 ====
        df = pd.DataFrame(mem_data)
        df.loc[:, "x"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df = df.dropna(subset=["x"])
        for col in ["summary_java_heap", "summary_native_heap", "summary_graphics", "pss", "rss", "uss"]:
            df.loc[:, col] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0)
        df.loc[:, "activity"] = df["activity"].fillna("-")

        # 🟡 ==== 滑动窗口均值 ====
        window_size = max(3, len(df) // 20)
        df.loc[:, "pss_sliding_avg"] = df["pss"].rolling(window=window_size, min_periods=1).mean()

        # 🟡 ==== 区块分组 ====
        mode_series = df["mode"]
        changed = mode_series.ne(mode_series.shift())
        df.loc[:, "block_id"] = changed.cumsum()

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

        # 🟡 ==== 区块配色 ====
        fg_color = "#8FE9FC"  # 前台湖蓝
        bg_color = "#F1F1F1"  # 后台淡灰
        fg_alpha = 0.15
        bg_alpha = 0.35

        # 🟡 ==== 堆叠配色 ====
        stack_fields = ["summary_java_heap", "summary_native_heap", "summary_graphics"]
        stack_labels = ["Java Heap", "Native Heap", "Graphics"]
        stack_colors = ["#FFD6E0", "#D4E7FF", "#CAE7E1"]

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

        # 🟡 ==== 默认极值 ====
        df.loc[:, "shapes"] = "circle"
        df.loc[:, "colors"] = pss_color
        df.loc[:, "sizes"] = 3

        # 🟡 ==== 分区极值 ====
        fg_df = df[df["mode"] == "FG"]
        bg_df = df[df["mode"] == "BG"]

        fg_max = fg_df["pss"].max() if not fg_df.empty else None
        bg_max = bg_df["pss"].max() if not bg_df.empty else Non

        # 🟡 ==== 标记极值 ====
        df.loc[(df["pss"] == fg_max) & (df["mode"] == "FG") & extreme, "colors"] = "#FF90A0"  # 前台最大
        df.loc[(df["pss"] == fg_max) & (df["mode"] == "FG") & extreme, "sizes"] = 7
        df.loc[(df["pss"] == fg_max) & (df["mode"] == "FG") & extreme, "shapes"] = "circle"

        df.loc[(df["pss"] == bg_max) & (df["mode"] == "BG") & extreme, "colors"] = "#FFB366"  # 后台最大
        df.loc[(df["pss"] == bg_max) & (df["mode"] == "BG") & extreme, "sizes"] = 7
        df.loc[(df["pss"] == bg_max) & (df["mode"] == "BG") & extreme, "shapes"] = "square"

        df.loc[(df["pss"] == max_value) & (~extreme), "colors"] = max_color  # 全局最大
        df.loc[(df["pss"] == max_value) & (~extreme), "sizes"] = 7
        df.loc[(df["pss"] == max_value) & (~extreme), "shapes"] = "circle"

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
            source=source, size="sizes", color="colors", marker="shapes", alpha=0.98
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
    def plot_gfx_analysis(
        frames: list[dict],
        roll_ranges: typing.Optional[list[dict]],
        drag_ranges: typing.Optional[list[dict]],
        jank_ranges: typing.Optional[list[dict]]
    ) -> "figure":
        """
        绘制图形渲染帧耗时分析图。

        将帧级别性能数据可视化，展示帧耗时变化趋势、前端滚动/拖拽/掉帧区间，
        并提供平均值、最大值及性能阈值参考线，用于图形渲染性能分析与优化诊断。

        Parameters
        ----------
        frames : list of dict
            帧数据列表，每个元素应包含：
            - `timestamp_ms` : 采样时间戳（毫秒）。
            - `duration_ms`  : 当前帧渲染耗时（毫秒）。
            - `is_jank`      : 是否掉帧（布尔值）。
            - `frame_type`   : 帧类型描述（如 App / SurfaceFlinger）。
            - `fps_sys` / `fps_app` : 系统与应用帧率。
            - `layer_name`   : 图层名称（可选）。

        roll_ranges : list of dict or None
            滚动操作的时间区间，每个元素包含：
            - `start_ts` / `end_ts` : 区间起止时间戳（毫秒）。

        drag_ranges : list of dict or None
            拖拽操作的时间区间，结构同上。

        jank_ranges : list of dict or None
            掉帧发生的时间区间，结构同上。

        Returns
        -------
        figure
            `bokeh.plotting.figure` 对象，包含：
            - 主帧耗时折线与颜色标记的散点（绿色正常 / 红色掉帧）。
            - 平均值、最大值及 60 FPS 阈值参考线。
            - 滚动、拖拽、掉帧背景区间标记。
            - 悬浮提示（HoverTool）显示帧耗时与上下文信息。
            - 可交互图例与缩放平移工具。

        Notes
        -----
        - X 轴为秒，基于帧采样时间戳换算。
        - Y 轴为帧渲染耗时（毫秒），动态调整范围。
        - 背景区块区分不同交互类型（滚动、拖拽、掉帧）。
        - 用于可视化帧性能瓶颈、交互性能衰退及掉帧集中区域。
        """

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
        df.loc[:, "timestamp_s"] = df["timestamp_ms"] / 1000
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
