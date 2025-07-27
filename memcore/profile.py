#   ____             __ _ _
#  |  _ \ _ __ ___  / _(_) | ___
#  | |_) | '__/ _ \| |_| | |/ _ \
#  |  __/| | | (_) |  _| | |  __/
#  |_|   |_|  \___/|_| |_|_|\___|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import os
import yaml
import typing
from engine.tinker import FileAssist
from memcore.parser import Parser


class Align(object):
    """Align"""

    aligns = {
        "common": {
            "label": "应用名称",
            "mem_speed": 0.5,
            "gfx_speed": 30.0,
        },
        "mem": {
            "base": {
                "fg_max": 0.0,
                "fg_avg": 0.0,
                "bg_max": 0.0,
                "bg_avg": 0.0,
                "headline": "内存基线",
                "sections": [
                    {
                        "title": "准出标准",
                        "class": "criteria",
                        "value": []
                    }
                ]
            },
            "leak": {
                "headline": "内存泄露",
                "sections": [
                    {
                        "title": "准出标准",
                        "class": "criteria",
                        "lines": True,
                        "value": []
                    }
                ]
            },
        },
        "gfx": {
            "headline": "流畅度",
            "sections": [
                {
                    "title": "参考标准",
                    "class": "refer",
                    "value": []
                },
                {
                    "title": "准出标准",
                    "class": "criteria",
                    "value": []
                }
            ]
        }
    }

    def __init__(self, align_file: typing.Any):
        self.align_file = align_file

    def __getstate__(self):
        return self.aligns

    def __setstate__(self, state):
        self.aligns = state

    @property
    def label(self):
        return self.aligns["common"]["label"]

    @property
    def mem_speed(self):
        return self.aligns["common"]["mem_speed"]

    @property
    def gfx_speed(self):
        return self.aligns["common"]["gfx_speed"]

    @property
    def fg_max(self):
        return self.aligns["mem"]["base"]["fg_max"]

    @property
    def fg_avg(self):
        return self.aligns["mem"]["base"]["fg_avg"]

    @property
    def bg_max(self):
        return self.aligns["mem"]["base"]["bg_max"]

    @property
    def bg_avg(self):
        return self.aligns["mem"]["base"]["bg_avg"]

    # ✅ 获取某个测试项的 headline 字符
    def get_headline(self, section: str, subfield: str = None) -> str:
        if subfield:
            return self.aligns.get(section, {}).get(subfield, {}).get("headline", "")

        return self.aligns.get(section, {}).get("headline", "")

    # ✅ 获取某个测试项的 sections 列表
    def get_sections(self, section: str, subfield: str = None) -> list:
        if subfield:
            return self.aligns.get(section, {}).get(subfield, {}).get("sections", [])

        return self.aligns.get(section, {}).get("sections", [])

    @label.setter
    def label(self, value: typing.Any):
        self.aligns["common"]["label"] = value

    @mem_speed.setter
    def mem_speed(self, value: typing.Any):
        limit = min(10.0, max(Parser.parse_decimal(value), 0.1))
        self.aligns["common"]["mem_speed"] = limit

    @gfx_speed.setter
    def gfx_speed(self, value: typing.Any):
        limit = min(60.0, max(Parser.parse_decimal(value), 5.0))
        self.aligns["common"]["gfx_speed"] = limit

    @fg_max.setter
    def fg_max(self, value: typing.Any):
        self.aligns["mem"]["base"]["fg_max"] = Parser.parse_decimal(value)

    @fg_avg.setter
    def fg_avg(self, value: typing.Any):
        self.aligns["mem"]["base"]["fg_avg"] = Parser.parse_decimal(value)

    @bg_max.setter
    def bg_max(self, value: typing.Any):
        self.aligns["mem"]["base"]["bg_max"] = Parser.parse_decimal(value)

    @bg_avg.setter
    def bg_avg(self, value: typing.Any):
        self.aligns["mem"]["base"]["bg_avg"] = Parser.parse_decimal(value)

    async def load_align(self) -> None:
        try:
            user_align = await FileAssist.read_yaml(self.align_file)

            # 校验并设置三个字段，触发 setter
            self.label = user_align.get("common", {}).get("label", self.label)
            self.mem_speed = user_align.get("common", {}).get("mem_speed", self.mem_speed)
            self.gfx_speed = user_align.get("common", {}).get("gfx_speed", self.gfx_speed)

            # 其余字段直接更新 aligns 内容（不触发 setter）
            for section in list(self.aligns.keys())[1:]:
                if section in user_align:
                    self.aligns[section].update(user_align[section])

        except (FileNotFoundError, yaml.YAMLError):
            await self.dump_align()

    async def dump_align(self) -> None:
        os.makedirs(os.path.dirname(self.align_file), exist_ok=True)
        await FileAssist.dump_yaml(self.align_file, self.aligns)


if __name__ == '__main__':
    pass
