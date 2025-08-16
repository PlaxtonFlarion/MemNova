#  _                    _
# | |   _   _ _ __ ___ (_)_  __
# | |  | | | | '_ ` _ \| \ \/ /
# | |__| |_| | | | | | | |>  <
# |_____\__,_|_| |_| |_|_/_/\_\
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import numpy as np
import pandas as pd
import matplotlib.dates as md
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.dates import (
    AutoDateLocator, ConciseDateFormatter
)
from loguru import logger


class Lumix(object):
    """Lumix"""

    # Notes: ======================== MEM ========================

    @staticmethod
    def draw_mem_metrics(
        mem_data: list[dict],
        output_path: str,
        *_,
        **kwargs
    ) -> str:
        """
        绘制内存使用时序图（PSS/RSS/USS 及堆叠内存区），并保存为图片文件。

        Parameters
        ----------
        mem_data : list[dict]
            内存数据列表，每条记录包含时间戳、内存值（PSS、RSS、USS）、模式（前台/后台）、堆内存等信息。

        output_path : str
            输出图片的保存路径（包含文件名和扩展名）。

        Returns
        -------
        str
            保存的图片文件路径。

        Notes
        -----
        - 图表包含 PSS 主曲线、RSS/USS 辅助曲线、滑动平均线，以及 Java Heap/Native Heap/Graphics 堆叠区。
        - 前台/后台区块以不同底色区分，并标注均值带、极值点。
        - 图例由主曲线与堆叠区两部分构成，评分信息显示在图表左上角。
        """
        df = pd.DataFrame(mem_data)

        df.loc[:, "x"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df = df.dropna(subset=["x"])
        df.loc[:, "num_x"] = md.date2num(df["x"])
        df.loc[:, "pss"] = pd.to_numeric(df["pss"], errors="coerce")
        df = df.dropna(subset=["pss"])

        # 🟡 ==== 滑窗均值 ====
        window_size = max(3, len(df) // 20)
        df.loc[:, "pss_sliding_avg"] = df["pss"].rolling(window=window_size, min_periods=1).mean()

        # 🟡 ==== 区块分组 ====
        mode_series = df["mode"]
        changed = mode_series.ne(mode_series.shift())
        df.loc[:, "block_id"] = changed.cumsum()

        # 🟡 ==== 全局统计 ====
        avg_val = kwargs.get("avg", df["pss"].mean())
        max_val = kwargs.get("max", df["pss"].max())
        min_val = kwargs.get("min", df["pss"].min())
        y_range = max_val - min_val if max_val > min_val else 1
        offset = 0.1
        y_min = max(0, min_val - offset * y_range)
        y_max = max_val + offset * y_range

        # 🟡 ==== 区块统计 ====
        block_stats = df.groupby(["block_id", "mode"]).agg(
            start_time=("num_x", "first"), end_time=("num_x", "last")
        ).reset_index()

        # 🟡 ==== 判断内存趋势 ====
        summary_text = (
            f"Trend: {kwargs['trend']}\n"
            f"Poly Trend: {kwargs['poly_trend']}\n"
            f"Score: {kwargs['trend_score']:.2f}\n"
            f"Jitter: {kwargs['jitter_index']:.4f}\n"
            f"Slope: {kwargs['slope']:.4f}\n"
            f"R²: {kwargs['r_squared']}"
        )

        # 🟡 ==== 配色与视觉分区 ====
        pss_color = kwargs.get("color", "#3564B0")
        rss_color = "#FEB96B"
        uss_color = "#90B2C8"
        avg_color = "#BDB5D5"
        max_color = "#FF5872"
        # min_color = "#54E3AF"
        sld_color = "#A8BFFF"
        avg_band_color = "#D0D0FF"

        # 🟡 ==== 区块配色 ====
        fg_color = "#8FE9FC"
        bg_color = "#F1F1F1"
        fg_alpha = 0.15
        bg_alpha = 0.35

        # 🟡 ==== 绘图 ====
        fig, ax = plt.subplots(figsize=(16, 6))
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(md.DateFormatter("%H:%M:%S"))
        ax.xaxis.set_major_locator(md.AutoDateLocator())

        # 🟡 ==== 前后台区块底色 ====
        for _, row in block_stats.iterrows():
            color = fg_color if row["mode"] == "FG" else bg_color
            alpha = fg_alpha if row["mode"] == "FG" else bg_alpha
            ax.fill_between(
                [row["start_time"], row["end_time"]], y_min, y_max, color=color, alpha=alpha, zorder=0
            )

        # 🟡 ==== 堆叠区 ====
        stack_colors = ["#FFD6E0", "#D4E7FF", "#CAE7E1"]
        stack_labels = ["Java Heap", "Native Heap", "Graphics"]
        ax.stackplot(
            df["num_x"],
            df["summary_java_heap"],
            df["summary_native_heap"],
            df["summary_graphics"],
            colors=stack_colors,
            alpha=0.38,
            labels=stack_labels
        )

        # 🟡 ==== PSS主线 / RSS折线 / USS折线 ====
        ax.plot(df["num_x"], df["pss"], color=pss_color, linewidth=1.2, label="PSS")
        ax.plot(df["num_x"], df["rss"], color=rss_color, linewidth=1.1, linestyle="--", alpha=0.75, label="RSS")
        ax.plot(df["num_x"], df["uss"], color=uss_color, linewidth=1.1, linestyle=":", alpha=0.75, label="USS")

        # 🟡 ==== 滑动平均 ====
        ax.plot(
            df["num_x"], df["pss_sliding_avg"],
            color=sld_color, linestyle="--", linewidth=0.8, alpha=0.8, label="Sliding Avg"
        )

        # 🟡 ==== 均值带 ====
        ax.axhspan(
            avg_val - 0.05 * y_range, avg_val + 0.05 * y_range, color=avg_band_color, alpha=0.25, label="Average Range"
        )

        # 🟡 ==== 均值线 ====
        ax.axhline(y=avg_val, linestyle=":", color=avg_color, linewidth=0.8)

        # 🟡 ==== 极值点 ====
        ax.scatter(
            df.loc[df["pss"] == max_val, "num_x"], df.loc[df["pss"] == max_val, "pss"],
            s=20, color=max_color, zorder=3, label="Max"
        )

        # 🟡 ==== 设置轴与样式 ====
        ax.set_title("Memory Usage Over Time (PSS)")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("PSS (MB)")
        ax.grid(True, linestyle="--", alpha=0.4)
        plt.xticks(rotation=30)

        # 🟡 ==== 堆叠区 legend ====
        stack_handles = [
            Patch(facecolor=c, edgecolor="none", alpha=0.38, label=l)
            for c, l in zip(stack_colors, stack_labels)
        ]

        # 🟡 ==== 构造伪图例项 ====
        line_handles = [
            Line2D([0], [0], color=pss_color, linewidth=1.2, label="PSS"),
            Line2D([0], [0], color=rss_color, linewidth=1.1, linestyle="--", label="RSS"),
            Line2D([0], [0], color=uss_color, linewidth=1.1, linestyle=":", label="USS"),
            Line2D([0], [0], color=sld_color, linestyle="--", label="Sliding Avg"),
            Line2D([0], [0], color=avg_color, linestyle=":", label="PSS AVG"),
            Line2D([0], [0], marker="o", color=max_color, linestyle="None", markersize=7, label="Max")
        ]

        # 🟡 ==== 展示图例（主图例+堆叠区图例） ====
        ax.legend(
            handles=stack_handles + line_handles,
            loc="upper right",
            fontsize=9,
            frameon=True,
            framealpha=0.3,
            facecolor="#F9F9F9",
            edgecolor="#CCCCCC"
        )

        # 🟡 ==== 评分信息 ====
        ax.text(
            0.008, 0.98, summary_text,
            transform=ax.transAxes,
            ha="left", va="top",
            fontsize=9,
            color="#595959",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#F8F9FB", alpha=0.48, edgecolor="none")
        )

        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

        logger.info(f"[√] 图表已保存至: {output_path}")

        return output_path

    # Notes: ======================== GFX ========================

    @staticmethod
    def draw_gfx_metrics(
        raw_frames: list[dict],
        vsync_sys: list[dict],
        vsync_app: list[dict],
        roll_ranges: list[dict],
        drag_ranges: list[dict],
        jank_ranges: list[dict],
        output_path: str,
        *_,
        **kwargs
    ) -> str:
        """
        绘制帧耗时与帧率分布图，并高亮滚动、拖拽及掉帧区域，输出为图片文件。

        Parameters
        ----------
        raw_frames : list[dict]
            原始帧数据列表，每条记录包含时间戳（毫秒）、帧耗时（毫秒）等信息。

        vsync_sys : list[dict]
            系统层 FPS 采样数据列表，每条记录包含 FPS 值。

        vsync_app : list[dict]
            应用层 FPS 采样数据列表，每条记录包含 FPS 值。

        roll_ranges : list[dict]
            滚动（Scroll）区间列表，每项包含起止时间戳（毫秒）。

        drag_ranges : list[dict]
            拖拽（Drag）区间列表，每项包含起止时间戳（毫秒）。

        jank_ranges : list[dict]
            掉帧（Jank）区间列表，每项包含起止时间戳（毫秒）。

        output_path : str
            输出图片的保存路径（包含文件名和扩展名）。

        Returns
        -------
        str
            保存的图片文件路径。

        Notes
        -----
        - 主折线为帧耗时（ms），附带平均线、最大耗时线及 16.67ms 基准线（对应 60 FPS）。
        - 附加多帧率参考线（30/45/90/120 FPS）用于快速对比性能表现。
        - 滚动、拖拽、掉帧区间以不同颜色背景高亮标识。
        - 左上角展示系统层与应用层 FPS 的均值、最大值、评分与等级。
        """
        timestamps = [f["timestamp_ms"] / 1000 for f in raw_frames]
        durations = [f["duration_ms"] for f in raw_frames]
        fps_sys = [f["fps"] for f in vsync_sys]
        fps_app = [f["fps"] for f in vsync_app]

        # 🟢 ==== 计算帧耗时平均和最大值 ====
        avg_dur = np.mean(durations) if durations else 0
        max_dur = np.max(durations) if durations else 0
        ths_dur = 16.67

        fig, ax1 = plt.subplots(figsize=(16, 6))

        # 🟢 ==== 颜色定义 ====
        dur_color = "#585858"
        avg_color = "#448AFF"
        max_color = "#FF4081"
        ths_color = "#FF0000"
        roll_color = "#A2C8E6"
        drag_color = "#FFD39B"
        jank_color = "#F24C4C"

        # 🟢 ==== 主线 / 平均线 / 最高线 ====
        ax1.plot(timestamps, durations, label="Frame Duration", color=dur_color, linewidth=1.2)
        ax1.axhline(avg_dur, linestyle=":", linewidth=1.0, color=avg_color, alpha=0.88)
        ax1.axhline(max_dur, linestyle="--", linewidth=1.0, color=max_color, alpha=0.88)
        ax1.axhline(ths_dur, linestyle="--", linewidth=1.0, color=ths_color, alpha=0.88)

        # 🟢 ==== 多帧率基准线 ====
        fps_marks = {
            "120 FPS": {"ms": 1000 / 120, "color": "#BBBBBB"},
            "90 FPS": {"ms": 1000 / 90, "color": "#999999"},
            "45 FPS": {"ms": 1000 / 45, "color": "#999999"},
            "30 FPS": {"ms": 1000 / 30, "color": "#BBBBBB"}
        }
        for label, style in fps_marks.items():
            ax1.axhline(style["ms"], linestyle="--", linewidth=0.5, color=style["color"])

        # 🟢 ==== 滑动区 / 拖拽区 / 掉帧区 背景区块绘制 ====
        for r in roll_ranges:
            ax1.axvspan(r["start_ts"] / 1000, r["end_ts"] / 1000, color=roll_color, alpha=0.10)
        for r in drag_ranges:
            ax1.axvspan(r["start_ts"] / 1000, r["end_ts"] / 1000, color=drag_color, alpha=0.15)
        for r in jank_ranges:
            ax1.axvspan(r["start_ts"] / 1000, r["end_ts"] / 1000, color=jank_color, alpha=0.35)

        # 🟢 ==== FPS 统计信息 ====
        max_sys = max(fps_sys, default=0)
        avg_sys = sum(fps_sys) / len(fps_sys) if fps_sys else 0
        max_app = max(fps_app, default=0)
        avg_app = sum(fps_app) / len(fps_app) if fps_app else 0

        fps_summary = (
            f"SYS: Avg {avg_sys:.1f} / Max {max_sys:.1f}\n"
            f"APP: Avg {avg_app:.1f} / Max {max_app:.1f}\n"
            f"Score: {kwargs['score'] * 100:.2f}\n"
            f"Level: {kwargs['level']}"
        )

        # 🟢 ==== 自定义图例（颜色区块 + 主线 + 60 FPS）====
        legend_elements = [
            Line2D([0], [0], color=dur_color, lw=1.2, label="Frame Duration"),
            Line2D([0], [0], color=avg_color, lw=1.0, linestyle=":", label=f"Avg: {avg_dur:.1f}ms"),
            Line2D([0], [0], color=max_color, lw=1.0, linestyle="--", label=f"Max: {max_dur:.1f}ms"),
            Line2D([0], [0], color=ths_color, lw=1.0, linestyle='--', label="16.67ms / 60 FPS"),
            Line2D([0], [0], color="#999999", lw=0.5, linestyle='--', label="45 FPS / 90 FPS"),
            Line2D([0], [0], color="#BBBBBB", lw=0.5, linestyle='--', label="30 FPS / 120 FPS"),
            Patch(facecolor=roll_color, edgecolor="none", label="Scroll Region"),
            Patch(facecolor=drag_color, edgecolor="none", label="Drag Region"),
            Patch(facecolor=jank_color, edgecolor="none", label="Jank Region"),
        ]

        ax1.legend(
            handles=legend_elements,
            loc="upper right",
            fontsize=8,
            title_fontsize=9,
            frameon=True,
            facecolor="#FAFAFA",
            edgecolor="#CCCCCC"
        )

        # 🟢 ==== 展示FPS ====
        ax1.text(
            0.008, 0.98, fps_summary,
            transform=ax1.transAxes,
            ha="left", va="top",
            fontsize=9,
            color="#595959",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#F8F9FB", alpha=0.48, edgecolor="none")
        )

        # 🟢 ==== 图表样式 ====
        ax1.set_title("Frame Duration Over Time")
        ax1.set_xlabel("Timestamp (s)")
        ax1.set_ylabel("Frame Duration (ms)")
        ax1.grid(True, linestyle="--", linewidth=0.3, alpha=0.6)
        ax1.spines["right"].set_visible(False)
        ax1.spines["top"].set_visible(False)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

        logger.info(f"[√] 图表已保存至: {output_path}")

        return output_path

    # Notes: ======================== I/O ========================

    @staticmethod
    def draw_io_metrics(
        io_data: list[dict],
        output_path: str,
        *_,
        **kwargs
    ) -> str:
        """
        绘制 I/O 读写与系统调用的时间序列图，支持多指标对比和性能评分展示。

        Parameters
        ----------
        io_data : list[dict]
            I/O 采样数据列表，每条记录包含时间戳、读写字节量、字符数、系统调用次数等。

        output_path : str
            输出图片的保存路径（包含文件名和扩展名）。

        Returns
        -------
        str
            保存的图片文件路径。

        Notes
        -----
        - 主轴（左）显示读写字节量变化（MB/s），含 Read Bytes、Write Bytes、RChar、WChar 四条曲线。
        - 副轴（右）显示系统调用变化（Count/s），含 Syscr、Syscw 两条曲线。
        - 评分信息（等级、得分、峰值、抖动、空闲占比、Swap、系统调用爆发等）显示在图表左上角。
        - 对负值进行归零处理，确保数据可视化的稳定性。
        """
        df = pd.DataFrame(io_data)

        fig, ax1 = plt.subplots(figsize=(16, 6))
        ax2 = ax1.twinx()

        # 🔵 ==== 时间轴 ====
        ts = pd.to_datetime(df["timestamp"], errors="coerce")
        # 避免 NaT 造成报错
        ts = ts.ffill().bfill()  
        # 估计中位采样周期
        dt = ts.diff().dt.total_seconds()
        med_interval = float(np.median(dt[dt > 0])) if (dt > 0).any() else None
        # 配置时间轴格式器
        locator = AutoDateLocator()
        formatter = ConciseDateFormatter(locator)
        ax1.xaxis.set_major_locator(locator)
        ax1.xaxis.set_major_formatter(formatter)
        ax2.xaxis.set_major_locator(locator)
        ax2.xaxis.set_major_formatter(formatter)
        # 让时间标签不重叠
        fig.autofmt_xdate()

        # 🔵 ==== 字节量主轴（MB） ====
        byte_fields = [
            ("read_bytes", "#4F8CFD", "Read Bytes Δ", "o"),
            ("write_bytes", "#6BE675", "Write Bytes Δ", "^"),
            ("rchar", "#F09F3E", "RChar Δ", "s"),
            ("wchar", "#F46C9D", "WChar Δ", "x")
        ]
        byte_handles = []
        for col, color, label, marker in byte_fields:
            vals = df[col].astype(float).diff().fillna(0)
            vals = vals.clip(lower=0)   # 负值归零
            ax1.plot(
                ts, vals,
                color=color, label=label, marker=marker, linewidth=1.1, markersize=2.2, alpha=0.95
            )
            byte_handles.append(
                Line2D([0], [0], color=color, marker=marker, label=label, linewidth=2)
            )

        # 🔵 ==== 次数副轴 ====
        count_fields = [
            ("syscr", "#9B8FBA", "Syscr Δ", "*"), ("syscw", "#A8D8EA", "Syscw Δ", "+")
        ]
        count_handles = []
        for col, color, label, marker in count_fields:
            vals = df[col].astype(float).diff().fillna(0)
            vals = vals.clip(lower=0)   # 负值归零
            ax2.plot(
                ts, vals,
                color=color, label=label, marker=marker, linewidth=1.2, markersize=2.5, alpha=0.88, linestyle="--"
            )
            count_handles.append(
                Line2D([0], [0], color=color, marker=marker, label=label, linewidth=2, linestyle="--")
            )

        handles = byte_handles + count_handles

        # 🔵 ==== Swap 背景染色 ====
        swap_status = kwargs.get("swap_status", "PASS").upper()
        match swap_status:
            case "WARN": 
                ax1.axhspan(*ax1.get_ylim(), color="#FFF5CC", alpha=0.3, zorder=-1)
                handles.append(Patch(facecolor="#FFF5CC", edgecolor="none", alpha=0.3, label="Swap WARN"))
            case "FAIL":
                ax1.axhspan(*ax1.get_ylim(), color="#FFD6D6", alpha=0.3, zorder=-1)
                handles.append(Patch(facecolor="#FFD6D6", edgecolor="none", alpha=0.3, label="Swap FAIL"))

        # 🔵 ==== 坐标轴和标题 ====
        ax1.set_ylabel("Delta (MB/interval)", fontsize=12)
        ax2.set_ylabel("Syscalls (Count/interval)", fontsize=12)
        ax1.set_xlabel("Time (s)", fontsize=12)
        ax1.set_title("I/O Timeline", fontsize=16)
        ax1.grid(True, linestyle="--", alpha=0.35, zorder=0)

        # 🔵 ==== 图例 ====
        ax1.legend(
            handles=handles,
            loc="upper right",
            fontsize=9,
            framealpha=0.6,
            facecolor="#F8F9FB",
            edgecolor="#CCCCCC"
        )

        # 🔵 ==== 展示评分 ====
        io_summary = (
            f"Grade: {kwargs['grade']}\n"
            f"Score: {kwargs['score']}\n"
            f"RW Burst: {kwargs['rw_burst_ratio']:.2%}\n"
            f"RW Idle: {kwargs['rw_idle_ratio']:.2%}\n"
            f"Swap: {swap_status}\n"
            f"SwapMax: {kwargs['swap_max_mb']} MB\n"
            f"BurstEvt: {kwargs['sys_burst_events']}\n"
        )
        if kwargs["tags"]:
            io_summary += f"Tags: {', '.join(kwargs['tags'])}"
            
        ax1.text(
            0.008, 0.98, io_summary,
            transform=ax1.transAxes,
            ha="left", va="top",
            fontsize=9,
            color="#595959",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#F8F9FB", alpha=0.48, edgecolor="none")
        )

        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

        logger.info(f"[√] 图表已保存至: {output_path}")

        return output_path


if __name__ == '__main__':
    pass
