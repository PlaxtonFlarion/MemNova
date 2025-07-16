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


class _Tracer(object):
    """Tracer"""

    # Notes: ======================== MEM ========================

    @staticmethod
    async def extract_rss(tp: "TraceProcessor", app_name: str) -> list[dict]:
        # todo c.value / 1024.0 / 1024.0 AS rss_mb ?
        sql = f"""
               SELECT
                   c.ts / 1e9 AS time_sec,
                   c.value / 1024.0 / 1024.0 AS rss_mb
               FROM counter c
               JOIN process_counter_track t ON c.track_id = t.id
               JOIN process p ON t.upid = p.upid
               WHERE t.name = 'mem.rss' AND p.name = '{app_name}'
               ORDER BY c.ts;
           """
        df = tp.query(sql).as_pandas_dataframe().dropna()
        return df.to_dict("records")

    # Notes: ======================== GFX ========================

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
                "process_name": row.process_name,
                "frame_type": row.present_type or "Unknown",
                "gpu_composition": bool(row.gpu_composition),
                "on_time_finish": bool(row.on_time_finish),
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
    async def annotate_frames(
            frames: list[dict],
            roll_ranges: list[dict],
            drag_ranges: list[dict],
            jank_ranges: list[dict],
            vsync_sys: list[dict],
            vsync_app: list[dict]
    ) -> None:

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

    # Notes: ======================== I/O ========================

    @staticmethod
    async def extract_io(tp: "TraceProcessor") -> dict[str, list[dict]]:
        sql = """
            SELECT
                ts / 1e9 AS time_sec,
                t.name AS counter_name,
                value,
                COALESCE(value - LAG(value) OVER (PARTITION BY t.name ORDER BY ts), 0.0) AS delta
            FROM counter c
            JOIN counter_track t ON c.track_id = t.id
            WHERE t.name IN ('pgpgin', 'pgpgout', 'pswpin', 'pswpout')
            ORDER BY ts;
        """
        df = tp.query(sql).as_pandas_dataframe().dropna()
        grouped = {
            name: df[df["counter_name"] == name][["time_sec", "delta"]].to_dict("records")
            for name in df["counter_name"].unique()
        }
        return grouped

    @staticmethod
    async def extract_block(tp: "TraceProcessor", app_name: str) -> list[dict]:
        sql = f"""
            SELECT
                slice.ts / 1e9 AS time_sec,
                slice.name AS event
            FROM slice
            JOIN thread_track ON slice.track_id = thread_track.id
            JOIN thread ON thread_track.utid = thread.utid
            JOIN process ON thread.upid = process.upid
            WHERE slice.name IN ('block_rq_issue', 'block_rq_complete')
              AND process.name = '{app_name}'
            ORDER BY slice.ts;
        """
        df = tp.query(sql).as_pandas_dataframe()
        return df[["time_sec", "event"]].to_dict("records")

    @staticmethod
    async def extract_metrics(tp: "TraceProcessor", app_name: str) -> dict:
        raise NotImplementedError("")  # todo


class MemAnalyzer(_Tracer):
    """MEM"""

    @staticmethod
    async def extract_metrics(tp: "TraceProcessor", app_name: str) -> dict:
        pass


class GfxAnalyzer(_Tracer):
    """GFX"""

    async def extract_metrics(self, tp: "TraceProcessor", app_name: str) -> dict:
        raw_frames = await self.extract_primary_frames(tp, app_name)

        vsync_sys = await self.extract_vsync_sys_points(tp)  # 系统FPS
        vsync_app = await self.extract_vsync_app_points(tp)  # 应用FPS

        roll_ranges = await self.extract_roll_ranges(tp)  # 滑动区间
        drag_ranges = await self.extract_drag_ranges(tp)  # 拖拽区间

        jank_ranges = await self.mark_consecutive_jank(raw_frames)  # 连续丢帧

        await self.annotate_frames(
            raw_frames, roll_ranges, drag_ranges, jank_ranges, vsync_sys, vsync_app
        )

        return {
            "metadata": {
                "source": "perfetto", "app": app_name
            },
            "raw_frames": raw_frames,
            "vsync_sys": vsync_sys,
            "vsync_app": vsync_app,
            "roll_ranges": roll_ranges,
            "drag_ranges": drag_ranges,
            "jank_ranges": jank_ranges
        }


class IonAnalyzer(_Tracer):
    """I/O"""

    async def extract_metrics(self, tp: "TraceProcessor", app_name: str) -> dict:
        return {
            "metadata": {
                "source": "perfetto", "app": app_name
            },
            "io": await self.extract_io(tp),
            "rss": await self.extract_rss(tp, app_name),
            "block": await self.extract_block(tp, app_name)
        }


if __name__ == '__main__':
    pass
