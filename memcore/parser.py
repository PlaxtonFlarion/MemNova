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
        \033[1;35m{const.APP_NAME}\033[0m --track mem,gfx,io --focus <com.example.app> --imply <device.serial>
        \033[1;35m{const.APP_NAME}\033[0m --forge --focus <file.name>
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

        major_group.add_argument(
            "--track",
            nargs="?",
            type=lambda x: [i for i in re.split(r'[,\s;]+', x) if i],
            help=textwrap.dedent(f'''\
                \033[1;34m^*星痕律动*^\033[0m
                -------------------------
                - 内存基线，内存泄露，流畅度，I/O

            ''')
        )
        major_group.add_argument(
            "--forge", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;34m^*真相快照*^\033[0m
                -------------------------
                - 生成报告

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

        minor_group = self.__parse_engine.add_argument_group(
            title="\033[1m^* 环境桥接 *^\033[0m",
            description=textwrap.dedent(f'''\
                \033[1;32m参数兼容\033[0m
            '''),
        )
        minor_group.add_argument(
            "--hprof", type=str, default=None,
            help=textwrap.dedent(f'''\
                \033[1;36m^*核心碎片*^\033[0m
                -------------------------
                - 核心碎片

            ''')
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
            "--vault", type=str, default=None,
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
            return float(max(0.0, value))
        except TypeError:
            return 0.0


if __name__ == '__main__':
    pass
