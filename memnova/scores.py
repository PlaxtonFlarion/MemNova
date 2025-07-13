#   ____
#  / ___|  ___ ___  _ __ ___  ___
#  \___ \ / __/ _ \| '__/ _ \/ __|
#   ___) | (_| (_) | | |  __/\__ \
#  |____/ \___\___/|_|  \___||___/
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import numpy
import typing
import statistics
from scipy.stats import linregress


class Scores(object):

    # Notes: ======================== MEM ========================

    @staticmethod
    def analyze_mem_trend(values: tuple[typing.Any]) -> dict:
        if len(values) < 10:
            return {
                "trend": "Insufficient Data",
                "trend_score": 0.0,
                "jitter_index": 0.0,
                "r_squared": 0.0,
                "slope": 0.0,
                "color": "#BBBBBB"
            }

        # ==== 阈值定义 ====
        r2_threshold = 0.5
        slope_threshold = 0.01

        # ==== 抖动指数 ====
        diffs = numpy.diff(values)
        jitter_index = round(float(numpy.std(diffs)) / float(numpy.mean(values)) + 1e-6, 4)

        # ==== 线性拟合 ====
        x = numpy.arange(len(values))
        slope, intercept, r_val, _, _ = linregress(x, values)
        r_squared = round(r_val ** 2, 4)
        slope = round(slope, 4)

        # ==== 趋势判断 ====
        if r_squared < r2_threshold:
            trend = "Fluctuating ~"
            color = "#999999"
            score = 0.0
        elif slope > slope_threshold:
            trend = "Upward ↑"
            color = "#FF3333"
            score = min(round(slope * r_squared * 10, 4), 1.0)
        elif slope < -slope_threshold:
            trend = "Downward ↓"
            color = "#33CC66"
            score = -min(round(abs(slope) * r_squared * 10, 4), 1.0)
        else:
            trend = "Stable →"
            color = "#FFA500"
            score = 0.3

        return {
            "trend": trend,
            "trend_score": score,
            "jitter_index": jitter_index,
            "r_squared": r_squared,
            "slope": slope,
            "color": color
        }

    # Notes: ======================== GFX ========================

    @staticmethod
    def score_segment(
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

        # 🟩 帧延迟比例（超过理想帧耗的帧数占比）
        ideal_frame_time = 1000 / 60
        over_threshold = sum(1 for f in frames if f["duration_ms"] > ideal_frame_time)
        latency_score = 1.0 - over_threshold / len(frames)

        # 🟩 FPS 波动与平均值
        if fps_values := [f.get(fps_key) for f in frames if f.get(fps_key)]:
            fps_avg = sum(fps_values) / len(fps_values)
            fps_std = statistics.stdev(fps_values) if len(fps_values) >= 2 else 0
            fps_stability = max(1.0 - min(fps_std / 10, 1.0), 0.0)
            fps_penalty = min(fps_avg / 60, 1.0)
            fps_score = fps_stability * fps_penalty
        else:
            fps_score = 1.0

        # 🟩 滑动/拖拽区域中抖动占比（互动质量）
        if (motion_total := sum(r["end_ts"] - r["start_ts"] for r in roll_ranges + drag_ranges)) == 0:
            motion_score = 0.0
        else:
            motion_jank_overlap = sum(
                max(0, min(rj["end_ts"], rm["end_ts"]) - max(rj["start_ts"], rm["start_ts"]))
                for rm in roll_ranges + drag_ranges
                for rj in jank_ranges
            )
            motion_jank_ratio = motion_jank_overlap / (motion_total + 1e-6)
            motion_score = 1.0 - min(motion_jank_ratio, 1.0)

        # ✅ 综合得分
        final_score = (
            jank_score * 0.5 + latency_score * 0.2 + fps_score * 0.2 + motion_score * 0.1
        )
        return round(final_score, 3)

    @staticmethod
    def quality_label(score: float) -> dict:
        if score >= 0.95:
            return {
                "level": "S",
                "color": "#007E33",
                "label": "极致流畅，近乎完美"
            }
        elif score >= 0.85:
            return {
                "level": "A",
                "color": "#43A047",
                "label": "流畅稳定，表现优秀"
            }
        elif score >= 0.7:
            return {
                "level": "B",
                "color": "#F4B400",
                "label": "基本流畅，偶有波动"
            }
        elif score >= 0.55:
            return {
                "level": "C",
                "color": "#FF8C00",
                "label": "有明显卡顿，影响体验"
            }
        elif score >= 0.4:
            return {
                "level": "D",
                "color": "#FF3D00",
                "label": "严重卡顿，需要优化"
            }
        else:
            return {
                "level": "E",
                "color": "#B00020",
                "label": "极差体验，建议排查"
            }


if __name__ == '__main__':
    pass
