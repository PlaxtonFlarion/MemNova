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
        if score >= 0.93:
            return {
                "level": "S",
                "color": "#005822",
                "label": "极致流畅，近乎完美"
            }
        elif score >= 0.80:
            return {
                "level": "A",
                "color": "#1B5E20",
                "label": "稳定流畅，表现优秀"
            }
        elif score >= 0.68:
            return {
                "level": "B",
                "color": "#D39E00",
                "label": "基本流畅，偶有波动"
            }
        elif score >= 0.50:
            return {
                "level": "C",
                "color": "#E65100",
                "label": "有明显卡顿，影响体验"
            }
        elif score >= 0.35:
            return {
                "level": "D",
                "color": "#C62828",
                "label": "严重卡顿，需要优化"
            }
        else:
            return {
                "level": "E",
                "color": "#7B1FA2",
                "label": "极差体验，建议排查"
            }

    # Notes: ======================== I/O ========================

    @staticmethod
    def assess_io_score(
            io: dict,
            block: list,
            swap_io_threshold: float = 10.0,
            page_io_peak_threshold: float = 100.0,
            swap_active_ratio_threshold: float = 0.2
    ) -> dict:

        result = {
            "swap_status": "PASS",
            "swap_max": 0.0,
            "swap_events": 0,
            "swap_ratio": 0.0,
            "page_io_status": "PASS",
            "page_io_peak": 0.0,
            "page_io_std": 0.0,
            "block_events": len(block),
            "tags": [],
            "risk": [],
            "score": 100,
            "grade": "S"
        }

        penalties = []
        tags = []

        # Swap IO
        swap_vals = []
        swap_times = set()
        for k in ("pswpin", "pswpout"):
            for d in io.get(k, []):
                v = float(d.get("delta", 0))
                t = float(d.get("time_sec", 0))
                if v > 0:
                    swap_vals.append(v)
                    swap_times.add(round(t, 1))

        if swap_vals:
            max_swap = max(swap_vals)
            ratio = len(swap_times) / max(len(io.get("pgpgin", [])), 1)
            result["swap_max"] = round(max_swap, 2)
            result["swap_events"] = len(swap_vals)
            result["swap_ratio"] = round(ratio, 2)
            if max_swap > swap_io_threshold:
                result["swap_status"] = "FAIL"
                penalties.append(20)
                result["risk"].append("swap_peak")
                tags.append("high_swap")
            if ratio > swap_active_ratio_threshold:
                result["swap_status"] = "FAIL"
                penalties.append(10)
                result["risk"].append("swap_ratio")
                tags.append("swap_active")

        # Page IO
        page_vals = []
        for k in ("pgpgin", "pgpgout"):
            page_vals += [float(d.get("delta", 0)) for d in io.get(k, [])]
        if page_vals:
            peak = max(page_vals)
            std = numpy.std(page_vals)
            result["page_io_peak"] = round(peak, 2)
            result["page_io_std"] = round(std, 2)
            if peak > page_io_peak_threshold:
                result["page_io_status"] = "FAIL"
                penalties.append(10)
                result["risk"].append("page_io_peak")
                tags.append("high_page_io")

        score = max(100 - sum(penalties), 0)
        result["score"], result["tags"] = score, tags

        if score >= 95:
            result["grade"] = "S"
        elif score >= 90:
            result["grade"] = "A"
        elif score >= 80:
            result["grade"] = "B"
        elif score >= 70:
            result["grade"] = "C"
        elif score >= 60:
            result["grade"] = "D"
        else:
            result["grade"] = "E"

        return result


if __name__ == '__main__':
    pass
