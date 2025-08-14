#  _____                      _                _
# |_   _| __ __ _  ___ ___   / \   _ __   __ _| |_   _ _______ _ __
#   | || '__/ _` |/ __/ _ \ / _ \ | '_ \ / _` | | | | |_  / _ \ '__|
#   | || | | (_| | (_|  __// ___ \| | | | (_| | | |_| |/ /  __/ |
#   |_||_|  \__,_|\___\___/_/   \_\_| |_|\__,_|_|\__, /___\___|_|
#                                                |___/
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import json
from bisect import bisect_left
from perfetto.trace_processor import (
    TraceProcessor, TraceProcessorConfig
)


class _TraceAnalyzer(object):
    """_TraceAnalyzer"""

    normalize_start_ts: float = 0.0

    def set_trace_start_ts(self, tp: "TraceProcessor") -> None:
        """
        设置 trace 起始时间戳，用于时间归一化处理。
        """
        self.normalize_start_ts = float(
            list(tp.query("SELECT trace_start() AS start_ts"))[0].start_ts
        ) / 1e6

    # Notes: ======================== MEM ========================

    @staticmethod
    def extract_rss(tp: "TraceProcessor", app_name: str) -> list[dict]:
        """
        提取指定进程的 RSS 内存使用数据。
        """
        sql = f"""
            SELECT
                c.ts / 1e6 AS time_sec,
                c.value / 1024.0 / 1024.0 AS rss_mb
            FROM counter c
            JOIN process_counter_track t ON c.track_id = t.id
            JOIN process p ON t.upid = p.upid
            WHERE t.name = 'mem.rss' AND p.name = '{app_name}'
            ORDER BY c.ts;
        """

        df = tp.query(sql).as_pandas_dataframe().dropna()
        # df["time_sec"] -= self.normalize_start_ts
        return df.to_dict("records")

    # Notes: ======================== GFX ========================

    @staticmethod
    def extract_raw_frames(tp: "TraceProcessor", app_name: str) -> list[dict]:
        """
        提取实际帧和期望帧的时间戳与属性，计算是否掉帧。
        """
        sql = f"""
            SELECT * FROM (
                SELECT
                    a.ts AS actual_ts,
                    a.dur AS actual_dur,
                    e.ts AS expected_ts,
                    e.dur AS expected_dur,
                    a.layer_name,
                    p.name AS process_name,
                    a.surface_frame_token,
                    a.present_type,
                    a.gpu_composition,
                    a.on_time_finish,
                    ROW_NUMBER() OVER (
                        PARTITION BY a.layer_name, a.surface_frame_token
                        ORDER BY a.ts
                    ) AS row_rank
                FROM actual_frame_timeline_slice a
                JOIN expected_frame_timeline_slice e ON a.surface_frame_token = e.surface_frame_token
                LEFT JOIN process p ON a.upid = p.upid
                WHERE a.layer_name LIKE '%{app_name}%'
            )
            WHERE row_rank = 1
            ORDER BY actual_ts
        """

        return [
            {
                # "timestamp_ms": (row.actual_ts / 1e6) - self.normalize_start_ts,
                "timestamp_ms": (row.actual_ts / 1e6),
                "duration_ms": row.actual_dur / 1e6,
                "drop_count": (drop_count := max(0, round(row.actual_dur / int(1e9 / 60)) - 1)),
                "is_jank": drop_count > 0,
                "layer_name": row.layer_name,
                "process_name": row.process_name,
                "frame_type": row.present_type or "Unknown",
                "gpu_composition": bool(row.gpu_composition),
                "on_time_finish": bool(row.on_time_finish),
            } for row in tp.query(sql)
        ]

    @staticmethod
    def extract_roll_ranges(tp: "TraceProcessor") -> list[dict]:
        """
        提取 trace 中滑动操作对应的时间范围。
        """
        sql = """
            SELECT ts, dur
            FROM slice
            WHERE name LIKE '%Scroll%' OR name LIKE '%scroll%'
        """

        return [
            {
                # "start_ts": (row.ts / 1e6) - self.normalize_start_ts,
                # "end_ts": ((row.ts + row.dur) / 1e6) - self.normalize_start_ts,
                "start_ts": (row.ts / 1e6),
                "end_ts": ((row.ts + row.dur) / 1e6),
            } for row in tp.query(sql)
        ]

    @staticmethod
    def extract_drag_ranges(tp: "TraceProcessor") -> list[dict]:
        """
        提取 trace 中拖拽操作对应的时间范围。
        """
        sql = """
            SELECT ts, dur
            FROM slice
            WHERE name LIKE '%drag%' OR name LIKE '%Drag%'
        """

        return [
            {
                # "start_ts": (row.ts / 1e6) - self.normalize_start_ts,
                # "end_ts": ((row.ts + row.dur) / 1e6) - self.normalize_start_ts,
                "start_ts": (row.ts / 1e6),
                "end_ts": ((row.ts + row.dur) / 1e6),
            } for row in tp.query(sql)
        ]

    @staticmethod
    def extract_vsync_sys_points(tp: "TraceProcessor") -> list[dict]:
        """
        提取系统 VSYNC 事件，计算系统帧率变化。
        """
        sql = f"""
            SELECT counter.ts
            FROM counter
            WHERE counter.track_id IN (
                SELECT track.id FROM track WHERE track.name = 'VSYNC-sf'
            )
            ORDER BY counter.ts
        """

        result = list(tp.query(sql))
        timestamps = [row.ts for row in result]

        fps_points = []
        for i in range(1, len(timestamps)):
            ts_prev = timestamps[i - 1]
            ts_curr = timestamps[i]
            interval_ns = ts_curr - ts_prev

            # 排除不合理采样间隔
            if interval_ns <= 0 or interval_ns > 1e9:
                continue

            fps = round(1e9 / interval_ns, 2)
            fps_points.append({
                # "ts": (ts_curr / 1e6) - self.normalize_start_ts,
                "ts": (ts_curr / 1e6),
                "fps": fps
            })

        return fps_points

    @staticmethod
    def extract_vsync_app_points(tp: "TraceProcessor") -> list[dict]:
        """
        提取应用 VSYNC 事件，计算应用帧率变化。
        """
        sql = f"""
            SELECT counter.ts
            FROM counter
            WHERE counter.track_id IN (
                SELECT track.id FROM track WHERE track.name = 'VSYNC-app'
            )
            ORDER BY counter.ts
        """

        result = list(tp.query(sql))
        timestamps = [row.ts for row in result]

        fps_points = []
        for i in range(1, len(timestamps)):
            ts_prev = timestamps[i - 1]
            ts_curr = timestamps[i]
            interval_ns = ts_curr - ts_prev

            # 排除不合理采样间隔
            if interval_ns <= 0 or interval_ns > 1e9:
                continue

            fps = round(1e9 / interval_ns, 2)
            fps_points.append({
                # "ts": (ts_curr / 1e6) - self.normalize_start_ts,
                "ts": (ts_curr / 1e6),
                "fps": fps
            })

        return fps_points

    @staticmethod
    def extract_sf_fps(tp: "TraceProcessor") -> list[dict]:
        """
        提取 SurfaceFlinger 的 FPS 计数器曲线。
        """
        sql = """
            SELECT ts/1e6 AS ts, value AS fps
            FROM counter
            WHERE track_id = (SELECT id FROM track WHERE name = 'SfCpu_fps')
            ORDER BY ts
        """

        df = tp.query(sql).as_pandas_dataframe()
        # df["ts"] -= self.normalize_start_ts
        return df.to_dict("records")

    @staticmethod
    def mark_consecutive_jank(frames: list[dict], min_count: int = 2) -> list[dict]:
        """
        标记连续掉帧区间，用于识别卡顿片段。
        """
        jank_ranges = []
        count = 0
        start_ts = None

        for frame in frames:
            if frame["is_jank"]:
                if count == 0:
                    start_ts = frame["timestamp_ms"]
                count += 1
            else:
                if count >= min_count:
                    end_ts = frame["timestamp_ms"]
                    jank_ranges.append({"start_ts": start_ts, "end_ts": end_ts})
                count = 0
                start_ts = None

        if count >= min_count:
            jank_ranges.append({"start_ts": start_ts, "end_ts": frames[-1]["timestamp_ms"]})

        return jank_ranges

    @staticmethod
    def annotate_frames(
        frames: list[dict],
        roll_ranges: list[dict],
        drag_ranges: list[dict],
        jank_ranges: list[dict],
        vsync_sys: list[dict],
        vsync_app: list[dict]
    ) -> None:
        """
        为帧数据打标注，包括滑动/拖拽/掉帧区间及对应帧率。
        """
        max_delta_ms = 50.0

        def in_any_range(ts: float, ranges: list[dict]) -> bool:
            return any(r["start_ts"] <= ts <= r["end_ts"] for r in ranges)

        def find_nearest(ts: float, vsync_list: list[dict]) -> float | None:
            ts_list = [v["ts"] for v in vsync_list]
            if not vsync_list or not ts_list:
                return None
            pos = bisect_left(ts_list, ts)
            candidates = []
            if pos < len(ts_list):
                candidates.append(vsync_list[pos])
            if pos > 0:
                candidates.append(vsync_list[pos - 1])
            nearest = min(candidates, key=lambda v: abs(v["ts"] - ts))
            return nearest["fps"] if abs(nearest["ts"] - ts) <= max_delta_ms else None

        for f in frames:
            timestamp_ms = f["timestamp_ms"]
            f["in_roll"] = in_any_range(timestamp_ms, roll_ranges)
            f["in_drag"] = in_any_range(timestamp_ms, drag_ranges)
            f["in_jank"] = in_any_range(timestamp_ms, jank_ranges)
            f["fps_sys"] = find_nearest(timestamp_ms, vsync_sys)
            f["fps_app"] = find_nearest(timestamp_ms, vsync_app)

    @staticmethod
    def extract_metrics(trace_file: str, tp_shell: str, app_name: str) -> dict:
        """
        抽象方法，需由子类实现指标提取逻辑。
        """
        raise NotImplementedError("Subclasses must implement extract_metrics() to return formatted trace data.")


