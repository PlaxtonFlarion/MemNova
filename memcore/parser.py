#   ____
#  |  _ \ __ _ _ __ ___  ___ _ __
#  | |_) / _` | '__/ __|/ _ \ '__|
#  |  __/ (_| | |  \__ \  __/ |
#  |_|   \__,_|_|  |___/\___|_|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

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
            "--storm", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;34m^*记忆风暴*^\033[0m
                -------------------------
                - 启动 **记忆风暴模式**，以持续的周期性方式拉取目标应用的内存使用情况，并将数据写入本地数据库中，供后续报告分析与可视化展示使用。
                - 可指定目标应用包名，通过配置文件自定义拉取频率（默认 1 秒，可设定范围为 1~10 秒）。
                - 适用于长时间稳定性监控、内存波动追踪、异常捕捉及前后台行为对比等复杂测试场景。
                - 手动中断（Ctrl+C）。

            ''')
        )
        major_group.add_argument(
            "--sleek", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;34m^*z帧影流光*^\033[0m
                -------------------------
                - 流畅度

            ''')
        )
        major_group.add_argument(
            "--forge", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;34m^*真相快照*^\033[0m
                -------------------------
                - 启动 **真相快照模式**，从测试过程中记录的本地数据库中提取原始数据，执行统计分析（如均值、峰值、波动区段）。
                - 自动生成结构化、可视化的 **HTML** 格式报告，包含内存曲线图、异常区域标记、基本统计指标、测试元信息等。
                - 支持限定输出指定批次的数据报告。

            ''')
        )
        major_group.add_argument(
            "--align", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;34m^*星核蓝图*^\033[0m
                -------------------------
                - 启动 **星核蓝图模式**，**Memrix** 将自动调用系统内置的文本编辑器，打开主配置文件（YAML 格式）。
                - 文件将以格式化、美观、带注释的方式呈现，便于修改参数行为、默认模式、报告设置等。
                - 完成编辑并保存后，**Memrix** 会在下次启动时自动加载该配置。
                - 配置文件是 **Memrix** 的“星核蓝图”，定义了程序的运行地图、参数注入与行为预设。

            ''')
        )
        major_group.add_argument(
            "--apply", type=str,
            help=textwrap.dedent(f'''\
                \033[1;34m^*星图凭证*^\033[0m
                -------------------------
                - 使用激活码向远程授权中心发起请求，获取签名后的授权数据。
                - 授权数据将绑定当前设备指纹，并以 LIC 文件形式存储在本地。
                - 一旦激活成功，系统将进入已授权状态，具备完全运行权限。
                - 适用于首次部署、跨环境迁移、临时激活等场景。

            ''')
        )

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
                - 用于传递关键上下文信息，根据核心操控命令的不同将自动转换为对应的上下文用途，提供结构化参数支持。

            ''')
        )
        minor_group.add_argument(
            "--imply", type=str, default=None,
            help=textwrap.dedent(f'''\
                \033[1;36m^*宿主代号*^\033[0m
                -------------------------
                - 指定目标设备的唯一序列号，当连接多个设备或自动识别失败时强制绑定目标设备。
                - 它是 **Memrix** 与设备之间的“精确信标”，确保测试任务落在指定设备之上，防止误测、多测或设备错位操作。

            ''')
        )
        minor_group.add_argument(
            "--vault", type=str, default=None,
            help=textwrap.dedent(f'''\
                \033[1;36m^*中枢节点*^\033[0m
                -------------------------
                - 指定文件夹名称，作为任务的挂载目录或输出目录。数据的中转与聚合中心。
                - 每次内存采集任务会将所有数据输出到一个对应的文件夹中，便于归档与后续生成报告。
                - 你可以手动传入一个自定义名称，例如 `20250410223015`。
                - 如果未传递该参数，将默认生成一个以当前时间戳命名的目录，例如 `20250410223232`。
                - 所有输出文件（日志、HTML 报告等）都会保存在该目录下。

            ''')
        )
        minor_group.add_argument(
            "--title", type=str, default=None,
            help=textwrap.dedent(f'''\
                \033[1;36m^*标题*^\033[0m
                -------------------------
                - 标题

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
                - 启动调试反射视角，用于观察系统运行轨迹与隐藏信息。
                - 展示最详细的调试输出，追踪函数调用与变量变化。

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
