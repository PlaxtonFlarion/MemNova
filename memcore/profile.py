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
                "headline": "内存基线",
                "sections": [
                    {
                        "title": "参考标准",
                        "class": "refer",
                        "value": [
                            "前台 FG-MAX、FG-AVG 控制在业务常规阈值",
                            "后台 BG-MAX、BG-AVG 不大幅高于前台",
                            "无突增、无长时间高位波动",
                            "运行周期无内存泄漏表现"
                        ]
                    },
                    {
                        "title": "准出标准",
                        "class": "criteria",
                        "value": [
                            "前台、后台峰值和均值均不超标",
                            "整体内存趋势平稳，无明显异常",
                            "报告周期内未检测到泄漏趋势"
                        ]    
                    }
                ]
            },
            "leak": {
                "headline": "内存泄露",
                "sections": [
                    {
                        "title": "参考标准",
                        "class": "refer",
                        "value": [
                            "PSS 持续上升且无明显回落",
                            "趋势斜率 Slope > 0.01 且拟合优度 R² > 0.5",
                            "内存峰值不因 GC 回落到初始水平",
                            "业务稳定阶段分析，启动等异常不计入",
                            "内存波动但无趋势上涨（R² < 0.5）不判为泄漏"
                        ]
                    },
                    {
                        "title": "准出标准",
                        "class": "criteria",
                        "value": [
                            "内存曲线稳定，无持续上升趋势",
                            "Slope ≤ 0.01 或 R² ≤ 0.5",
                            "峰值能被 GC 有效回收",
                            "排除启动、切后台等短期波动"
                        ]
                    }
                ]
            },
        },
        "gfx": {
            "base": {
                "headline": "流畅度",
                "sections": [
                    {
                        "title": "参考标准",
                        "class": "refer",
                        "value": [
                            "平均 FPS ≥ 55",
                            "最大连续掉帧段 ≤ 2",
                            "单帧耗时 > 50ms 占比 ≤ 3%",
                            "滑动段平均帧率 ≥ 50",
                            "Trace 文件中无明显主线程阻塞"
                        ]
                    },
                    {
                        "title": "准出标准",
                        "class": "criteria",
                        "value": [
                            "整体 FPS 高于 55，波动小",
                            "无严重连续掉帧或主线程卡死",
                            "卡帧（>50ms）比例很低",
                            "滑动区域流畅度达标"
                        ]
                    }
                ]
            }
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

    async def load_align(self) -> None:
        try:
            user_align = await FileAssist.read_yaml(self.align_file)

            self.label = user_align.get("common", {}).get("label", self.label)
            self.mem_speed = user_align.get("common", {}).get("mem_speed", self.mem_speed)
            self.gfx_speed = user_align.get("common", {}).get("gfx_speed", self.gfx_speed)

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
