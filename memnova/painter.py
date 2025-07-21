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
from memnova.scores import Scores


class Painter(object):
    """绘图"""

    # Notes: ======================== MEM ========================

    @staticmethod
    async def draw_mem_metrics(
            df: "pd.DataFrame",
            output_path: str,
            *_,
            **kwargs
    ) -> str:

        df["x"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df = df.dropna(subset=["x"])
        df["num_x"] = md.date2num(df["x"])
        df["pss"] = pd.to_numeric(df["pss"], errors="coerce")
        df = df.dropna(subset=["pss"])

        # 滑动窗口平均
        window_size = max(3, len(df) // 20)
        df["pss_sliding_avg"] = df["pss"].rolling(window=window_size, min_periods=1).mean()

        # 区块分组
        df["block_id"] = (df["mode"] != df["mode"].shift()).cumsum()

        # 全局统计
        max_val, min_val, avg_val = df["pss"].max(), df["pss"].min(), df["pss"].mean()
        y_range = max_val - min_val if max_val > min_val else 1
        offset = 0.1
        y_min = max(0, min_val - offset * y_range)
        y_max = max_val + offset * y_range

        # 区块统计
        block_stats = df.groupby(["block_id", "mode"]).agg(
            start_time=("num_x", "first"),
            end_time=("num_x", "last"),
            avg_pss=("pss", "mean"),
            max_pss=("pss", "max"),
            min_pss=("pss", "min"),
            size=("pss", "size"),
        ).reset_index()

        # 判断内存趋势
        trend, trend_score, jitter, r_squared, slope, pss_color = kwargs.values()
        summary_text = (
            f"Trend: {trend}\n"
            f"Score: {trend_score:.2f}\n"
            f"Shake: {jitter:.4f}\n"
            f"Slope: {slope:.4f}"
        )

        # 配色与视觉分区
        avg_color = "#BD93F9"   # 均值线（淡紫/莫兰迪紫）
        max_color = "#FFB86C"   # 峰值线（温暖橙/沙金色）
        min_color = "#50FA7B"   # 谷值线（绿色/薄荷绿）
        # 区块配色
        fg_color = "#3386E6"
        bg_color = "#757575"
        fg_alpha = 0.15
        bg_alpha = 0.10

        # ---- 绘图 ----
        fig, ax = plt.subplots(figsize=(16, 6))
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(md.DateFormatter("%H:%M:%S"))
        ax.xaxis.set_major_locator(md.AutoDateLocator())

        # 区块底色
        for _, row in block_stats.iterrows():
            color = fg_color if row["mode"] == "FG" else bg_color
            alpha = fg_alpha if row["mode"] == "FG" else bg_alpha
            ax.fill_between(
                [row["start_time"], row["end_time"]], y_min, y_max, color=color, alpha=alpha, zorder=0
            )
            # ax.axvspan(
            #    row["start_time"], row["end_time"], color=color, alpha=alpha, zorder=0
            # )

        # 堆叠区
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

        # RSS折线
        ax.plot(df["num_x"], df["rss"], color="#FEB96B", linewidth=1.1, linestyle="--", alpha=0.75, label="RSS")
        # USS折线
        ax.plot(df["num_x"], df["uss"], color="#90B2C8", linewidth=1.1, linestyle=":", alpha=0.75, label="USS")
        # PSS主线
        ax.plot(df["num_x"], df["pss"], color=pss_color, linewidth=1.2, label="PSS")
        
        # 滑动平均
        ax.plot(
            df["num_x"], df["pss_sliding_avg"], color="#A8BFFF", linestyle="--", linewidth=0.8, alpha=0.8, label="Sliding Avg"
        )
        
        # 均值带
        ax.axhspan(
            avg_val - 0.05 * y_range, avg_val + 0.05 * y_range, color="#D0D0FF", alpha=0.25, label="Average Range"
        )
        
        # 均值/极值线
        ax.axhline(y=avg_val, linestyle=":", color=avg_color, linewidth=0.8)
        # ax.axhline(y=max_val, linestyle=":", color=max_color, linewidth=0.8)
        # ax.axhline(y=min_val, linestyle=":", color=min_color, linewidth=0.8)

        # 极值点
        ax.scatter(
            df.loc[df["pss"] == max_val, "num_x"], df.loc[df["pss"] == max_val, "pss"],
            s=60, color="#FF1D58", zorder=3, label="Max"
        )
        ax.scatter(
            df.loc[df["pss"] == min_val, "num_x"], df.loc[df["pss"] == min_val, "pss"],
            s=60, color="#009FFD", zorder=3, label="Min"
        )

        # 设置轴与样式
        # ax.set_ylim(y_min, y_max)
        ax.set_title("Memory Usage Over Time (PSS)")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("PSS (MB)")
        ax.grid(True, linestyle="--", alpha=0.4)
        plt.xticks(rotation=30)

        # 堆叠区 legend
        stack_handles = [
            Patch(facecolor=c, edgecolor="none", alpha=0.38, label=l)
            for c, l in zip(stack_colors, stack_labels)
        ]

        # 其他折线等如果需要可以用 Line2D...

        # 构造伪图例项
        line_handles = [
            Line2D([0], [0], color=pss_color, linewidth=1.2, label="PSS"),
            Line2D([0], [0], color="#FEB96B", linewidth=1.1, linestyle="--", label="RSS"),
            Line2D([0], [0], color="#90B2C8", linewidth=1.1, linestyle=":", label="USS"),
            Line2D([0], [0], color="#A8BFFF", linestyle="--", label="Sliding Avg"),
            Line2D([0], [0], color=avg_color, linestyle=":", label="PSS AVG"),
            Line2D([0], [0], marker="o", color="#FF1D58", linestyle="None", markersize=7, label="Max"),
            Line2D([0], [0], marker="o", color="#009FFD", linestyle="None", markersize=7, label="Min"),
        ]

         # === 展示图例（主图例+堆叠区图例） ===
         ax.legend(
             handles=stack_handles + line_handles,
             loc="upper right",
             fontsize=9,
             frameon=True,
             framealpha=0.3,
             facecolor="#F9F9F9",
             edgecolor="#CCCCCC"
         )

        # ====== 评分信息 ======
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
        def draw_background(ranges: list[dict], color: str, alpha: float) -> None:
            for r in ranges:
                ax1.axvspan(r["start_ts"], r["end_ts"], color=color, alpha=alpha)

        draw_background(roll_ranges, "#A2C8E6", 0.10)   # 滑动区
        draw_background(drag_ranges, "#FFD39B", 0.15)   # 拖拽区
        draw_background(jank_ranges, "#F24C4C", 0.35)   # 掉帧区

        # === 帧耗时主线 ===
        line_color = "#585858"
        ax1.plot(
            timestamps, durations,
            label="Frame Duration", color=line_color, linewidth=1.8
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
            plt.Line2D([0], [0], color="#D62728", lw=1.2, linestyle='--', label="16.67ms / 60 FPS")
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
    async def draw_io_metrics(
            metadata: dict,
            io: dict,
            rss: list,
            block: list,
            output_path: str
    ) -> str:

        _, evaluate = metadata, Scores.assess_io_score(io, block)

        fig, ax1 = plt.subplots(figsize=(16, 6))

        # === 左轴：RSS ===
        rss_times, rss_vals = [d["time_sec"] / 1000 for d in rss], [d["rss_mb"] for d in rss]

        ax1.plot(
            rss_times, rss_vals,
            color="#1F77B4", linewidth=2.0, label="RSS (MB)", marker="o", markersize=3
        )
        ax1.set_ylabel("RSS (MB)", fontsize=12, color="#1F77B4")
        ax1.tick_params(axis="y", labelcolor="#1F77B4")

        # === 右轴：IO ===
        io_lines, ax2 = [], ax1.twinx()

        def plot_io_line(series_name: str, color: str, marker: str, label: str) -> list[float]:
            if not (data := io.get(series_name, [])):
                return []
            times = [d["time_sec"] / 1000 for d in data]
            values = [d["delta"] for d in data]
            io_line = ax2.plot(
                times, values,
                linestyle="--", linewidth=1.2, marker=marker, markersize=2, color=color, label=label
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
            Line2D([0], [0], color="#7F7F7F", linewidth=2, linestyle="--", marker="|", label="Block Complete")
        ]

        # === 主图例项 ===
        ax1.legend(
            handles=legend_lines,
            loc="upper right",
            fontsize=9,
            framealpha=0.4,
            handlelength=0,
            handletextpad=0.4,
            labelspacing=0.3,
            borderpad=0.8
        )

        # === 评分信息 ===
        summary_text = (
            f"Score: {evaluate['score']} / 100\n"
            f"Grade: {evaluate['grade']}\n"
            f"Swap: {evaluate['swap_status']} ({evaluate['swap_max']} KB)\n"
            f"Page IO: {evaluate['page_io_status']} ({evaluate['page_io_peak']} KB)\n"
            f"Block IO: {evaluate['block_events']} events"
        )
        # 右上角展示评分
        ax1.text(
            0.008, 0.98, summary_text,
            transform=ax1.transAxes,
            ha="right", va="top",
            fontsize=9,
            color="#595959",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#F8F9FB", alpha=0.48, edgecolor="none")
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
    
    @staticmethod
    async def draw_io_metrics_2(
            metadata: dict,
            io: list,
            rss: list,
            block: list,
            output_path: str
    ) -> str:
    
        # 评分函数先注释掉
        # _, evaluate = metadata, Scores.assess_io_score(io, block)

        fig, ax1 = plt.subplots(figsize=(16, 6))

        # === 左轴：RSS ===
        rss_times = [d["time_sec"] / 1000 for d in rss]
        rss_vals = [d["rss_mb"] for d in rss]

        ax1.plot(
            rss_times, rss_vals,
            color="#1F77B4", linewidth=2.0, label="RSS (MB)", marker="o", markersize=3
        )
        ax1.set_ylabel("RSS (MB)", fontsize=12, color="#1F77B4")
        ax1.tick_params(axis="y", labelcolor="#1F77B4")

        # === 右轴：IO ===
        ax2 = ax1.twinx()

        # 显示（io.read_bytes/io.write_bytes），按 counter_name 分组
        df = pd.DataFrame(io)
        io_colors = {
            "io.read_bytes": "#FF7F0E",
            "io.write_bytes": "#2CA02C",
            "io.rchar": "#8C564B",
            "io.wchar": "#9467BD",
        }
        io_markers = {
            "io.read_bytes": "s",
            "io.write_bytes": "^",
            "io.rchar": "d",
            "io.wchar": "x",
        }

        for name, group in df.groupby("counter_name"):
            times = group["time_ms"] / 1000
            value = group["value"].diff().fillna(0)
            ax2.plot(
                times, value,
                linestyle="--", linewidth=1.2, marker=io_markers.get(name, "o"),
                markersize=2, color=io_colors.get(name, "#888888"), label=name
            )

        ax2.set_ylabel("IO Delta (Bytes)", fontsize=12)
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
            Line2D([0], [0], color="#FF7F0E", linestyle="--", marker="s", label="io.read_bytes"),
            Line2D([0], [0], color="#2CA02C", linestyle="--", marker="^", label="io.write_bytes"),
            Line2D([0], [0], color="#8C564B", linestyle="--", marker="d", label="io.rchar"),
            Line2D([0], [0], color="#9467BD", linestyle="--", marker="x", label="io.wchar"),
        ]

        ax1.legend(
            handles=legend_lines,
            loc="upper left",
            fontsize=9,
            framealpha=0.4,
            handlelength=1.5,
            handletextpad=0.4,
            labelspacing=0.3,
            borderpad=0.8
        )

        # === 图表设置 ===
        ax1.set_xlabel("Time (seconds)", fontsize=12)
        plt.title("I/O + RSS Timeline", fontsize=16)
        plt.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

        logger.info(f"[√] 图表已保存至: {output_path}")

        return output_path


if __name__ == '__main__':
    pass
