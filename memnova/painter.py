#   ____       _       _
#  |  _ \ __ _(_)_ __ | |_ ___ _ __
#  | |_) / _` | | '_ \| __/ _ \ '__|
#  |  __/ (_| | | | | | ||  __/ |
#  |_|   \__,_|_|_| |_|\__\___|_|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import matplotlib.dates as md
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from loguru import logger
from datetime import datetime
from memnova.scores import Scores


class Painter(object):

    # Notes: ======================== MEM ========================

    @staticmethod
    async def draw_memory_enhanced(data_list: list[tuple], output_path: str) -> str:
        timestamp, _, pss, *_ = list(zip(*data_list))

        timestamps = md.date2num(
            [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in timestamp]
        )

        # 计算统计值
        max_val = max(pss)
        min_val = min(pss)
        avg_val = sum(pss) / len(pss)
        y_range = max_val - min_val if max_val > min_val else 1
        offset = 0.1
        y_min = max(0, min_val - offset * y_range)
        y_max = max_val + offset * y_range

        # 判断内存趋势
        result = Scores.analyze_mem_trend(pss)

        line_color = result["color"]
        trend_label = result["trend"]
        jitter = result["jitter_index"]
        trend_score = result["trend_score"]

        fig, ax = plt.subplots(figsize=(16, 6))

        # 设置 x 轴为时间格式
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(md.DateFormatter("%H:%M:%S"))
        ax.xaxis.set_major_locator(md.AutoDateLocator())

        # 主折线
        ax.plot(timestamps, pss, color=line_color, linewidth=1.2, label="PSS")

        # 均值带
        ax.axhspan(
            avg_val - 0.05 * y_range, avg_val + 0.05 * y_range, color="#D0D0FF", alpha=0.3, label="Average Range"
        )
        # 均值线
        ax.axhline(y=avg_val, linestyle=":", color="#6666CC", linewidth=0.8)

        # 最大值标注
        ax.axhline(y=max_val, linestyle=":", color="#FF4B00", linewidth=0.8)

        # 最小值标注
        ax.axhline(y=min_val, linestyle=":", color="#00FF85", linewidth=0.8)

        # 滑动窗口平均线
        window_size = max(3, len(pss) // 20)
        sliding_avg = [
            sum(pss[max(0, i - window_size):i + 1]) / (i - max(0, i - window_size) + 1)
            for i in range(len(pss))
        ]
        ax.plot(
            timestamps, sliding_avg,
            color="#3333AA",
            linestyle="--",
            linewidth=0.5,
            alpha=0.8,
            label="Sliding Avg"
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
    async def draw_frame_timeline(
            frames: list[dict],
            roll_ranges: list[dict],
            drag_ranges: list[dict],
            jank_ranges: list[dict],
            vsync_sys: list[dict],
            vsync_app: list[dict],
            output_path: str
    ) -> str:

        timestamps = [f["timestamp_ms"] for f in frames]
        durations = [f["duration_ms"] for f in frames]
        fps_sys = [f["fps_sys"] for f in vsync_sys]
        fps_app = [f["fps_app"] for f in vsync_app]

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



if __name__ == '__main__':
    pass
