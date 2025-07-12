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


class Scores(object):

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

        # 🟩 帧延迟：超过理想帧时长的占比（如16.67ms）
        ideal_frame_time = 1000 / 60
        over_threshold = sum(1 for f in frames if f["duration_ms"] > ideal_frame_time)
        latency_score = 1.0 - over_threshold / len(frames)

        # 🟩 FPS 波动越大越扣分；越稳定越高分
        fps_values = [f.get(fps_key) for f in frames if f.get(fps_key)]
        if len(fps_values) >= 2:
            fps_std = statistics.stdev(fps_values)
            fps_stability = max(1.0 - min(fps_std / 10, 1.0), 0.0)
        else:
            fps_stability = 1.0  # 缺失帧率不扣分

        # 🔸 额外考虑平均FPS较低的情况
        fps_avg = sum(fps_values) / len(fps_values) if fps_values else 60
        fps_penalty = min(fps_avg / 60, 1.0)
        fps_score = fps_stability * fps_penalty

        # 🟩 有滑动/拖拽越多说明有交互，不能因为空白区域得高分
        motion_total = sum(r["end_ts"] - r["start_ts"] for r in roll_ranges + drag_ranges)
        motion_score = min(motion_total / duration, 1.0)

        # ✅ 综合得分：越高越流畅
        final_score = (
            jank_score * 0.4 +
            latency_score * 0.2 +
            fps_score * 0.2 +
            motion_score * 0.2
        )

        return round(final_score, 3)

    @staticmethod
    def quality_label(score: float) -> dict:
        if score >= 0.85:
            return {
                "level": "A+",
                "color": "#007E33",  # 深绿
                "label": "极其流畅，无明显波动"
            }
        elif score >= 0.7:
            return {
                "level": "A",
                "color": "#3FAD00",  # 草绿
                "label": "流畅稳定，仅偶尔波动"
            }
        elif score >= 0.55:
            return {
                "level": "B",
                "color": "#F4B400",  # 鲜黄
                "label": "有部分抖动，整体尚可"
            }
        elif score >= 0.4:
            return {
                "level": "C",
                "color": "#FF8C00",  # 深橙
                "label": "波动明显，体验一般"
            }
        elif score >= 0.25:
            return {
                "level": "D",
                "color": "#E04B00",  # 红橙
                "label": "卡顿较多，影响操作"
            }
        else:
            return {
                "level": "E",
                "color": "#B00020",  # 深红
                "label": "严重卡顿，建议优化"
            }


if __name__ == '__main__':
    pass
