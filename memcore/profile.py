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
            "app_label": "应用名称",
            "mem_speed": 0.5,
            "gfx_speed": 30.0,
        },
        "mem": {
            "base": {
                "headline": "内存基线",
                "standard": {
                    "fg-max": {
                        "threshold": 0.00, 
                        "direction": "le"
                    },
                    "fg-avg": {
                        "threshold": 0.00, 
                        "direction": "le"
                    },
                    "bg-max": {
                        "threshold": 0.00, 
                        "direction": "le"
                    },
                    "bg-avg": {
                        "threshold": 0.00, 
                        "direction": "le"
                    },
                    "trend": {
                        "desc": "趋势判定",
                        "tooltip": "对内存曲线整体形态进行自动分类，包括线性增长（泄漏）、平稳（正常）、波动（无泄漏特征）、U型/∩型（业务波动）等。主要参考 Slope 斜率与 R² 拟合优度，结合趋势类型（如 Upward、Stable、U-shape 等），辅助泄漏诊断。"
                    },
                    "jitter_index": {
                         "desc": "抖动指数",
                         "tooltip": "衡量曲线短周期内波动幅度。值越小，代表数据更平稳。"
                    }
                },
                "sections": [
                    {
                        "title": "参考标准",
                        "class": "refer",
                        "enter": True,
                        "value": [
                            "前台 FG-MAX、FG-AVG 控制在业务常规阈值，后台 BG-MAX、BG-AVG 不大幅高于前台",
                            "无突增、无长时间高位波动，运行周期无内存泄漏表现"
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
                "standard": {
                    "trend": {
                        "desc": "趋势判定",
                        "tooltip": "对内存曲线整体形态进行自动分类，包括线性增长（泄漏）、平稳（正常）、波动（无泄漏特征）、U型/∩型（业务波动）等。主要参考 Slope 斜率与 R² 拟合优度，结合趋势类型（如 Upward、Stable、U-shape 等），辅助泄漏诊断。"
                    },
                    "poly_trend": {
                        "desc": "多项式趋势判定",
                        "tooltip": "通过二阶多项式拟合内存曲线，自动识别非线性趋势类型：U-shape（先降后升）、∩-shape（先升后降）、Linear（近似直线）等。辅助识别业务活动导致的内存波动，避免误判正常回收为泄漏。"
                    },
                    "trend_score": {
                        "desc": "趋势评分",
                        "tooltip": "根据斜率（Slope）、拟合优度（R²）、持续上升时长等综合指标加权得分，用于量化内存泄漏风险程度。得分越高，泄漏概率越大。一般 0.0~1.0，≥0.7 建议重点排查。"
                    },
                    "jitter_index": {
                         "desc": "抖动指数",
                         "tooltip": "衡量曲线短周期内波动幅度。值越小，代表数据更平稳。"
                    },
                    "slope": {
                        "desc": "趋势斜率",
                        "tooltip": "衡量内存曲线随时间上升的线性速度。Slope > 0.01 时可判定为疑似泄漏。"
                    },
                    "r_squared": {
                        "desc": "拟合优度",
                        "tooltip": "评估曲线与线性趋势的吻合程度。R² > 0.5 表明线性趋势显著，泄漏特征明显。"
                    }
                },
                "sections": [
                    {
                        "title": "参考标准",
                        "class": "refer",
                        "value": [
                            "PSS 持续上升且无明显回落",
                            "趋势斜率 Slope > 0.01 且拟合优度 R² > 0.5"
                        ]
                    },
                    {
                        "title": "准出标准",
                        "class": "criteria",
                        "value": [
                            "内存曲线稳定，无持续上升趋势",
                            "Slope ≤ 0.01 或 R² ≤ 0.5"
                        ]
                    }
                ]
            },
        },
        "gfx": {
            "base": {
                "headline": "流畅度",
                "standard": {
                    "fps_std": {
                        "threshold": 5.0, 
                        "direction": "le",
                        "desc": "帧率波动标准差",
                        "tooltip": "评估帧率稳定性的关键度量。数值越低，说明帧率分布越集中，用户视觉体验越顺滑。≤5代表优秀稳定性。"
                    },
                    "jank_ratio": {
                        "threshold": 0.03, 
                        "direction": "le",
                        "desc": "卡顿帧占比",
                        "tooltip": "表示出现明显卡顿的帧在总帧数中的占比。此指标直观反映异常渲染事件频次，数值越低越佳。≤3%为流畅体验标准。"
                    },
                    "roll_avg_fps": {
                        "threshold": 50.0, 
                        "direction": "ge",
                        "desc": "滑动区间平均帧率",
                        "tooltip": "仅统计滚动场景下的平均帧率，专用于交互性能评估。≥50为一流触感保障。"
                    },
                    "severe_latency_ratio": {
                        "threshold": 0.02, 
                        "direction": "le",
                        "desc": "高延迟帧比例",
                        "tooltip": "统计单帧耗时超过32ms的占比，用于评估极端性能抖动。≤2%为优质区间。"
                    },
                    "longest_low_fps": {
                        "threshold": 2.0, 
                        "direction": "le",
                        "desc": "最长低帧率持续时长",
                        "tooltip": "反映连续低于阈值帧率的最长时间（秒）。数值越短，说明极端性能退化事件越少。≤2s为卓越体验。"
                    }
                },
                "sections": [
                    {
                        "title": "参考标准",
                        "class": "refer",
                        "value": [
                            "AVG FPS ≥ 55",
                            "FPS STD ≤ 5",
                            "JNK % ≤ 3%",
                            "Roll FPS ≥ 50",
                            "Hi-Lat % ≤ 2%",
                            "LMax ≤ 2s"
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
    def app_label(self):
        return self.aligns["common"]["app_label"]

    @property
    def mem_speed(self):
        return self.aligns["common"]["mem_speed"]

    @property
    def gfx_speed(self):
        return self.aligns["common"]["gfx_speed"]

    # ✅ ==== headline 字符 ====
    def get_headline(self, section: str, subfield: str = None) -> str:
        primary_key = "headline"
        if subfield:
            return self.aligns.get(section, {}).get(subfield, {}).get(primary_key, "")

        return self.aligns.get(section, {}).get(primary_key, "")

    # ✅ ==== standard 字典 ====
    def get_standard(self, section: str, subfield: str = None) -> dict:
        primary_key = "standard"
        if subfield:
            value = self.aligns.get(section, {}).get(subfield, {}).get(primary_key, {})
        else:
            value = self.aligns.get(section, {}).get(primary_key, {})

        if not isinstance(value, dict):
            return {}
        
        return {
            k.lower(): {**v, kwd: float(v[kwd])} if (kwd := "threshold") in v else v
            for k, v in value.items() if isinstance(v, dict)
        }

    # ✅ ==== sections 列表 ====
    def get_sections(self, section: str, subfield: str = None) -> list:
        primary_key = "sections"
        if subfield:
            return self.aligns.get(section, {}).get(subfield, {}).get(primary_key, [])

        return self.aligns.get(section, {}).get(primary_key, [])

    @app_label.setter
    def app_label(self, value: typing.Any):
        self.aligns["common"]["app_label"] = value

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

            self.app_label = user_align.get("common", {}).get("app_label", self.app_label)
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
