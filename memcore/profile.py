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
from engine.tackle import FileAssist
from memcore.parser import Parser


class Align(object):
    """
    配置管理类，用于加载、更新与访问 YAML 配置文件。

    封装了默认配置结构，包括内存采样频率、测试标签、报告参数等，
    并通过属性方式提供统一访问接口。同时支持类型容错转换与 YAML 写入。
    """

    aligns = {
        "Memory": {
            "speed": 1,
            "label": "应用名称"
        },
        "Script": {
            "group": "mission"
        },
        "Report": {
            "fg_max": 0.0,
            "fg_avg": 0.0,
            "bg_max": 0.0,
            "bg_avg": 0.0,
            "headline": "标题",
            "criteria": "标准"
        }
    }

    def __init__(self, align_file: typing.Any):
        self.load_align(align_file)

    def __getstate__(self):
        return self.aligns

    def __setstate__(self, state):
        self.aligns = state

    @property
    def speed(self):
        """
        采样间隔时间（秒），范围建议为 1~10。
        """
        return self.aligns["Memory"]["speed"]

    @property
    def label(self):
        """
        当前测试任务的标签或名称，用于日志与报告标注。
        """
        return self.aligns["Memory"]["label"]

    @property
    def group(self):
        """
        JSON 自动化脚本中任务组字段名。
        """
        return self.aligns["Script"]["group"]

    @property
    def fg_max(self):
        """
        报告中前台 PSS 峰值容忍阈。
        """
        return self.aligns["Report"]["fg_max"]

    @property
    def fg_avg(self):
        """
        报告中前台 PSS 平均值容忍阈。
        """
        return self.aligns["Report"]["fg_avg"]

    @property
    def bg_max(self):
        """
        报告中后台 PSS 峰值容忍阈。
        """
        return self.aligns["Report"]["bg_max"]

    @property
    def bg_avg(self):
        """
        报告中后台 PSS 平均值容忍阈。
        """
        return self.aligns["Report"]["bg_avg"]

    @property
    def headline(self):
        """
        报告页标题。
        """
        return self.aligns["Report"]["headline"]

    @property
    def criteria(self):
        """
        报告中的性能评估标准描述。
        """
        return self.aligns["Report"]["criteria"]

    @speed.setter
    def speed(self, value: typing.Any):
        self.aligns["Memory"]["speed"] = Parser.parse_decimal(value)

    @label.setter
    def label(self, value: typing.Any):
        self.aligns["Memory"]["label"] = value

    @group.setter
    def group(self, value: typing.Any):
        self.aligns["Script"]["group"] = value

    @fg_max.setter
    def fg_max(self, value: typing.Any):
        self.aligns["Report"]["fg_max"] = Parser.parse_decimal(value)

    @fg_avg.setter
    def fg_avg(self, value: typing.Any):
        self.aligns["Report"]["fg_avg"] = Parser.parse_decimal(value)

    @bg_max.setter
    def bg_max(self, value: typing.Any):
        self.aligns["Report"]["bg_max"] = Parser.parse_decimal(value)

    @bg_avg.setter
    def bg_avg(self, value: typing.Any):
        self.aligns["Report"]["bg_avg"] = Parser.parse_decimal(value)

    @headline.setter
    def headline(self, value: typing.Any):
        self.aligns["Report"]["headline"] = value

    @criteria.setter
    def criteria(self, value: typing.Any):
        self.aligns["Report"]["criteria"] = value

    def load_align(self, align_file: typing.Any) -> None:
        """
        加载 YAML 配置文件并更新当前配置项。

        如果指定的配置文件存在且格式正确，则逐项读取其中内容并设置为当前属性值。
        若文件不存在或读取失败（语法错误等），则自动写入默认配置并覆盖原文件。

        Parameters
        ----------
        align_file : str or Path
            配置文件的路径，应为 YAML 格式。
        """
        try:
            user_align = FileAssist.read_yaml(align_file)
            for key, value in self.aligns.items():
                for k, v in value.items():
                    setattr(self, k, user_align.get(key, {}).get(k, v))
        except (FileNotFoundError, yaml.YAMLError):
            self.dump_align(align_file)

    def dump_align(self, align_file: typing.Any) -> None:
        """
        将当前配置结构写入 YAML 文件，自动格式化并支持中文。

        Parameters
        ----------
        align_file : str or Path
            要写入的配置文件路径。
        """
        os.makedirs(os.path.dirname(align_file), exist_ok=True)
        FileAssist.dump_yaml(align_file, self.aligns)


if __name__ == '__main__':
    pass
