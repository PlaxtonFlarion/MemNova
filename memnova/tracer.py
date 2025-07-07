#   _____
#  |_   _| __ __ _  ___ ___ _ __
#    | || '__/ _` |/ __/ _ \ '__|
#    | || | | (_| | (_|  __/ |
#    |_||_|  \__,_|\___\___|_|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

from bisect import bisect_left
from perfetto.trace_processor import TraceProcessor


class Tracer(object):

    @staticmethod
    async def extract_primary_frames(tp: "TraceProcessor", layer_like: str = "") -> list[dict]:
        where_clause = f"WHERE a.layer_name LIKE '%{layer_like}%'" if layer_like else ""

        sql = f"""
            SELECT * FROM (
                SELECT
                    a.ts AS actual_ts,
                    a.dur AS actual_dur,
                    e.ts AS expected_ts,
                    e.dur AS expected_dur,
                    a.layer_name,
                    a.surface_frame_token,
                    p.name AS process_name,
                    ROW_NUMBER() OVER (
                        PARTITION BY a.layer_name, a.surface_frame_token
                        ORDER BY a.ts
                    ) AS row_rank
                FROM actual_frame_timeline_slice a
                JOIN expected_frame_timeline_slice e
                LEFT JOIN process p ON a.upid = p.upid
                {where_clause}
            )
            WHERE row_rank = 1
            ORDER BY actual_ts
        """

        return [
            {
                "timestamp_ms": row.actual_ts / 1e6,
                "duration_ms": row.actual_dur / 1e6,
                "drop_count": (drop_count := max(0, round(row.actual_dur / int(1e9 / 60)) - 1)),
                "is_jank": drop_count > 0,
                "layer_name": row.layer_name,
                "process_name": row.process_name
            } for row in tp.query(sql)
        ]

    @staticmethod
    async def extract_roll_ranges(tp: "TraceProcessor") -> list[dict]:
        sql = """
            SELECT ts, dur
            FROM slice
            WHERE name LIKE '%Scroll%' OR name LIKE '%scroll%'
        """
        return [
            {"start_ts": row.ts / 1e6, "end_ts": (row.ts + row.dur) / 1e6} for row in tp.query(sql)
        ]

    @staticmethod
    async def extract_drag_ranges(tp: "TraceProcessor") -> list[dict]:
        sql = """
            SELECT ts, dur
            FROM slice
            WHERE name LIKE '%drag%' OR name LIKE '%Drag%'
        """
        return [
            {"start_ts": row.ts / 1e6, "end_ts": (row.ts + row.dur) / 1e6} for row in tp.query(sql)
        ]

    @staticmethod
    async def extract_vsync_sys_points(tp: "TraceProcessor") -> list[dict]:
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
                "ts": ts_curr / 1e6,  # 转为 ms
                "fps": fps
            })

        return fps_points

    @staticmethod
    async def extract_vsync_app_points(tp: "TraceProcessor") -> list[dict]:
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
                "ts": ts_curr / 1e6,  # 转为 ms
                "fps": fps
            })

        return fps_points

    @staticmethod
    async def mark_consecutive_jank(frames: list[dict], min_count: int = 2) -> list[dict]:
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
    async def annotate_fps(frames: list[dict], vsync_sys: list[dict], vsync_app: list[dict]) -> None:
        ts_key, fps_key, max_delta_ms = "ts", "fps", 50.0

        async def build_index(vsync_list: list[dict], key: str) -> list[float]:
            return [v[key] for v in vsync_list]

        async def find_nearest(ts: float, ts_list: list[float], vsync_list: list[dict]) -> float | None:
            if not vsync_list or not ts_list:
                return None
            pos = bisect_left(ts_list, ts)
            candidates = []
            if pos < len(ts_list):
                candidates.append(vsync_list[pos])
            if pos > 0:
                candidates.append(vsync_list[pos - 1])
            nearest = min(candidates, key=lambda v: abs(v[ts_key] - ts))
            return nearest[fps_key] if abs(nearest[ts_key] - ts) <= max_delta_ms else None

        vsync_sys_ts = await build_index(vsync_sys, ts_key)
        vsync_app_ts = await build_index(vsync_app, ts_key)

        for f in frames:
            timestamp_ms = f["timestamp_ms"]
            f["fps_sys"] = await find_nearest(timestamp_ms, vsync_sys_ts, vsync_sys)
            f["fps_app"] = await find_nearest(timestamp_ms, vsync_app_ts, vsync_app)


if __name__ == '__main__':
    pass
