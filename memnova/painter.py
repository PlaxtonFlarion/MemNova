#   ____       _       _
#  |  _ \ __ _(_)_ __ | |_ ___ _ __
#  | |_) / _` | | '_ \| __/ _ \ '__|
#  |  __/ (_| | | | | | ||  __/ |
#  |_|   \__,_|_|_| |_|\__\___|_|
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
from loguru import logger
from memnova.scores import Scores


class Painter(object):
    """Painter"""

    # Notes: ======================== MEM ========================

    @staticmethod
    def draw_mem_metrics(
            union_data_list: list[tuple],
            output_path: str,
            *_,
            **kwargs
    ) -> str:

        df = pd.DataFrame(
            union_data_list, columns=[
                "timestamp", "pss", "rss", "uss", "activity", "adj", "mode",
                "native_heap", "dalvik_heap", "java_heap", "graphics",
            ]
        )

        df["x"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df = df.dropna(subset=["x"])
        df["num_x"] = md.date2num(df["x"])
        df["pss"] = pd.to_numeric(df["pss"], errors="coerce")
        df = df.dropna(subset=["pss"])

        # ==== 滑动窗口平均 ====
        window_size = max(3, len(df) // 20)
        df["pss_sliding_avg"] = df["pss"].rolling(window=window_size, min_periods=1).mean()

        # ==== 前后台区块分组 ====
        df["block_id"] = (df["mode"] != df["mode"].shift()).cumsum()

        # ==== 全局统计 ====
        max_val, min_val, avg_val = df["pss"].max(), df["pss"].min(), df["pss"].mean()
        y_range = max_val - min_val if max_val > min_val else 1
        offset = 0.1
        y_min = max(0, min_val - offset * y_range)
        y_max = max_val + offset * y_range

        # ==== 区块统计 ====
        block_stats = df.groupby(["block_id", "mode"]).agg(
            start_time=("num_x", "first"),
            end_time=("num_x", "last"),
            avg_pss=("pss", "mean"),
            max_pss=("pss", "max"),
            min_pss=("pss", "min"),
            size=("pss", "size"),
        ).reset_index()

        # ==== 判断内存趋势 ====
        trend, trend_score, jitter, r_squared, slope, pss_color = kwargs.values()
        summary_text = (
            f"Trend: {trend}\n"
            f"Score: {trend_score:.2f}\n"
            f"Shake: {jitter:.4f}\n"
            f"Slope: {slope:.4f}"
        )

        # ==== 配色与视觉分区 ====
        avg_color = "#BD93F9"   # 均值
        max_color = "#FF1D58"   # 峰值
        min_color = "#009FFD"   # 谷值
        # ==== 前后台区块配色 ====
        fg_color = "#3386E6"
        bg_color = "#757575"
        fg_alpha = 0.15
        bg_alpha = 0.10

        # ==== 绘图 ====
        fig, ax = plt.subplots(figsize=(16, 6))
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(md.DateFormatter("%H:%M:%S"))
        ax.xaxis.set_major_locator(md.AutoDateLocator())

        # ==== 前后台区块底色 ====
        for _, row in block_stats.iterrows():
            color = fg_color if row["mode"] == "FG" else bg_color
            alpha = fg_alpha if row["mode"] == "FG" else bg_alpha
            ax.fill_between(
                [row["start_time"], row["end_time"]], y_min, y_max, color=color, alpha=alpha, zorder=0
            )

        # ==== 堆叠区 ====
        stack_colors = ["#FFD6E0", "#D4E7FF", "#CAE7E1"]
        stack_labels = ["Native Heap", "Dalvik Heap", "Graphics"]
        ax.stackplot(
            df["num_x"],
            df["native_heap"],
            df["dalvik_heap"],
            df["graphics"],
            colors=stack_colors,
            alpha=0.38,
            labels=stack_labels
        )

        # ==== PSS主线 ====
        ax.plot(df["num_x"], df["pss"], color=pss_color, linewidth=1.2, label="PSS")
        # ==== RSS折线 ====
        ax.plot(df["num_x"], df["rss"], color="#FEB96B", linewidth=1.1, linestyle="--", alpha=0.75, label="RSS")
        # ==== USS折线 ====
        ax.plot(df["num_x"], df["uss"], color="#90B2C8", linewidth=1.1, linestyle=":", alpha=0.75, label="USS")
        
        # ==== 滑动平均 ====
        ax.plot(
            df["num_x"], df["pss_sliding_avg"],
            color="#A8BFFF", linestyle="--", linewidth=0.8, alpha=0.8, label="Sliding Avg"
        )

        # ==== 均值带 ====
        ax.axhspan(
            avg_val - 0.05 * y_range, avg_val + 0.05 * y_range, color="#D0D0FF", alpha=0.25, label="Average Range"
        )

        # ==== 均值线 ====
        ax.axhline(y=avg_val, linestyle=":", color=avg_color, linewidth=0.8)

        # ==== 极值点 ====
        ax.scatter(
            df.loc[df["pss"] == max_val, "num_x"], df.loc[df["pss"] == max_val, "pss"],
            s=60, color=max_color, zorder=3, label="Max"
        )
        ax.scatter(
            df.loc[df["pss"] == min_val, "num_x"], df.loc[df["pss"] == min_val, "pss"],
            s=60, color=min_color, zorder=3, label="Min"
        )

        # ==== 设置轴与样式 ====
        ax.set_title("Memory Usage Over Time (PSS)")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("PSS (MB)")
        ax.grid(True, linestyle="--", alpha=0.4)
        plt.xticks(rotation=30)

        # ==== 堆叠区 legend ====
        stack_handles = [
            Patch(facecolor=c, edgecolor="none", alpha=0.38, label=l)
            for c, l in zip(stack_colors, stack_labels)
        ]

        # ==== 构造伪图例项 ====
        line_handles = [
            Line2D([0], [0], color=pss_color, linewidth=1.2, label="PSS"),
            Line2D([0], [0], color="#FEB96B", linewidth=1.1, linestyle="--", label="RSS"),
            Line2D([0], [0], color="#90B2C8", linewidth=1.1, linestyle=":", label="USS"),
            Line2D([0], [0], color="#A8BFFF", linestyle="--", label="Sliding Avg"),
            Line2D([0], [0], color=avg_color, linestyle=":", label="PSS AVG"),
            Line2D([0], [0], marker="o", color=max_color, linestyle="None", markersize=7, label="Max"),
            Line2D([0], [0], marker="o", color=min_color, linestyle="None", markersize=7, label="Min"),
        ]

        # ==== 展示图例（主图例+堆叠区图例） ====
        ax.legend(
            handles=stack_handles + line_handles,
            loc="upper right",
            fontsize=9,
            frameon=True,
            framealpha=0.3,
            facecolor="#F9F9F9",
            edgecolor="#CCCCCC"
        )

        # ==== 评分信息 ====
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
            metadata: dict,
            raw_frames: list[dict],
            vsync_sys: list[dict],
            vsync_app: list[dict],
            roll_ranges: list[dict],
            drag_ranges: list[dict],
            jank_ranges: list[dict],
            output_path: str
    ) -> str:

        _ = metadata

        timestamps = [f["timestamp_ms"] / 1000 for f in raw_frames]
        durations = [f["duration_ms"] for f in raw_frames]
        fps_sys = [f["fps"] for f in vsync_sys]
        fps_app = [f["fps"] for f in vsync_app]

        # ==== 计算帧耗时平均和最大值 ====
        avg_dur = np.mean(durations) if durations else 0
        max_dur = np.max(durations) if durations else 0

        fig, ax1 = plt.subplots(figsize=(16, 6))

        # ==== 背景区块绘制 ====
        def draw_background(ranges: list[dict], color: str, alpha: float) -> None:
            for r in ranges:
                ax1.axvspan(r["start_ts"] / 1000, r["end_ts"] / 1000, color=color, alpha=alpha)

        draw_background(roll_ranges, "#A2C8E6", 0.10)   # 滑动区
        draw_background(drag_ranges, "#FFD39B", 0.15)   # 拖拽区
        draw_background(jank_ranges, "#F24C4C", 0.35)   # 掉帧区

        # ==== 帧耗时主线 ====
        line_color = "#585858"
        ax1.plot(
            timestamps, durations,
            label="Frame Duration", color=line_color, linewidth=1.2
        )
        # ==== 平均线 ====
        ax1.axhline(avg_dur, linestyle=":", linewidth=1.3, color="#448AFF", alpha=0.88, label="Avg Duration")
        # ==== 最高线 ====
        ax1.axhline(max_dur, linestyle="--", linewidth=1.1, color="#FF4081", alpha=0.88, label="Max Duration")

        # ==== 多帧率基准线 ====
        fps_marks = {
            "120 FPS": 1000 / 120,
            "90 FPS": 1000 / 90,
            "60 FPS": 1000 / 60,
            "45 FPS": 1000 / 45,
            "30 FPS": 1000 / 30,
        }
        fps_colors = {
            "120 FPS": "#BBBBBB",
            "90 FPS": "#999999",
            "60 FPS": "#FF0000",  # 红色警戒线
            "45 FPS": "#999999",
            "30 FPS": "#BBBBBB",
        }

        for label, ms in fps_marks.items():
            ax1.axhline(ms, linestyle="--", linewidth=1.0, color=fps_colors[label])

        # ==== FPS 统计信息 ====
        max_sys = max(fps_sys, default=0)
        avg_sys = sum(fps_sys) / len(fps_sys) if fps_sys else 0
        max_app = max(fps_app, default=0)
        avg_app = sum(fps_app) / len(fps_app) if fps_app else 0

        fps_summary = (
            f"SYS: Avg {avg_sys:.1f} / Max {max_sys:.1f}\n"
            f"APP: Avg {avg_app:.1f} / Max {max_app:.1f}"
        )

        # ==== 自定义图例（颜色区块 + 主线 + 60 FPS）====
        legend_elements = [
            Line2D([0], [0], color=line_color, lw=1.2, label="Frame Duration"),
            Line2D([0], [0], color="#D62728", lw=1.0, linestyle='--', label="16.67ms / 60 FPS"),
            Line2D([0], [0], color="#448AFF", lw=1.3, linestyle=":", label=f"Avg Duration: {avg_dur:.1f}ms"),
            Line2D([0], [0], color="#FF4081", lw=1.1, linestyle="--", label=f"Max Duration: {max_dur:.1f}ms"),
            Line2D([0], [0], color="#999999", lw=1.0, linestyle='--', label="45 FPS / 90 FPS"),
            Line2D([0], [0], color="#BBBBBB", lw=1.0, linestyle='--', label="30 FPS / 120 FPS"),
            Patch(facecolor="#A2C8E6", edgecolor="none", label="Scroll Region"),
            Patch(facecolor="#FFD39B", edgecolor="none", label="Drag Region"),
            Patch(facecolor="#F5A9A9", edgecolor="none", label="Jank Region"),
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

        # ==== 展示FPS ====
        ax1.text(
            0.008, 0.98, fps_summary,
            transform=ax1.transAxes,
            ha="left", va="top",
            fontsize=9,
            color="#595959",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#F8F9FB", alpha=0.48, edgecolor="none")
        )

        # ==== 图表样式 ====
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
            metadata: dict,
            union_data_list: list[tuple],
            output_path: str
    ) -> str:

        df = pd.DataFrame(
            union_data_list, columns=[
                "rchar", "wchar", "syscr", "syscw", "read_bytes", "write_bytes"
            ]
        )

        # ==== 获取评分 ====
        _, evaluate = metadata, Scores.analyze_io_score(df)

        io_summary = (
            f"Grade: {evaluate['grade']}\n"
            f"Score: {evaluate['score']}\n"
        )

        fig, ax1 = plt.subplots(figsize=(16, 6))
        ax2 = ax1.twinx()

        # ==== 时间轴 ====
        ts = pd.to_datetime(df["timestamp"])
        x = (ts - ts.iloc[0]).dt.total_seconds()

        # ==== 字节量主轴（MB） ====
        byte_fields = [
            ("read_bytes", "#4F8CFD", "Read Bytes Δ", "o"),
            ("write_bytes", "#6BE675", "Write Bytes Δ", "^"),
            ("rchar", "#F09F3E", "RChar Δ", "s"),
            ("wchar", "#F46C9D", "WChar Δ", "x"),
        ]
        byte_handles = []
        for col, color, label, marker in byte_fields:
            vals = df[col].astype(float).diff().fillna(0)
            vals = vals.clip(lower=0)   # 负值归零
            ax1.plot(x, vals, color=color, label=label, marker=marker, linewidth=1.4, markersize=2.5, alpha=0.95)
            byte_handles.append(Line2D([0], [0], color=color, marker=marker, label=label, linewidth=2))

        # ==== 次数副轴 ====
        count_fields = [
            ("syscr", "#9B8FBA", "Syscr Δ", "*"),
            ("syscw", "#A8D8EA", "Syscw Δ", "+"),
        ]
        count_handles = []
        for col, color, label, marker in count_fields:
            vals = df[col].astype(float).diff().fillna(0)
            vals = vals.clip(lower=0)   # 负值归零
            ax2.plot(x, vals, color=color, label=label, marker=marker, linewidth=1.5, markersize=2.8, alpha=0.88, linestyle="--")
            count_handles.append(Line2D([0], [0], color=color, marker=marker, label=label, linewidth=2, linestyle="--"))

        # ==== 坐标轴和标题 ====
        ax1.set_ylabel("Delta (MB/s)", fontsize=12)
        ax2.set_ylabel("Syscalls (Count/s)", fontsize=12)
        ax1.set_xlabel("Time (s)", fontsize=12)
        ax1.set_title("I/O Timeline", fontsize=16)
        ax1.grid(True, linestyle="--", alpha=0.35, zorder=0)

        # ==== 图例 ====
        handles = byte_handles + count_handles
        ax1.legend(
            handles=handles,
            loc="upper right",
            fontsize=9,
            framealpha=0.6,
            facecolor="#F8F9FB",
            edgecolor="#CCCCCC"
        )

        # ==== 展示评分 ====
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
