#   ___       _     _
#  / _ \ _ __| |__ (_)___
# | | | | '__| '_ \| / __|
# | |_| | |  | |_) | \__ \
#  \___/|_|  |_.__/|_|___/
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import numpy as np
import pandas as pd
from scipy.stats import (
    linregress, zscore
)


class Orbis(object):
    """Orbis"""

    # Workflow: ======================== CFG ========================

    @staticmethod
    def mem_fields_cfg() -> dict:
        """
        返回内存分析字段配置，定义展示格式与单位。
        """
        return {
            "trend":            {"prefix": "",         "format": "{}",     "factor": 1, "unit": ""},
            "trend_score":      {"prefix": "Score",    "format": "{:.2f}", "factor": 1, "unit": ""},
            "jitter_index":     {"prefix": "Jitter",   "format": "{:.2f}", "factor": 1, "unit": ""},
            "r_squared":        {"prefix": "R²",       "format": "{:.2f}", "factor": 1, "unit": ""},
            "slope":            {"prefix": "Slope",    "format": "{:.2f}", "factor": 1, "unit": ""},
            "avg":              {"prefix": "Avg",      "format": "{:.2f}", "factor": 1, "unit": ""},
            "max":              {"prefix": "Max",      "format": "{:.2f}", "factor": 1, "unit": ""},
            "min":              {"prefix": "Min",      "format": "{:.2f}", "factor": 1, "unit": ""},
            "color":            {"prefix": "Color",    "format": "{}",     "factor": 1, "unit": ""},
            "poly_trend":       {"prefix": "",         "format": "{}",     "factor": 1, "unit": ""},
            "poly_r2":          {"prefix": "PolyR²",   "format": "{:.2f}", "factor": 1, "unit": ""},
            "poly_coef":        {"prefix": "PolyC",    "format": "{}",     "factor": 1, "unit": ""},
            "window_slope":     {"prefix": "WinSlp",   "format": "{:.2f}", "factor": 1, "unit": ""},
            "window_slope_max": {"prefix": "WinMax",   "format": "{:.2f}", "factor": 1, "unit": ""},
            "window_slope_min": {"prefix": "WinMin",   "format": "{:.2f}", "factor": 1, "unit": ""}
        }

    @staticmethod
    def gfx_fields_cfg() -> dict:
        """
        返回图形分析字段配置，定义指标标签、格式与评分结构。
        """
        return {
            "level":                {"prefix": "Level",      "format": "{}",      "factor": 1,   "unit": ""},
            "score":                {"prefix": "Score",      "format": "{:.2f}",  "factor": 100, "unit": ""},
            "color":                {"prefix": "Color",      "format": "{}",      "factor": 1,   "unit": ""},
            "frame_count":          {"prefix": "Count",      "format": "{:.0f}",  "factor": 1,   "unit": ""},
            "duration_s":           {"prefix": "Dur",        "format": "{:.2f}",  "factor": 1,   "unit": "s"},
            "min_fps":              {"prefix": "Min FPS",    "format": "{:.2f}",  "factor": 1,   "unit": ""},
            "avg_fps":              {"prefix": "Avg FPS",    "format": "{:.2f}",  "factor": 1,   "unit": ""},
            "max_fps":              {"prefix": "Max FPS",    "format": "{:.2f}",  "factor": 1,   "unit": ""},
            "p95_fps":              {"prefix": "P95 FPS",    "format": "{:.2f}",  "factor": 1,   "unit": ""},
            "p99_fps":              {"prefix": "P99 FPS",    "format": "{:.2f}",  "factor": 1,   "unit": ""},
            "fps_std":              {"prefix": "STD",        "format": "{:.2f}",  "factor": 1,   "unit": ""},
            "jank_ratio":           {"prefix": "JNK",        "format": "{:.2f}",  "factor": 100, "unit": "%"},
            "high_latency_ratio":   {"prefix": "Hi-Lat",     "format": "{:.2f}",  "factor": 100, "unit": "%"},
            "severe_latency_ratio": {"prefix": "Sev-Lat",    "format": "{:.2f}",  "factor": 100, "unit": "%"},
            "max_frame_time":       {"prefix": "MaxDur",     "format": "{:.2f}",  "factor": 1,   "unit": "ms"},
            "min_frame_time":       {"prefix": "MinDur",     "format": "{:.2f}",  "factor": 1,   "unit": "ms"},
            "roll_avg_fps":         {"prefix": "Roll FPS",   "format": "{:.2f}",  "factor": 1,   "unit": ""},
            "roll_jnk_ratio":       {"prefix": "Roll JNK",   "format": "{:.2f}",  "factor": 100, "unit": "%"},
            "drag_avg_fps":         {"prefix": "Drag FPS",   "format": "{:.2f}",  "factor": 1,   "unit": ""},
            "drag_jnk_ratio":       {"prefix": "Drag JNK",   "format": "{:.2f}",  "factor": 100, "unit": "%"},
            "longest_low_fps":      {"prefix": "LMax",       "format": "{:.2f}",  "factor": 1,   "unit": "s"},
            "score_jank":           {"prefix": "JNK Score",  "format": "{:.2f}",  "factor": 1,   "unit": ""},
            "score_latency":        {"prefix": "Lat Score",  "format": "{:.2f}",  "factor": 1,   "unit": ""},
            "score_fps_var":        {"prefix": "Var Score",  "format": "{:.2f}",  "factor": 1,   "unit": ""},
            "score_motion":         {"prefix": "Mot Score",  "format": "{:.2f}",  "factor": 1,   "unit": ""}
        }

    @staticmethod
    def io_fields_cfg() -> dict:
        """
        返回I/O分析字段配置，用于评估磁盘、交换区与系统调用表现。
        """
        return {
            "swap_status":        {"prefix": "Swap",      "format": "{}",      "factor": 1,   "unit": ""},
            "swap_max_kb":        {"prefix": "SwapMax",   "format": "{:.0f}",  "factor": 1,   "unit": "KB"},
            "swap_burst_ratio":   {"prefix": "SwpBurst",  "format": "{:.2f}",  "factor": 100, "unit": "%"},
            "swap_burst_count":   {"prefix": "SwpBurst#", "format": "{:.2f}",  "factor": 1,   "unit": ""},
            "rw_peak_kb":         {"prefix": "RWPeak",    "format": "{:.2f}",  "factor": 1,   "unit": "KB"},
            "rw_std_kb":          {"prefix": "RWStd",     "format": "{:.2f}",  "factor": 1,   "unit": "KB"},
            "rw_burst_ratio":     {"prefix": "RW Burst",  "format": "{:.2f}",  "factor": 100, "unit": "%"},
            "rw_idle_ratio":      {"prefix": "RW Idle",   "format": "{:.2f}",  "factor": 100, "unit": "%"},
            "sys_burst":          {"prefix": "SysBurst",  "format": "{:.2f}",  "factor": 1,   "unit": ""},
            "sys_burst_events":   {"prefix": "BurstEvt",  "format": "{:.2f}",  "factor": 1,   "unit": ""},
            "score":              {"prefix": "Score",     "format": "{:.2f}",  "factor": 1,   "unit": ""},
            "grade":              {"prefix": "Grade",     "format": "{}",      "factor": 1,   "unit": ""}
        }

    # Workflow: ======================== MEM ========================

    @staticmethod
    def analyze_mem_score(
        mem_part: list[float],
        r2_threshold: float = 0.5,
        slope_threshold: float = 0.01,
        window: int = 30
    ) -> dict:
        """
        分析一组内存采样数据的变化趋势、稳定性与结构特征，返回结构化评分结果。

        Parameters
        ----------
        mem_part : list[float]
            内存采样的原始时间序列数据，一般为某段时间内的 PSS 或 RSS 值。

        r2_threshold : float, optional
            判定趋势拟合优度的阈值，R² 低于该值将视为无明显趋势，默认值为 0.5。

        slope_threshold : float, optional
            判定线性趋势方向的斜率阈值，低于该值将视为稳定趋势，默认值为 0.01。

        window : int, optional
            滑动窗口大小，用于计算局部斜率变化趋势，默认值为 30。

        Returns
        -------
        result : dict
            返回结构化的趋势评分字典，字段说明如下：

            - trend : str
                趋势类型，包括 Upward ↑、Downward ↓、Stable →、Wave ~ 等。

            - trend_score : float
                趋势得分，范围 [-1.0, 1.0]，反映趋势强度与方向性。

            - jitter_index : float
                抖动指数，衡量数据的波动幅度，值越大表示不稳定性越高。

            - r_squared : float
                线性拟合的决定系数 R²，用于量化趋势拟合优度。

            - slope : float
                拟合直线的斜率，正值表示上升，负值表示下降。

            - avg, max, min : float
                内存数据的均值、最大值与最小值，单位与输入一致。

            - color : str
                趋势对应的推荐颜色，用于图表高亮或 UI 渲染。

            - poly_trend : str
                多项式趋势形态标识（如 U-shape ↑↓、∩-shape ↓↑、Linear ~）。

            - poly_r2 : float
                二阶多项式拟合的决定系数 R²，反映非线性趋势拟合效果。

            - poly_coef : list[float]
                多项式拟合的系数列表 [a, b, c]，对应公式 ax² + bx + c。

            - window_slope : float
                滑动窗口中所有局部斜率的平均值。

            - window_slope_max : float
                滑动窗口中观察到的最大上升斜率。

            - window_slope_min : float
                滑动窗口中观察到的最大下降斜率。

        Notes
        -----
        - 建议输入等间隔采样的内存使用序列，采样长度不少于 10。
        - 若输入数据波动剧烈或噪声较多，开启异常剔除可提升趋势识别准确性。
        - 趋势评分可作为内存泄漏、回收抖动等问题的辅助判据。
        """

        # 🟨 ==== 默认结果 ====
        result = {
            "trend": "N/A",
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
            "window_slope_min": None
        }

        # 🟨 ==== 数据校验 ====
        if np.isnan(values := np.array(mem_part, dtype=float)).any():
            return {"trend": "Invalid Data", **result}

        if len(values) < 10:
            return {"trend": "Few Data", **result}

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
            "window_slope_min": window_slope_min
        }

    # Workflow: ======================== GFX ========================

    @staticmethod
    def analyze_gfx_score(
        frames: list[dict],
        roll_ranges: list[dict],
        drag_ranges: list[dict],
        jank_ranges: list[dict],
        fps_key: str = "fps_app"
    ) -> dict:
        """
        分析一组图形帧数据的帧率、卡顿、滑动与拖拽性能，生成多维评分与等级评估。

        Parameters
        ----------
        frames : list of dict
            帧时间数据列表，每个字典应包含时间戳、帧时长、是否掉帧、帧率等字段。

        roll_ranges : list of dict
            滑动操作的时间范围集合，常用于提取滑动场景下的性能表现。

        drag_ranges : list of dict
            拖拽操作的时间范围集合，用于评估交互操作下的流畅度和卡顿情况。

        jank_ranges : list of dict
            连续掉帧的时间区间列表，用于计算卡顿时长和对应影响。

        fps_key : str, optional
            用于提取帧率的字段名称，默认使用 `"fps_app"`，支持替换为系统帧率等指标。

        Returns
        -------
        result : dict
            返回包含评分、等级、波动性与局部指标的分析结果，字段说明如下：

            - level : str
                综合评分等级（S~E），反映系统图形性能档次。

            - score : float
                综合得分（0~1），由多个子评分加权计算而得。

            - color : str
                根据评分等级推荐的十六进制颜色值。

            - frame_count : int
                总帧数，用于评估采样数据覆盖量。

            - duration_s : float
                采样时长，单位为秒。

            - min_fps, avg_fps, max_fps : float
                最小、平均、最大帧率指标。

            - p95_fps, p99_fps : float
                第 95 和 99 百分位帧率，反映极端性能情况。

            - fps_std : float
                帧率标准差，用于衡量帧率波动性。

            - jank_ratio : float
                掉帧比例（帧耗时 > 16.67ms），反映系统轻度卡顿情况。

            - high_latency_ratio : float
                高延迟帧比例（帧耗时 > 16.67ms），衡量非理想帧时间的占比。

            - severe_latency_ratio : float
                严重延迟帧比例（帧耗时 > 32ms），衡量明显卡顿的频率。

            - max_frame_time, min_frame_time : float
                单帧最大与最小耗时（单位 ms）。

            - longest_low_fps : float
                连续低帧率段的最长时长（FPS < 30）。

            - roll_avg_fps, roll_jnk_ratio : float or None
                滑动区间下的平均帧率与卡顿比例，若无滑动则为 None。

            - drag_avg_fps, drag_jnk_ratio : float or None
                拖拽区间下的平均帧率与卡顿比例，若无拖拽则为 None。

            - score_jank : float
                卡顿评分，基于卡顿时长对总时长的占比计算。

            - score_latency : float
                延迟评分，基于高延迟帧占比评估响应能力。

            - score_fps_var : float
                帧率波动评分，结合稳定性与平均帧率计算。

            - score_motion : float
                动作流畅性评分，评估交互区与卡顿区的重叠程度。

        Notes
        -----
        - 建议用于 App 的图形流畅度分析，特别适合基于帧时间与 VSYNC 数据的性能评估。
        - 支持通过 roll 和 drag 区间分场景分析帧率表现与波动性。
        - 综合评分采用多因子加权算法，并提供标准等级与配色，用于直观展示评估结果。
        """

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
    def analyze_io_score(
        io_data: list[dict],
        rw_peak_threshold: int = 102400,
        idle_threshold: int = 10,
        swap_threshold: int = 10240
    ) -> dict:
        """
        分析一组 I/O 指标数据的性能表现，包括读写行为、Swap 使用和系统调用波动，并生成评分与等级。

        Parameters
        ----------
        io_data : list of dict
            包含原始 I/O 采样数据的列表，每个字典表示一次采样结果，需包含读写字节数、Swap、系统调用等字段。

        rw_peak_threshold : int, optional
            读写峰值阈值（单位：字节），超过该值会触发 RW 高峰惩罚，默认值为 102400。

        idle_threshold : int, optional
            判定空闲状态的 I/O 活动阈值（单位：字节），低于此值的周期将视为 Idle，默认值为 10。

        swap_threshold : int, optional
            Swap 使用量的爆发阈值（单位：KB），超过该值将被判定为 Swap 爆发，默认值为 10240。

        Returns
        -------
        result : dict
            包含 I/O 评估结果的结构化字典，字段说明如下：

            - swap_status : str
                Swap 状态标记（如 PASS / FAIL），用于快速判断是否存在异常。

            - swap_max_kb : float
                采样周期内观察到的最大 Swap 使用量（单位：KB）。

            - swap_burst_ratio : float
                Swap 爆发比例，表示超过阈值的采样点占比。

            - swap_burst_count : int
                Swap 爆发的总次数（即超阈值的点数）。

            - rw_peak_kb : float
                读写带宽的最大瞬时值（单位：KB）。

            - rw_std_kb : float
                读写带宽的波动程度（标准差，单位：KB）。

            - rw_burst_ratio : float
                RW 爆发段比例，即带宽瞬时值超出波动阈值的占比。

            - rw_idle_ratio : float
                Idle 周期占比，即 RW 活动较低的时间段占比。

            - sys_burst : float
                系统调用突变事件的总数（读+写）。

            - sys_burst_events : int
                系统突变的采样点数量，表示调用量异常剧增的事件频次。

            - tags : list of str
                所触发的风险标签，用于识别哪些维度存在异常（如 rw_burst、swap_burst 等）。

            - risk : list of str
                对应标签的风险描述文本，适用于日志与前端展示。

            - score : float
                总评分（0~100），由各异常项的扣分总和决定。

            - grade : str
                评分等级（S~E），用于表示整体 I/O 健康度。

        Notes
        -----
        - 建议输入已按照时间顺序排列的原始 I/O 数据，且包含完整字段。
        - 差值处理采用 `.diff()` 提取周期变化值，因此首个点不参与计算。
        - 分数评估体系采用惩罚累计机制，初始分数为 100，逐项扣除异常项得分。
        """

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

        df = pd.DataFrame(io_data)

        # 🟦 ==== 差值处理，避免链式赋值 ====
        io_cols = ["read_bytes", "write_bytes", "rchar", "wchar", "syscr", "syscw"]
        df.loc[:, io_cols] = df[io_cols].astype(float).diff().fillna(0).clip(lower=0)

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
