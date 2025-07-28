#   ____
#  |  _ \ __ _ _ __ ___  ___ _ __
#  | |_) / _` | '__/ __|/ _ \ '__|
#  |  __/ (_| | |  \__ \  __/ |
#  |_|   \__,_|_|  |___/\___|_|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import re
import typing
import argparse
import textwrap
from memnova import const


class Parser(object):
    """
    命令行解析控制器类，用于统一管理命令参数、使用说明与美化输出。
    """

    __parse_engine: typing.Optional["argparse.ArgumentParser"] = None

    def __init__(self):
        custom_made_usage = f"""\
        --------------------------------------------
        \033[1;35m{const.APP_NAME}\033[0m --storm --focus <com.example.app> --imply <device.serial>
        \033[1;35m{const.APP_NAME}\033[0m --sleek --focus <com.example.app> --imply <device.serial>
        \033[1;35m{const.APP_NAME}\033[0m --forge <file.name>
        \033[1;35m{const.APP_NAME}\033[0m --align
        """
        self.__parse_engine = argparse.ArgumentParser(
            const.APP_NAME,
            usage=f" \033[1;35m{const.APP_NAME}\033[0m [-h] [--help] View help documentation\n" + custom_made_usage,
            description=textwrap.dedent(f'''\
                \033[1;32m{const.APP_DESC} · {const.APP_CN}\033[0m
                \033[1m-----------------------------\033[0m
                \033[1;32mCommand Line Arguments {const.APP_DESC}\033[0m
            '''),
            formatter_class=argparse.RawTextHelpFormatter
        )

        mutually_exclusive = self.__parse_engine.add_argument_group(
            title="\033[1m^* 核心操控 *^\033[0m",
            description=textwrap.dedent(f'''\
                \033[1;33m参数互斥\033[0m
            '''),
        )
        major_group = mutually_exclusive.add_mutually_exclusive_group()

        # Workflow: ======================== 参数互斥 ========================

        major_group.add_argument(
            "--storm", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;34m^*星痕律动*^\033[0m
                -------------------------
                - 内存基线，内存泄露，I/O

            ''')
        )
        major_group.add_argument(
            "--sleek", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;34m^*帧影流光*^\033[0m
                -------------------------
                - 流畅度，I/O

            ''')
        )
        major_group.add_argument(
            "--forge",
            type=lambda x: re.sub(r"[^a-zA-Z0-9_\-.\u4e00-\u9fff]", "", x),
            help=textwrap.dedent(f'''\
                \033[1;34m^*真相快照*^\033[0m
                -------------------------
                - 真相快照

            ''')
        )
        major_group.add_argument(
            "--align", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;34m^*星核蓝图*^\033[0m
                -------------------------
                - 星核蓝图

            ''')
        )
        major_group.add_argument(
            "--apply", type=str,
            help=textwrap.dedent(f'''\
                \033[1;34m^*星图凭证*^\033[0m
                -------------------------
                - 星图凭证

            ''')
        )

        # Workflow: ======================== 参数兼容 ========================

        minor_group = self.__parse_engine.add_argument_group(
            title="\033[1m^* 环境桥接 *^\033[0m",
            description=textwrap.dedent(f'''\
                \033[1;32m参数兼容\033[0m
            '''),
        )
        minor_group.add_argument(
            "--focus", type=str, default=None,
            help=textwrap.dedent(f'''\
                \033[1;36m^*数据魔方*^\033[0m
                -------------------------
                - 数据魔方

            ''')
        )
        minor_group.add_argument(
            "--imply", type=str, default=None,
            help=textwrap.dedent(f'''\
                \033[1;36m^*宿主代号*^\033[0m
                -------------------------
                - 宿主代号

            ''')
        )
        minor_group.add_argument(
            "--nodes", type=str, default=None,
            help=textwrap.dedent(f'''\
                \033[1;36m^*中枢节点*^\033[0m
                -------------------------
                - 中枢节点

            ''')
        )
        minor_group.add_argument(
            "--title", type=str, default=None,
            help=textwrap.dedent(f'''\
                \033[1;36m^*星辰序列*^\033[0m
                -------------------------
                - 星辰序列

            ''')
        )
        minor_group.add_argument(
            "--layer", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;36m^*极昼极夜*^\033[0m
                -------------------------
                - 极昼极夜

            ''')
        )

        # Workflow: ======================== 参数兼容 ========================

        extra_group = self.__parse_engine.add_argument_group(
            title="\033[1m^* 观象引擎 *^\033[0m",
            description=textwrap.dedent(f'''\
                \033[1;32m参数兼容\033[0m
            '''),
        )
        extra_group.add_argument(
            "--watch", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;36m^*洞察之镜*^\033[0m
                -------------------------
                - 洞察之镜

            ''')
        )

    @property
    def parse_cmd(self) -> "argparse.Namespace":
        """
        解析后的命令行参数对象，可通过属性方式访问参数值。
        """
        return self.__parse_engine.parse_args()

    @property
    def parse_engine(self) -> typing.Optional["argparse.ArgumentParser"]:
        """
        内部的 argparse 实例，用于访问或打印 help 内容。
        """
        return self.__parse_engine

    @staticmethod
    def parse_integer(value: typing.Any) -> int:
        """
        安全解析整数值，失败时返回默认值 0。
        """
        try:
            return int(max(0, value))
        except TypeError:
            return 0

    @staticmethod
    def parse_decimal(value: typing.Any) -> float:
        """
        安全解析浮点值，自动将负数归零，失败时返回默认值 0.0。
        """
        try:
            return round(float(max(0.0, value)), 2)
        except TypeError:
            return 0.0

    @staticmethod
    def is_valid(val: typing.Any) -> bool:
        """
        判断输入值是否为有效配置项。
        """
        if val is None:
            return False
        if isinstance(val, str) and not val.strip():
            return False
        # 数字类型（int/float）都认为是有效的
        return True


if __name__ == '__main__':
    pass
