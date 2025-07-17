#   ____       _       _
#  |  _ \ __ _(_)_ __ | |_ ___ _ __
#  | |_) / _` | | '_ \| __/ _ \ '__|
#  |  __/ (_| | | | | | ||  __/ |
#  |_|   \__,_|_|_| |_|\__\___|_|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import pandas as pd
import matplotlib.dates as md
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from loguru import logger
from datetime import datetime
from memnova.scores import Scores


class Painter(object):
    """绘图"""

    # Notes: ======================== MEM ========================

    @staticmethod
    async def draw_mem_metrics(
            data_list: list[tuple],
            output_path: str
    ) -> str:

        df = pd.DataFrame(
            data_list, 
            columns=["timestamp", "rss", "pss", "uss", "opss", "activity", "adj", "foreground"]
        )
        df["x"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df = df.dropna(subset=["x"])
        df["num_x"] = md.date2num(df["x"])
        df["pss"] = pd.to_numeric(df["pss"], errors="coerce")
        df = df.dropna(subset=["pss"])

        # 滑动窗口平均
        window_size = max(3, len(df)//20)
        df["pss_sliding_avg"] = df["pss"].rolling(window=window_size, min_periods=1).mean()

        # 全局统计
        max_val, min_val, avg_val = df["pss"].max(), df["pss"].min(), df["pss"].mean()
        y_range = max_val - min_val if max_val > min_val else 1
        offset = 0.1
        y_min = max(0, min_val - offset * y_range)
        y_max = max_val + offset * y_range

        # 连续区块分组（只要 foreground 变就换一块）
        block_flag: "pd.Series" = (df["foreground"] != df["foreground"].shift())
        df["block_id"] = block_flag.cumsum()

        # 区块统计
        block_stats = df.groupby(["block_id", "foreground"]).agg(
            start_time=("num_x", "first"),
            end_time=("num_x", "last"),
            avg_pss=("pss", "mean"),
            max_pss=("pss", "max"),
            min_pss=("pss", "min"),
            size=("pss", "size"),
        ).reset_index()

        # 判断内存趋势
        result = Scores.analyze_mem_trend(df["pss"])

        line_color = result["color"]
        trend_label = result["trend"]
        jitter = result["jitter_index"]
        trend_score = result["trend_score"]

        # 区块配色
        fg_color = "#3386E6"
        bg_color = "#757575"
        fg_alpha = 0.22
        bg_alpha = 0.18

        # ---- 绘图 ----
        fig, ax = plt.subplots(figsize=(16, 6))
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(md.DateFormatter("%H:%M:%S"))
        ax.xaxis.set_major_locator(md.AutoDateLocator())

        # 区块底色
        for _, row in block_stats.iterrows():
            color = fg_color if row["foreground"] == "前台" else bg_color
            alpha = fg_alpha if row["foreground"] == "前台" else bg_alpha
            ax.axvspan(row["start_time"], row["end_time"], color=color, alpha=alpha, zorder=0)

        # 主线
        ax.plot(df["num_x"], df["pss"], color="#4074B4", linewidth=1.2, label="PSS")
        # 滑动平均
        ax.plot(df["num_x"], df["pss_sliding_avg"], color="#3333AA", linestyle="--", linewidth=0.8, alpha=0.8, label="Sliding Avg") 
        # 均值带
        ax.axhspan(avg_val - 0.05 * y_range, avg_val + 0.05 * y_range, color="#D0D0FF", alpha=0.25, label="Average Range")
        # 均值/极值线
        ax.axhline(y=avg_val, linestyle=":", color="#6666CC", linewidth=0.8)
        ax.axhline(y=max_val, linestyle=":", color="#FF4B00", linewidth=0.8)
        ax.axhline(y=min_val, linestyle=":", color="#00FF85", linewidth=0.8)

        # 极值点
        ax.scatter(
            df.loc[df["pss"] == max_val, "num_x"], [max_val], s=60, color="#FF1D58", zorder=3, label="Max"
        )
        ax.scatter(
            df.loc[df["pss"] == min_val, "num_x"], [min_val], s=60, color="#009FFD", zorder=3, label="Min"
        )

        # 设置轴与样式
        ax.set_ylim(y_min, y_max)
        ax.set_title("Memory Usage Over Time (PSS)")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("PSS (MB)")
        ax.grid(True, linestyle="--", alpha=0.4)
        plt.xticks(rotation=30)

        # 构造伪图例项（作为文字说明）
        legend_items = [
            Line2D([0], [0], color="none", label=f"Trend: {trend_label}"),
            Line2D([0], [0], color="none", label=f"Score: {trend_score:.2f}"),
            Line2D([0], [0], color="none", label=f"Jitter: {jitter:.4f}"),
            Line2D([0], [0], color="#FF4B00", label=f"PSS MAX: {max_val:.2f} MB"),
            Line2D([0], [0], color="#6666CC", label=f"PSS AVG: {avg_val:.2f} MB"),
            Line2D([0], [0], color="#00FF85", label=f"PSS MIN: {min_val:.2f} MB"),
            Line2D([0], [0], color="#3333AA", label=f"Sliding Avg"),
            Line2D([0], [0], color=line_color, label="PSS Line")
        ]

        # 展示图例
        ax.legend(
            handles=legend_items,
            loc="upper left",
            fontsize=9,
            frameon=True,
            framealpha=0.3,
            facecolor="#F9F9F9",
            edgecolor="#CCCCCC"
        )

        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

        logger.info(f"[√] 图表已保存至: {output_path}")

        return output_path

    # Notes: ======================== GFX ========================

    @staticmethod
    async def draw_gfx_metrics(
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

        timestamps = [f["timestamp_ms"] for f in raw_frames]
        durations = [f["duration_ms"] for f in raw_frames]
        fps_sys = [f["fps"] for f in vsync_sys]
        fps_app = [f["fps"] for f in vsync_app]

        fig, ax1 = plt.subplots(figsize=(16, 6))

        # === 背景区块绘制 ===
        def draw_background(ranges: list[dict], color: str):
            for r in ranges:
                ax1.axvspan(r["start_ts"], r["end_ts"], color=color, alpha=0.12)

        draw_background(roll_ranges, "#A2C8E6")   # 滑动
        draw_background(drag_ranges, "#FFD39B")   # 拖拽
        draw_background(jank_ranges, "#F5A9A9")   # 掉帧

        # === 帧耗时主线 ===
        line_color = "#585858"
        ax1.plot(
            timestamps, durations, label="Frame Duration", color=line_color, linewidth=1.8
        )

        # === 多帧率基准线（不进图例，右侧标注） ===
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
            ax1.axhline(ms, linestyle="--", linewidth=1.2, color=fps_colors[label])
            ax1.text(
                x=0.003,
                y=ms,
                s=label,
                transform=ax1.get_yaxis_transform(),
                color=fps_colors[label],
                fontsize=8,
                verticalalignment="bottom",
                horizontalalignment="left"
            )

        # === FPS 统计信息 ===
        max_sys = max(fps_sys, default=0)
        avg_sys = sum(fps_sys) / len(fps_sys) if fps_sys else 0
        max_app = max(fps_app, default=0)
        avg_app = sum(fps_app) / len(fps_app) if fps_app else 0

        fps_summary = (
            f"SYS: Avg {avg_sys:.1f} / Max {max_sys:.1f}\n"
            f"APP: Avg {avg_app:.1f} / Max {max_app:.1f}"
        )

        # === 自定义图例（颜色区块 + 主线 + 60 FPS）===
        legend_elements = [
            Patch(facecolor="#A2C8E6", edgecolor="none", label="Roll Area"),
            Patch(facecolor="#FFD39B", edgecolor="none", label="Drag Area"),
            Patch(facecolor="#F5A9A9", edgecolor="none", label="Jank Area"),
            plt.Line2D([0], [0], color=line_color, lw=2, label="Frame Duration"),
            plt.Line2D([0], [0], color="#D62728", lw=1.2, linestyle='--', label="16.67ms / 60 FPS"),
        ]

        ax1.legend(
            handles=legend_elements,
            loc="upper right",
            fontsize=8,
            title=fps_summary,
            title_fontsize=9,
            frameon=True,
            facecolor="#FAFAFA",
            edgecolor="#CCCCCC"
        )

        # === 图表样式 ===
        ax1.set_title("Frame Duration Over Time")
        ax1.set_xlabel("Timestamp (ms)")
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
    async def draw_ion_metrics(
            metadata: dict,
            io: dict,
            rss: list,
            block: list,
            output_path: str
    ) -> str:

        _ = metadata

        evaluate = Scores.assess_io_score(io, block)

        fig, ax1 = plt.subplots(figsize=(16, 6))

        # === 左轴：RSS ===
        rss_times = [d["time_sec"] for d in rss]
        rss_vals = [d["rss_mb"] for d in rss]
        ax1.plot(
            rss_times, rss_vals, color="#1F77B4", linewidth=2.0, label="RSS (MB)", marker="o", markersize=3
        )
        ax1.set_ylabel("RSS (MB)", fontsize=12, color="#1F77B4")
        ax1.tick_params(axis="y", labelcolor="#1F77B4")

        # === 右轴：IO ===
        ax2 = ax1.twinx()
        io_lines = []

        def plot_io_line(series_name, color, marker, label):
            if not (data := io.get(series_name, [])):
                return []
            times = [d["time_sec"] for d in data]
            values = [d["delta"] for d in data]
            io_line = ax2.plot(
                times, values, linestyle="--", linewidth=1.2, marker=marker, markersize=2, color=color, label=label
            )
            io_lines.append(io_line)
            return values

        all_io_vals = []
        all_io_vals += plot_io_line("pgpgin", "#FF7F0E", "s", "Page In (KB)") or []
        all_io_vals += plot_io_line("pgpgout", "#2CA02C", "^", "Page Out (KB)") or []
        all_io_vals += plot_io_line("pswpin", "#D62728", "v", "Swap In (KB)") or []
        all_io_vals += plot_io_line("pswpout", "#9467BD", "x", "Swap Out (KB)") or []

        ax2.set_ylabel("Page / Swap Delta (KB)", fontsize=12)
        ax2.tick_params(axis="y")

        # === Block IO 垂线 ===
        for event in block:
            t = event["time_sec"]
            if event["event"] == "block_rq_issue":
                ax1.axvline(x=t, color="#E377C2", linestyle="--", alpha=0.3)
            elif event["event"] == "block_rq_complete":
                ax1.axvline(x=t, color="#7F7F7F", linestyle="--", alpha=0.3)

        # === 主图例项 ===
        legend_lines = [
            Line2D([0], [0], color="#1F77B4", linewidth=2, marker="o", label="RSS (MB)"),
            Line2D([0], [0], color="#FF7F0E", linestyle="--", marker="s", label="Page In"),
            Line2D([0], [0], color="#2CA02C", linestyle="--", marker="^", label="Page Out"),
            Line2D([0], [0], color="#D62728", linestyle="--", marker="v", label="Swap In"),
            Line2D([0], [0], color="#9467BD", linestyle="--", marker="x", label="Swap Out"),
            Line2D([0], [0], color="#E377C2", linewidth=2, linestyle="--", marker="|", label="Block Issue"),
            Line2D([0], [0], color="#7F7F7F", linewidth=2, linestyle="--", marker="|", label="Block Complete"),
        ]

        # === 评估信息（伪图例项） ===
        summary_lines = [
            f"Score: {evaluate['score']} / 100",
            f"Grade: {evaluate['grade']}",
            f"Swap: {evaluate['swap_status']} ({evaluate['swap_max']} KB)",
            f"Page IO: {evaluate['page_io_status']} ({evaluate['page_io_peak']} KB)",
            f"Block IO: {evaluate['block_events']} events"
        ]
        summary_handles = [
            Line2D([0], [0], color="none", label=line) for line in summary_lines
        ]

        # === 合并图例：主图例项 + 评估项 ===
        ax1.legend(
            handles=legend_lines + summary_handles,
            loc="upper left",
            fontsize=9,
            framealpha=0.4,
            handlelength=0,
            handletextpad=0.4,
            labelspacing=0.3,
            borderpad=0.8
        )

        # === 图表设置 ===
        ax1.set_xlabel("Time (seconds)", fontsize=12)
        plt.title("RSS + I/O Timeline", fontsize=16)
        plt.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

        logger.info(f"[√] 图表已保存至: {output_path}")

        return output_path


if __name__ == '__main__':
    pass
