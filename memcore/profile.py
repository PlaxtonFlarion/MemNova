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
    """
    配置管理类，用于加载、更新与访问 YAML 配置文件。

    封装了默认配置结构，包括内存采样频率、测试标签、报告参数等，
    并通过属性方式提供统一访问接口。同时支持类型容错转换与 YAML 写入。
    """

    aligns = {
        "common": {
            "label": "应用名称"
        },
        "mem": {
            "mem_speed": 0.5,
            "fg_max": 0.0,
            "fg_avg": 0.0,
            "bg_max": 0.0,
            "bg_avg": 0.0,
            "base_headline": "标题",
            "base_criteria": "准出标准",
            "leak_headline": "标题",
            "leak_criteria": "准出标准"
        },
        "gfx": {
            "gfx_speed": 30.0,
            "headline": "标题",
            "criteria": "准出标准"
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
        """
        当前测试任务的标签或名称，用于日志与报告标注。
        """
        return self.aligns["common"]["label"]

    @property
    def mem_speed(self):
        """
        采样间隔时间（秒）。
        """
        return self.aligns["mem"]["mem_speed"]

    @property
    def fg_max(self):
        """
        报告中前台 PSS 峰值容忍阈。
        """
        return self.aligns["mem"]["fg_max"]

    @property
    def fg_avg(self):
        """
        报告中前台 PSS 平均值容忍阈。
        """
        return self.aligns["mem"]["fg_avg"]

    @property
    def bg_max(self):
        """
        报告中后台 PSS 峰值容忍阈。
        """
        return self.aligns["mem"]["bg_max"]

    @property
    def bg_avg(self):
        """
        报告中后台 PSS 平均值容忍阈。
        """
        return self.aligns["mem"]["bg_avg"]

    @property
    def base_headline(self):
        """
        报告页标题。
        """
        return self.aligns["mem"]["base_headline"]

    @property
    def base_criteria(self):
        """
        报告中的性能评估标准描述。
        """
        return self.aligns["mem"]["base_criteria"]

    @property
    def leak_headline(self):
        """
        报告页标题。
        """
        return self.aligns["mem"]["leak_headline"]

    @property
    def leak_criteria(self):
        """
        报告中的性能评估标准描述。
        """
        return self.aligns["mem"]["leak_criteria"]

    @property
    def gfx_speed(self):
        """
        采样间隔时间（秒）。
        """
        return self.aligns["gfx"]["gfx_speed"]

    @property
    def gfx_headline(self):
        """
        报告页标题。
        """
        return self.aligns["gfx"]["headline"]

    @property
    def gfx_criteria(self):
        """
        报告中的性能评估标准描述。
        """
        return self.aligns["gfx"]["criteria"]

    @label.setter
    def label(self, value: typing.Any):
        self.aligns["common"]["label"] = value

    @mem_speed.setter
    def mem_speed(self, value: typing.Any):
        limit = min(10.0, max(Parser.parse_decimal(value), 0.1))
        self.aligns["mem"]["mem_speed"] = limit

    @fg_max.setter
    def fg_max(self, value: typing.Any):
        self.aligns["mem"]["fg_max"] = Parser.parse_decimal(value)

    @fg_avg.setter
    def fg_avg(self, value: typing.Any):
        self.aligns["mem"]["fg_avg"] = Parser.parse_decimal(value)

    @bg_max.setter
    def bg_max(self, value: typing.Any):
        self.aligns["mem"]["bg_max"] = Parser.parse_decimal(value)

    @bg_avg.setter
    def bg_avg(self, value: typing.Any):
        self.aligns["mem"]["bg_avg"] = Parser.parse_decimal(value)

    @base_headline.setter
    def base_headline(self, value: typing.Any):
        if Parser.is_valid(value):
            self.aligns["mem"]["base_headline"] = value

    @base_criteria.setter
    def base_criteria(self, value: typing.Any):
        if Parser.is_valid(value):
            self.aligns["mem"]["base_criteria"] = value

    @leak_headline.setter
    def leak_headline(self, value: typing.Any):
        if Parser.is_valid(value):
            self.aligns["mem"]["leak_headline"] = value

    @leak_criteria.setter
    def leak_criteria(self, value: typing.Any):
        if Parser.is_valid(value):
            self.aligns["mem"]["leak_criteria"] = value

    @gfx_speed.setter
    def gfx_speed(self, value: typing.Any):
        limit = min(60.0, max(Parser.parse_decimal(value), 5.0))
        self.aligns["gfx"]["gfx_speed"] = limit

    @gfx_headline.setter
    def gfx_headline(self, value: typing.Any):
        if Parser.is_valid(value):
            self.aligns["gfx"]["headline"] = value

    @gfx_criteria.setter
    def gfx_criteria(self, value: typing.Any):
        if Parser.is_valid(value):
            self.aligns["gfx"]["criteria"] = value

    async def load_align(self) -> None:
        """
        加载 YAML 配置文件并更新当前配置项。

        如果指定的配置文件存在且格式正确，则逐项读取其中内容并设置为当前属性值。
        若文件不存在或读取失败（语法错误等），则自动写入默认配置并覆盖原文件。
        """
        try:
            user_align = await FileAssist.read_yaml(self.align_file)
            for key, value in self.aligns.items():
                for k, v in value.items():
                    setattr(self, k, user_align.get(key, {}).get(k, v))
        except (FileNotFoundError, yaml.YAMLError):
            await self.dump_align()

    async def dump_align(self) -> None:
        """
        将当前配置结构写入 YAML 文件，自动格式化并支持中文。
        """
        os.makedirs(os.path.dirname(self.align_file), exist_ok=True)
        await FileAssist.dump_yaml(self.align_file, self.aligns)


if __name__ == '__main__':
    pass
