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

        parser.add_argument("--sylora", type=str, default=None, help="数据集合")
        parser.add_argument("--serial", type=str, default=None, help="测试设备")

        return parser.parse_args()


if __name__ == '__main__':
    pass
