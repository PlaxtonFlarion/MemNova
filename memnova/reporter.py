#   ____                       _
#  |  _ \ ___ _ __   ___  _ __| |_ ___ _ __
#  | |_) / _ \ '_ \ / _ \| '__| __/ _ \ '__|
#  |  _ <  __/ |_) | (_) | |  | ||  __/ |
#  |_| \_\___| .__/ \___/|_|   \__\___|_|
#            |_|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import os
import time
import typing
from pathlib import Path
from memcore.profile import Align
from memnova import const


class Reporter(object):

    def __init__(self, src_total_place: str, vault: str, classify_type: str):
        self.total_dir = os.path.join(src_total_place, const.TOTAL_DIR)
        self.before_time = time.time()

        self.classify_dir = os.path.join(self.total_dir, classify_type)
        if not (classify_dir := Path(self.classify_dir)).exists():
            classify_dir.mkdir(parents=True, exist_ok=True)

        vault = vault or time.strftime("%Y%m%d%H%M%S", time.localtime(self.before_time))

        self.group_dir = os.path.join(self.classify_dir, vault)
        if not (group_dir := Path(self.group_dir)).exists():
            group_dir.mkdir(parents=True, exist_ok=True)

        self.db_file = os.path.join(self.total_dir, const.DB_FILE)
        self.log_file = os.path.join(self.group_dir, f"{const.APP_NAME}_log_{vault}.log")
        self.team_file = os.path.join(self.group_dir, f"{const.APP_NAME}_team_{vault}.yaml")

    @staticmethod
    def mem_rendition(align: "Align" , team_data: dict, report_list: list[dict]) -> dict:

        def mean_of_field(field: str) -> typing.Optional[float]:
            values = [float(i[field]) for i in report_list if field in i]
            return sum(values) / len(values) if values else None

        fg_final = {
            "前台峰值": (avg_fg_max := mean_of_field("fg_max")),
            "前台均值": (avg_fg_avg := mean_of_field("fg_avg")),
        }
        bg_final = {
            "后台峰值": (avg_bg_max := mean_of_field("bg_max")),
            "后台均值": (avg_bg_avg := mean_of_field("bg_avg")),
        }

        conclusion = []
        if avg_fg_max and avg_fg_max > align.fg_max:
            conclusion.append("前台峰值超标")
        if avg_fg_avg and avg_fg_avg > align.fg_avg:
            conclusion.append("前台均值超标")
        if avg_bg_max and avg_bg_max > align.bg_max:
            conclusion.append("后台峰值超标")
        if avg_bg_avg and avg_bg_avg > align.bg_avg:
            conclusion.append("后台均值超标")
        expiry = ["Fail"] if conclusion else ["Pass"]

        return {
            "title": f"{const.APP_DESC} Information",
            "headline": align.headline,
            "major_summary_items": [
                {
                    "label": "测试时间",
                    "value": [team_data.get("time", "Unknown")]
                },
                {
                    "label": "测试结论",
                    "value": expiry + conclusion,
                },
                {
                    "label": "参考标准",
                    "value": [
                        f"FG-MAX: {align.fg_max:.2f} MB",
                        f"FG-AVG: {align.fg_avg:.2f} MB",
                        f"BG-MAX: {align.bg_max:.2f} MB",
                        f"BG-AVG: {align.bg_avg:.2f} MB",
                    ]
                },
                {
                    "label": "准出标准",
                    "value": [align.criteria]
                }
            ],
            "minor_summary_items": [
                [f"{k}: {v} MB" for k, v in fg_final.items() if v],
                [f"{k}: {v} MB" for k, v in bg_final.items() if v],
            ],
            "report_list": report_list
        }


if __name__ == '__main__':
    pass
