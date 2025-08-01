#   ____
#  / ___|  ___ ___  _ __ ___  ___
#  \___ \ / __/ _ \| '__/ _ \/ __|
#   ___) | (_| (_) | | |  __/\__ \
#  |____/ \___\___/|_|  \___||___/
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import numpy as np
import pandas as pd
from scipy.stats import (
    linregress, zscore
)


class Scores(object):

    # Workflow: ======================== MEM ========================

    @staticmethod
    def mem_fields_cfg() -> list:
        return [
            {"key": "trend",           "prefix": "",         "format": "{}",     "factor": 1, "unit": ""},
            {"key": "trend_score",     "prefix": "Score",    "format": "{:.2f}", "factor": 1, "unit": ""},
            {"key": "jitter_index",    "prefix": "Jitter",   "format": "{:.2f}", "factor": 1, "unit": ""},
            {"key": "r_squared",       "prefix": "R²",       "format": "{:.2f}", "factor": 1, "unit": ""},
            {"key": "slope",           "prefix": "Slope",    "format": "{:.2f}", "factor": 1, "unit": ""},
            {"key": "avg",             "prefix": "Avg",      "format": "{:.2f}", "factor": 1, "unit": ""},
            {"key": "max",             "prefix": "Max",      "format": "{:.2f}", "factor": 1, "unit": ""},
            {"key": "min",             "prefix": "Min",      "format": "{:.2f}", "factor": 1, "unit": ""},
            {"key": "color",           "prefix": "Color",    "format": "{}",     "factor": 1, "unit": ""},
            {"key": "poly_trend",      "prefix": "",         "format": "{}",     "factor": 1, "unit": ""},
            {"key": "poly_r2",         "prefix": "PolyR²",   "format": "{:.2f}", "factor": 1, "unit": ""},
            {"key": "poly_coef",       "prefix": "PolyC",    "format": "{}",     "factor": 1, "unit": ""},
            {"key": "window_slope",    "prefix": "WinSlp",   "format": "{:.2f}", "factor": 1, "unit": ""},
            {"key": "window_slope_max","prefix": "WinMax",   "format": "{:.2f}", "factor": 1, "unit": ""},
            {"key": "window_slope_min","prefix": "WinMin",   "format": "{:.2f}", "factor": 1, "unit": ""},
            {"key": "outlier_count",   "prefix": "Outlier",  "format": "{:.0f}", "factor": 1, "unit": ""},
        ]

    @staticmethod
    def analyze_mem_score(
        df: "pd.DataFrame",
        column: str = "pss",
        r2_threshold: float = 0.5,
        slope_threshold: float = 0.01,
        window: int = 30,
        remove_outlier: bool = True
    ) -> dict:

        # 🟨 ==== 默认结果 ====
        result = {
            "trend_score": 0.0,
            "jitter_index": 0.0,
            "r_squared": 0.0,
            "slope": 0.0,
            "avg": 0.0,
            "max": 0.0,
            "min": 0.0,
            "color": "#BBBBBB",
            "poly_trend": "-",
            "poly_r2": 0.0,
            "poly_coef": [],
            "window_slope": None,
            "window_slope_max": None,
            "window_slope_min": None,
            "outlier_count": 0
        }

        # 🟨 ==== 数据校验 ====
        df = df.copy()

        if column not in df or df[column].isnull().any():
            return {"trend": "Invalid Data"} | result

        if len(values := df[column].to_numpy()) < 10:
            return {"trend": "Few Data"} | result

        # 🟨 ==== 异常剔除 ====
        outlier_count = 0
        if remove_outlier:
            if np.all(np.isnan(zs := zscore(values))):
                return {"trend": "All NaN", "outlier_count": len(values)} | result
            mask = np.abs(zs) < 3
            outlier_count = np.sum(~mask)
            if len(values := values[mask]) < 10:
                return {"trend": "Cleaned", "outlier_count": outlier_count} | result

        # 🟨 ==== 基础统计 ====
        avg_val = values.mean()
        max_val = values.max()
        min_val = values.min()

        # 🟨 ==== 抖动指数 ====
        jitter_index = round(values.std() / (avg_val or 1e-6), 4)

        # 🟨 ==== 线性拟合 ====
        x = np.arange(len(values))
        slope, intercept, r_val, _, _ = linregress(x, values)
        r_squared = round(r_val ** 2, 4)
        slope = round(slope, 4)

        # 🟨 ==== 多项式拟合（2阶） ====
        try:
            poly_coef = np.polyfit(x, values, 2)
            poly_fit = np.poly1d(poly_coef)
            fitted = poly_fit(x)
            poly_r2 = 1 - np.sum((values - fitted) ** 2) / np.sum((values - np.mean(values)) ** 2)
            poly_r2 = round(poly_r2, 4)
            if abs(poly_coef[0]) < 1e-8:
                poly_trend = "Linear ~"
            elif poly_coef[0] > 0:
                poly_trend = "U-shape ↑↓"
            else:
                poly_trend = "∩-shape ↓↑"
        except (np.linalg.LinAlgError, ValueError):
            poly_coef = [0, 0, 0]
            poly_r2 = 0.0
            poly_trend = "-"

        # 🟨 ==== 滑动窗口趋势分析 ====
        window_slope = window_slope_max = window_slope_min = None
        if window and len(values) >= window:
            slopes = []
            for i in range(0, len(values) - window + 1):
                segment = values[i:i+window]
                xw = np.arange(window)
                s, _, _, _, _ = linregress(xw, segment)
                slopes.append(s)
            if slopes:
                window_slope = round(np.mean(slopes), 4)
                window_slope_max = round(np.max(slopes), 4)
                window_slope_min = round(np.min(slopes), 4)

        # 🟨 ==== 趋势判断 ====
        if r_squared < r2_threshold:
            trend = "Wave ~"
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

        # 🟨 ==== 综合输出 ====
        return {
            "trend": trend,
            "trend_score": score,
            "jitter_index": jitter_index,
            "r_squared": r_squared,
            "slope": slope,
            "avg": avg_val,
            "max": max_val,
            "min": min_val,
            "color": color,
            "poly_trend": poly_trend,
            "poly_r2": poly_r2,
            "poly_coef": [round(c, 6) for c in poly_coef],
            "window_slope": window_slope,
            "window_slope_max": window_slope_max,
            "window_slope_min": window_slope_min,
            "outlier_count": int(outlier_count)
        }

    # Workflow: ======================== GFX ========================

    @staticmethod
    def gfx_fields_cfg() -> list:
        return [
            {"key": "level",                "prefix": "Level",      "format": "{}",      "factor": 1,   "unit": ""},
            {"key": "score",                "prefix": "Score",      "format": "{:.2f}",  "factor": 100, "unit": ""},
            {"key": "color",                "prefix": "Color",      "format": "{}",      "factor": 1,   "unit": ""},
            {"key": "frame_count",          "prefix": "Count",      "format": "{:.0f}",  "factor": 1,   "unit": ""},
            {"key": "duration_s",           "prefix": "Dur",        "format": "{:.2f}",  "factor": 1,   "unit": "s"},
            {"key": "min_fps",              "prefix": "Min FPS",    "format": "{:.2f}",  "factor": 1,   "unit": ""},
            {"key": "avg_fps",              "prefix": "Avg FPS",    "format": "{:.2f}",  "factor": 1,   "unit": ""},
            {"key": "max_fps",              "prefix": "Max FPS",    "format": "{:.2f}",  "factor": 1,   "unit": ""},
            {"key": "p95_fps",              "prefix": "P95 FPS",    "format": "{:.2f}",  "factor": 1,   "unit": ""},
            {"key": "p99_fps",              "prefix": "P99 FPS",    "format": "{:.2f}",  "factor": 1,   "unit": ""},
            {"key": "fps_std",              "prefix": "STD",        "format": "{:.2f}",  "factor": 1,   "unit": ""},
            {"key": "jank_ratio",           "prefix": "JNK",        "format": "{:.2f}",  "factor": 1,   "unit": "%"},
            {"key": "high_latency_ratio",   "prefix": "Hi-Lat",     "format": "{:.2f}",  "factor": 1,   "unit": "%"},
            {"key": "severe_latency_ratio", "prefix": "Sev-Lat",    "format": "{:.2f}",  "factor": 1,   "unit": "%"},
            {"key": "max_frame_time",       "prefix": "MaxDur",     "format": "{:.2f}",  "factor": 1,   "unit": "ms"},
            {"key": "min_frame_time",       "prefix": "MinDur",     "format": "{:.2f}",  "factor": 1,   "unit": "ms"},
            {"key": "roll_avg_fps",         "prefix": "Roll FPS",   "format": "{:.2f}",  "factor": 1,   "unit": ""},
            {"key": "roll_jnk_ratio",       "prefix": "Roll JNK",   "format": "{:.2f}",  "factor": 1,   "unit": "%"},
            {"key": "drag_avg_fps",         "prefix": "Drag FPS",   "format": "{:.2f}",  "factor": 1,   "unit": ""},
            {"key": "drag_jnk_ratio",       "prefix": "Drag JNK",   "format": "{:.2f}",  "factor": 100, "unit": "%"},
            {"key": "longest_low_fps",      "prefix": "LMax",       "format": "{:.2f}",  "factor": 1,   "unit": "s"},
            {"key": "score_jank",           "prefix": "JNK Score",  "format": "{:.2f}",  "factor": 1,   "unit": ""},
            {"key": "score_latency",        "prefix": "Lat Score",  "format": "{:.2f}",  "factor": 1,   "unit": ""},
            {"key": "score_fps_var",        "prefix": "Var Score",  "format": "{:.2f}",  "factor": 1,   "unit": ""},
            {"key": "score_motion",         "prefix": "Mot Score",  "format": "{:.2f}",  "factor": 1,   "unit": ""},
        ]

    @staticmethod
    def analyze_gfx_score(
        frames: list[dict],
        roll_ranges: list[dict],
        drag_ranges: list[dict],
        jank_ranges: list[dict],
        fps_key: str = "fps_app"
    ) -> dict:

        # 🟩 ==== 默认结果 ====
        result = {
            "level": "N/A",
            "score": 0.0,
            "color": "#BBBBBB",
            "frame_count": len(frames),
            "duration_s": 0,
            "min_fps": 0.0,
            "avg_fps": 0.0,
            "max_fps": 0.0,
            "p95_fps": 0.0,
            "p99_fps": 0.0,
            "fps_std": 0.0,
            "jank_ratio": 0.0,
            "high_latency_ratio": 0.0,
            "severe_latency_ratio": 0.0,
            "max_frame_time": 0.0,
            "min_frame_time": 0.0,
            "roll_avg_fps": None,
            "roll_jnk_ratio": None,
            "drag_avg_fps": None,
            "drag_jnk_ratio": None,
            "longest_low_fps": 0.0,
            "score_jank": 0.0,
            "score_latency": 0.0,
            "score_fps_var": 0.0,
            "score_motion": 0.0,
        }

        # 🟩 ==== 数据校验 ====
        if (total_frames := len(frames)) < 10:
            return {"label": "Few Frames", **result}

        if (duration := frames[-1]["timestamp_ms"] - frames[0]["timestamp_ms"]) <= 0:
            return {"label": "Invalid Time", **result}

        if not (fps_values := [app_fps for f in frames if (app_fps := f.get(fps_key)) is not None]):
            return {"label": "No FPS", **result}

        result["duration_s"] = (duration_s := duration / 1000)
        result["frame_count"] = total_frames

        # 🟩 ==== 基础统计 ====
        result["min_fps"] = min(fps_values)
        result["max_fps"] = max(fps_values)
        result["avg_fps"] = float(np.mean(fps_values))
        result["fps_std"] = float(np.std(fps_values, ddof=1)) if len(fps_values) > 1 else 0
        result["p95_fps"] = float(np.percentile(fps_values, 95))
        result["p99_fps"] = float(np.percentile(fps_values, 99))
        frame_times = [f["duration_ms"] for f in frames]
        result["max_frame_time"] = max(frame_times)
        result["min_frame_time"] = min(frame_times)

        # 🟩 ==== 16.67ms 掉帧指标 ====
        result["jank_ratio"] = sum(1 for f in frames if f.get("is_jank")) / total_frames
        ideal_frame_time = 1000 / 60
        over_threshold = sum(1 for f in frames if f["duration_ms"] > ideal_frame_time)
        result["high_latency_ratio"] = over_threshold / total_frames

        # 🟩 ==== 32ms 严重卡顿指标 ====
        severe_frame_time = 32
        severe_over_threshold = sum(1 for f in frames if f["duration_ms"] > severe_frame_time)
        result["severe_latency_ratio"] = severe_over_threshold / total_frames
        
        # 🟩 ==== 连续低FPS最长段 ====
        low_fps_threshold, longest, cur = 30, 0, 0
        for fps in fps_values:
            if fps < low_fps_threshold:
                cur += 1
                longest = max(longest, cur)
            else:
                cur = 0
        result["longest_low_fps"] = longest * duration_s / total_frames if total_frames else 0.0

        # 🟩 ==== 滑动区指标 ====
        roll_frames = []
        for r in roll_ranges or []:
            roll_frames.extend([f for f in frames if r["start_ts"] <= f["timestamp_ms"] <= r["end_ts"]])
        if roll_frames:
            roll_fps = [f.get(fps_key) for f in roll_frames if f.get(fps_key) is not None]
            roll_jnk = [f.get("is_jank", 0) for f in roll_frames]
            result["roll_avg_fps"] = float(np.mean(roll_fps)) if roll_fps else None
            result["roll_jnk_ratio"] = sum(roll_jnk) / len(roll_jnk) if roll_jnk else None

        # 🟩 ==== 拖拽区指标 ====
        drag_frames = []
        for r in drag_ranges or []:
            drag_frames.extend([f for f in frames if r["start_ts"] <= f["timestamp_ms"] <= r["end_ts"]])
        if drag_frames:
            drag_fps = [f.get(fps_key) for f in drag_frames if f.get(fps_key) is not None]
            drag_jnk = [f.get("is_jank", 0) for f in drag_frames]
            result["drag_avg_fps"] = float(np.mean(drag_fps)) if drag_fps else None
            result["drag_jnk_ratio"] = sum(drag_jnk) / len(drag_jnk) if drag_jnk else None

        # 🟩 ==== 评分组成 ====
        jank_total = sum(r["end_ts"] - r["start_ts"] for r in jank_ranges)
        score_jank = 1.0 - min(jank_total / duration, 1.0)
        latency_score = 1.0 - result["high_latency_ratio"] / 100
        fps_score = max(1.0 - min(result["fps_std"] / 10, 1.0), 0.0) * min(result["avg_fps"] / 60, 1.0)
        motion_total = sum(r["end_ts"] - r["start_ts"] for r in (roll_ranges or []) + (drag_ranges or []))

        if motion_total == 0:
            motion_score = 0.0
        else:
            motion_jank_overlap = sum(
                max(0, min(rj["end_ts"], rm["end_ts"]) - max(rj["start_ts"], rm["start_ts"]))
                for rm in (roll_ranges or []) + (drag_ranges or [])
                for rj in (jank_ranges or [])
            )
            motion_score = 1.0 - min(motion_jank_overlap / (motion_total + 1e-6), 1.0)

        result["score_jank"] = score_jank
        result["score_latency"] = latency_score
        result["score_fps_var"] = fps_score
        result["score_motion"] = motion_score

        # 🟩 ==== 综合得分 ====
        final_score = (
            score_jank * 0.5 + latency_score * 0.2 + fps_score * 0.2 + motion_score * 0.1
        )
        result["score"] = final_score

        if final_score >= 0.93:
            result.update({
                "label": "Flawless - Ultra Smooth", "level": "S", "color": "#005822"
            })
        elif final_score >= 0.80:
            result.update({
                "label": "Excellent - Stable & Fast", "level": "A", "color": "#1B5E20"
            })
        elif final_score >= 0.68:
            result.update({
                "label": "Good - Minor Stutters", "level": "B", "color": "#D39E00"
            })
        elif final_score >= 0.50:
            result.update({
                "label": "Fair - Noticeable Lag", "level": "C", "color": "#E65100"
            })
        elif final_score >= 0.35:
            result.update({
                "label": "Poor - Frequent Stutter", "level": "D", "color": "#C62828"
            })
        else:
            result.update({
                "label": "Unusable - Critical Lag", "level": "E", "color": "#7B1FA2"
            })

        return result

    # Workflow: ======================== I/O ========================

    @staticmethod
    def io_fields_cfg() -> list:
        return [
            {"key": "swap_status",        "prefix": "Swap",      "format": "{}",      "unit": "",   "factor": 1},
            {"key": "swap_max_kb",        "prefix": "SwapMax",   "format": "{:.0f}",  "unit": "KB", "factor": 1},
            {"key": "swap_burst_ratio",   "prefix": "SwpBurst",  "format": "{:.2f}",  "unit": "%",  "factor": 100},
            {"key": "swap_burst_count",   "prefix": "SwpBurst#", "format": "{:.2f}",  "unit": "",   "factor": 1},
            {"key": "rw_peak_kb",         "prefix": "RWPeak",    "format": "{:.2f}",  "unit": "KB", "factor": 1},
            {"key": "rw_std_kb",          "prefix": "RWStd",     "format": "{:.2f}",  "unit": "KB", "factor": 1},
            {"key": "rw_burst_ratio",     "prefix": "RW Burst",  "format": "{:.2f}",  "unit": "%",  "factor": 100},
            {"key": "rw_idle_ratio",      "prefix": "RW Idle",   "format": "{:.2f}",  "unit": "%",  "factor": 100},
            {"key": "sys_burst",          "prefix": "SysBurst",  "format": "{:.2f}",  "unit": "",   "factor": 1},
            {"key": "sys_burst_events",   "prefix": "BurstEvt",  "format": "{:.2f}",  "unit": "",   "factor": 1},
            {"key": "score",              "prefix": "Score",     "format": "{:.2f}",  "unit": "",   "factor": 1},
            {"key": "grade",              "prefix": "Grade",     "format": "{}",      "unit": "",   "factor": 1},
        ]

    @staticmethod
    def analyze_io_score(
        df: "pd.DataFrame",
        rw_peak_threshold: int = 102400,
        idle_threshold=10,
        swap_threshold: int = 10240
    ) -> dict:

        # 🟦 ==== 默认结果 ====
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

        df = df.copy()

        for col in ["read_bytes", "write_bytes", "rchar", "wchar", "syscr", "syscw"]:
            df[col] = df[col].astype(float).diff().fillna(0).clip(lower=0)

        # 🟦 ==== 标签统计 ====
        tags, penalties = [], []

        # 🟦 ==== RW峰值与抖动 ====
        rw_vals = pd.concat([df["read_bytes"], df["write_bytes"]])
        rw_peak = rw_vals.max()
        rw_std = rw_vals.std()
        result["rw_peak_kb"] = round(rw_peak, 2)
        result["rw_std_kb"] = round(rw_std, 2)
        if rw_peak > rw_peak_threshold:
            penalties.append(15)
            tags.append("rw_peak_high")
            result["risk"].append("RW Peak High")

        # 🟦 ==== 爆发段 ====
        rw_burst_threshold = rw_vals.mean() + rw_vals.std()
        rw_burst_ratio = (rw_vals > rw_burst_threshold).mean()
        result["rw_burst_ratio"] = round(rw_burst_ratio, 2)
        if rw_burst_ratio > 0.1:
            penalties.append(10)
            tags.append("rw_burst")
            result["risk"].append("RW Burst")

        # 🟦 ==== Idle段 ====
        idle_mask = ((df[["read_bytes", "write_bytes", "rchar", "wchar"]].sum(axis=1)) < idle_threshold)
        idle_ratio = idle_mask.mean()
        result["rw_idle_ratio"] = round(idle_ratio, 2)
        if idle_ratio > 0.4:
            penalties.append(10)
            tags.append("rw_idle")
            result["risk"].append("IO Idle")

        # 🟦 ==== 系统调用突变 ====
        cr_burst = (df["syscr"] > df["syscr"].mean() + 2 * df["syscr"].std()).sum()
        cw_burst = (df["syscw"] > df["syscw"].mean() + 2 * df["syscw"].std()).sum()
        sys_burst_events = cr_burst + cw_burst
        result["sys_burst"] = sys_burst_events
        if sys_burst_events > 3:
            penalties.append(5)
            tags.append("sys_burst")
            result["risk"].append("Sys Burst")

        # 🟦 ==== Swap爆发 ====
        swap_vals = df["swap"].astype(float) * 1024
        swap_max = swap_vals.max()
        result["swap_max_kb"] = round(swap_max, 2)
        if swap_max > swap_threshold:
            penalties.append(20)
            tags.append("swap_burst")
            result["risk"].append("Swap Burst")
        swap_burst_mask = (swap_vals > swap_threshold)
        result["swap_burst_ratio"] = round(swap_burst_mask.mean(), 2)
        result["swap_burst_count"] = swap_burst_mask.sum()

        # 🟦 ==== 综合输出 ====
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
