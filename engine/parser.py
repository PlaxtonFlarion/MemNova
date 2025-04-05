#   ____
#  |  _ \ __ _ _ __ ___  ___ _ __
#  | |_) / _` | '__/ __|/ _ \ '__|
#  |  __/ (_| | |  \__ \  __/ |
#  |_|   \__,_|_|  |___/\___|_|
#
# 版权所有 (c) 2024  Memrix(记忆星核)
# 此文件受 Memrix(记忆星核) 许可证的保护。您可以在 LICENSE.md 文件中查看详细的许可条款。
#
# Copyright (c) 2024  Memrix(记忆星核)
# This file is licensed under the Memrix(记忆星核) License. See the LICENSE.md file for more details.
#

import typing
import argparse
from memnova import const


class Parser(object):

    @staticmethod
    def parse_integer(content: typing.Any) -> int:
        try:
            return int(max(1, min(10, content)))
        except TypeError:
            return 1

    @staticmethod
    def parse_decimal(content: typing.Any) -> float:
        try:
            return float(max(0, content))
        except TypeError:
            return 0.0

    @staticmethod
    def parse_cmd() -> "argparse.Namespace":
        parser = argparse.ArgumentParser(
            const.APP_NAME, usage=None, description=f"Command Line Arguments {const.APP_DESC}"
        )

        items_group = parser.add_mutually_exclusive_group()
        items_group.add_argument("--memory", action="store_true", help="开始测试")
        items_group.add_argument("--script", action="store_true", help="自动测试")
        items_group.add_argument("--report", action="store_true", help="生成报告")
        items_group.add_argument("--config", action="store_true", help="配置文件")

        parser.add_argument("--sylora", type=str, default=None, help="数据集合")
        parser.add_argument("--serial", type=str, default=None, help="测试设备")

        return parser.parse_args()


if __name__ == '__main__':
    pass
