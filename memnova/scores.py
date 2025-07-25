#   ____
#  / ___|  ___ ___  _ __ ___  ___
#  \___ \ / __/ _ \| '__/ _ \/ __|
#   ___) | (_| (_) | | |  __/\__ \
#  |____/ \___\___/|_|  \___||___/
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import typing
import statistics
import numpy as np
import pandas as pd
from scipy.stats import linregress


class Scores(object):

    # Workflow: ======================== MEM ========================

    @staticmethod
    def analyze_mem_score(values: tuple[typing.Any]) -> dict:

        if len(values) < 10:
            return {
                "trend": "Insufficient Data",
                "trend_score": 0.0,
                "jitter_index": 0.0,
                "r_squared": 0.0,
                "slope": 0.0,
                "color": "#BBBBBB"
            }

        # 🟨 ==== 阈值定义 ====
        r2_threshold = 0.5
        slope_threshold = 0.01

        # 🟨 ==== 抖动指数 ====
        diffs = np.diff(values)
        jitter_index = round(float(np.std(diffs)) / float(np.mean(values)) + 1e-6, 4)

        # 🟨 ==== 线性拟合 ====
        x = np.arange(len(values))
        slope, intercept, r_val, _, _ = linregress(x, values)
        r_squared = round(r_val ** 2, 4)
        slope = round(slope, 4)

        # 🟨 ==== 趋势判断 ====
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

    # Workflow: ======================== GFX ========================

    @staticmethod
    def analyze_gfx_score(
            frames: list[dict],
            roll_ranges: list[dict],
            drag_ranges: list[dict],
            jank_ranges: list[dict],
            fps_key: str
    ) -> typing.Optional[dict]:

        if len(frames) < 5:
            return None

        if (duration := frames[-1]["timestamp_ms"] - frames[0]["timestamp_ms"]) <= 0:
            return None

        # 🟩 ==== Jank 比例 ====
        jank_total = sum(r["end_ts"] - r["start_ts"] for r in jank_ranges)
        jank_score = 1.0 - min(jank_total / duration, 1.0)

        # 🟩 ==== 帧延迟比例 ====
        ideal_frame_time = 1000 / 60
        over_threshold = sum(1 for f in frames if f["duration_ms"] > ideal_frame_time)
        latency_score = 1.0 - over_threshold / len(frames)

        # 🟩 ==== FPS 波动与平均值 ====
        if fps_values := [f.get(fps_key) for f in frames if f.get(fps_key)]:
            fps_avg = sum(fps_values) / len(fps_values)
            fps_std = statistics.stdev(fps_values) if len(fps_values) >= 2 else 0
            fps_stability = max(1.0 - min(fps_std / 10, 1.0), 0.0)
            fps_penalty = min(fps_avg / 60, 1.0)
            fps_score = fps_stability * fps_penalty
        else:
            fps_score = 1.0

        # 🟩 ==== 滑动/拖拽区域中抖动占比 ====
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

        # 🟩 ==== 综合得分 ====
        final_score = round(
            (jank_score * 0.5 + latency_score * 0.2 + fps_score * 0.2 + motion_score * 0.1), 3
        )

        if final_score >= 0.93:
            return {
                "score": final_score,
                "level": "S",
                "color": "#005822",
                "label": "极致流畅，近乎完美"
            }
        elif final_score >= 0.80:
            return {
                "score": final_score,
                "level": "A",
                "color": "#1B5E20",
                "label": "稳定流畅，表现优秀"
            }
        elif final_score >= 0.68:
            return {
                "score": final_score,
                "level": "B",
                "color": "#D39E00",
                "label": "基本流畅，偶有波动"
            }
        elif final_score >= 0.50:
            return {
                "score": final_score,
                "level": "C",
                "color": "#E65100",
                "label": "有明显卡顿，影响体验"
            }
        elif final_score >= 0.35:
            return {
                "score": final_score,
                "level": "D",
                "color": "#C62828",
                "label": "严重卡顿，需要优化"
            }
        else:
            return {
                "score": final_score,
                "level": "E",
                "color": "#7B1FA2",
                "label": "极差体验，建议排查"
            }

    # Workflow: ======================== I/O ========================

    @staticmethod
    def analyze_io_score(
            df: "pd.DataFrame",
            swap_threshold: int = 10240,
            rw_peak_threshold: int = 102400,
            idle_threshold=10
    ) -> dict:

        result = {
            "swap_status": "PASS",
            "swap_max_kb": 0.0,
            "swap_burst_ratio": 0.0,
            "swap_burst_count": 0,
            "rw_peak_kb": 0.0,
            "rw_std_kb": 0.0,
            "rw_burst_ratio": 0.0,
            "rw_idle_ratio": 0.0,
            "sys_burst": 0.0,
            "sys_burst_events": 0,
            "tags": [],
            "risk": [],
            "score": 100,
            "grade": "S"
        }

        tags, penalties = [], []

        df = df.copy()
        for col in ["read_bytes", "write_bytes", "rchar", "wchar", "syscr", "syscw"]:
            df[col] = df[col].astype(float).diff().fillna(0).clip(lower=0)

        # 🟦 ==== RW峰值与抖动 ====
        rw_vals = pd.concat([df["read_bytes"], df["write_bytes"]])
        rw_peak = rw_vals.max()
        rw_std = rw_vals.std()
        result["rw_peak_kb"] = round(rw_peak, 2)
        result["rw_std_kb"] = round(rw_std, 2)
        if rw_peak > rw_peak_threshold:
            penalties.append(15)
            tags.append("rw_peak_high")
            result["risk"].append("RW高峰")

        # 🟦 ==== 爆发段 ====
        rw_burst_ratio = (rw_vals > (rw_vals.mean() + rw_vals.std())).sum() / len(rw_vals)
        result["rw_burst_ratio"] = round(rw_burst_ratio, 2)
        if rw_burst_ratio > 0.1:
            penalties.append(10)
            tags.append("rw_burst")
            result["risk"].append("RW爆发")

        # 🟦 ==== Idle段 ====
        idle_mask = ((df[["read_bytes", "write_bytes", "rchar", "wchar"]].sum(axis=1)) < idle_threshold)
        idle_ratio = idle_mask.sum() / len(df)
        result["rw_idle_ratio"] = round(idle_ratio, 2)
        if idle_ratio > 0.4:
            penalties.append(10)
            tags.append("rw_idle")
            result["risk"].append("IO异常空闲")

        # 🟦 ==== 系统调用突变 ====
        cr_burst = (df["syscr"] > df["syscr"].mean() + 2 * df["syscr"].std()).sum()
        cw_burst = (df["syscw"] > df["syscw"].mean() + 2 * df["syscw"].std()).sum()
        sys_burst_events = cr_burst + cw_burst
        result["sys_burst"] = sys_burst_events
        if sys_burst_events > 3:
            penalties.append(5)
            tags.append("sys_burst")
            result["risk"].append("系统调用爆发")

        # 🟦 ==== Swap ====
        swap_vals = df["swap"].astype(float) * 1024
        swap_max = swap_vals.max()
        result["swap_max_kb"] = round(swap_max, 2)
        if swap_max > swap_threshold:
            penalties.append(20)
            tags.append("swap_burst")
            result["risk"].append("Swap爆发")
        swap_burst_mask = (swap_vals > swap_threshold)
        swap_burst_ratio = swap_burst_mask.sum() / len(df)
        result["swap_burst_ratio"] = round(swap_burst_ratio, 2)
        result["swap_burst_count"] = swap_burst_mask.sum()

        # 🟦 ==== Score/Level ====
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