class MemAnalyzer(_TraceAnalyzer):
    """MEM"""

    def extract_metrics(self, trace_file: str, tp_shell: str, app_name: str) -> dict:
        pass


class GfxAnalyzer(_TraceAnalyzer):
    """GFX"""

    def extract_metrics(self, trace_file: str, tp_shell: str, app_name: str) -> dict:
        with TraceProcessor(trace_file, config=TraceProcessorConfig(tp_shell)) as tp:
            self.set_trace_start_ts(tp)

            raw_frames = self.extract_raw_frames(tp, app_name)

            vsync_sys = self.extract_vsync_sys_points(tp)  # 系统FPS
            vsync_app = self.extract_vsync_app_points(tp)  # 应用FPS

            roll_ranges = self.extract_roll_ranges(tp)  # 滑动区间
            drag_ranges = self.extract_drag_ranges(tp)  # 拖拽区间

            jank_ranges = self.mark_consecutive_jank(raw_frames)  # 连续丢帧

            self.annotate_frames(
                raw_frames, roll_ranges, drag_ranges, jank_ranges, vsync_sys, vsync_app
            )

            gfx_data = {
                "metadata": {
                    "source": "perfetto", "app": app_name, "normalize": self.normalize_start_ts
                },
                "raw_frames": raw_frames,
                "vsync_sys": vsync_sys,
                "vsync_app": vsync_app,
                "roll_ranges": roll_ranges,
                "drag_ranges": drag_ranges,
                "jank_ranges": jank_ranges
            }

            gfx_fmt_data = {k: json.dumps(v) for k, v in gfx_data.items()}

            return gfx_fmt_data


if __name__ == '__main__':
    pass
