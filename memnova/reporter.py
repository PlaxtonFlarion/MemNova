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
import random
import string
import typing
import aiofiles
from pathlib import Path
from loguru import logger
from jinja2 import (
    Environment, FileSystemLoader
)
from memcore.design import Design
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
    async def make_report(template: str, destination: str, *args, **kwargs) -> None:
        template_dir, template_file = os.path.dirname(template), os.path.basename(template)
        loader = FileSystemLoader(template_dir)
        environment = Environment(loader=loader)
        template = environment.get_template(template_file)
        html = template.render(*args, **kwargs)

        salt: typing.Callable[[], str] = lambda: "".join(
            random.choices(string.ascii_uppercase + string.digits, k=5)
        )
        html_file = os.path.join(destination, f"{const.APP_DESC}_Inform_{salt()}.html")

        async with aiofiles.open(html_file, "w", encoding=const.CHARSET) as f:
            await f.write(html)
            logger.info(html_file)

        Design.build_file_tree(html_file)

    @staticmethod
    def mean_of_field(field: str, report_list: list[dict]) -> typing.Optional[float]:
        values = [
            float(item["metrics"][field])
            for item in report_list
            if "metrics" in item and field in item["metrics"]
        ]
        return sum(values) / len(values) if values else None

    # 内存基线
    def track_rendition(self, align: "Align" , team_data: dict, report_list: list[dict]) -> dict:

        fg_final = {
            "前台峰值": (avg_fg_max := self.mean_of_field("FG-MAX", report_list)),
            "前台均值": (avg_fg_avg := self.mean_of_field("FG-AVG", report_list)),
        }
        bg_final = {
            "后台峰值": (avg_bg_max := self.mean_of_field("BG-MAX", report_list)),
            "后台均值": (avg_bg_avg := self.mean_of_field("BG-AVG", report_list)),
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
                {
                    "value": [f"{k}: {v} MB" for k, v in fg_final.items() if v],
                    "class": "fg-copy"
                },
                {
                    "value": [f"{k}: {v} MB" for k, v in bg_final.items() if v],
                    "class": "bg-copy"
                }
            ],
            "report_list": report_list
        }

    # 内存泄露
    def lapse_rendition(self, align: "Align" , team_data: dict, report_list: list[dict]) -> dict:

        union_final = {
            "内存峰值": self.mean_of_field("MEM-MAX", report_list),
            "内存均值": self.mean_of_field("MEM-AVG", report_list),
        }

        return {
            "title": f"{const.APP_DESC} Information",
            "headline": align.headline,
            "major_summary_items": [
                {
                    "label": "测试时间",
                    "value": [team_data.get("time", "Unknown")]
                },
                {
                    "label": "准出标准",
                    "value": [align.criteria]
                }
            ],
            "minor_summary_items": [
                {
                    "value": [f"{k}: {v} MB" for k, v in union_final.items() if v]
                }
            ],
            "report_list": report_list
        }

    # 流畅度
    @staticmethod
    def sleek_rendition(align: "Align" , team_data: dict, report_list: list[dict]) -> dict:

        return {
            "title": f"{const.APP_DESC} Information",
            "headline": align.headline,
            "major_summary_items": [
                {
                    "label": "测试时间",
                    "value": [team_data.get("time", "Unknown")]
                },
                {
                    "label": "准出标准",
                    "value": [align.criteria]
                }
            ],
            "report_list": report_list
        }


if __name__ == '__main__':
    pass
