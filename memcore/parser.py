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
                - 执行 **内存波动 + I/O 行为** 联合采样。
                - 追踪进程内多维内存指标与系统调用特征，建模资源使用轨迹。

            ''')
        )
        major_group.add_argument(
            "--sleek", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;34m^*帧影流光*^\033[0m
                -------------------------
                - 执行 **帧率稳定性与交互流畅度** 分析。
                - 基于 Perfetto 时序数据，自动识别滑动段 / 拖拽段 / 掉帧段，并评分体验质量。

            ''')
        )
        major_group.add_argument(
            "--forge",
            type=lambda x: re.sub(r"[^a-zA-Z0-9_\-.\u4e00-\u9fff]", "", x),
            help=textwrap.dedent(f'''\
                \033[1;34m^*真相快照*^\033[0m
                -------------------------
                - 生成结构化测试报告与可视化图表。
                - 汇总内存 / IO / 流畅度结果，统一渲染为 HTML 报告。

            ''')
        )
        major_group.add_argument(
            "--align", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;34m^*星核蓝图*^\033[0m
                -------------------------
                - 启用结构化评分机制，自动对内存、流畅度、I/O 等指标进行多维度判级与可视化评估。
                - 所有配置基于 YAML 文件（默认内置），支持覆盖修改或外部引用，结构灵活，参数清晰。
                - 评分结果将用于报告生成、准出标准校验与风险标注。

            ''')
        )
        major_group.add_argument(
            "--apply", type=str,
            help=textwrap.dedent(f'''\
                \033[1;34m^*星图凭证*^\033[0m
                -------------------------
                - 使用激活码向远程授权中心发起请求，获取签名后的授权数据。
                - 授权数据将绑定当前设备指纹，并以 LIC 文件形式存储在本地。

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
                - 传递应用包名。

            ''')
        )
        minor_group.add_argument(
            "--imply", type=str, default=None,
            help=textwrap.dedent(f'''\
                \033[1;36m^*宿主代号*^\033[0m
                -------------------------
                - 指定目标设备的唯一序列号，当连接多个设备或自动识别失败时强制绑定目标设备。

            ''')
        )
        minor_group.add_argument(
            "--nodes", type=str, default=None,
            help=textwrap.dedent(f'''\
                \033[1;36m^*中枢节点*^\033[0m
                -------------------------
                - 指定文件夹名称，作为任务的挂载目录或输出目录。数据的中转与聚合中心。
                - 每次采集任务会将所有数据输出到一个对应的文件夹中，便于归档与后续生成报告。

            ''')
        )
        minor_group.add_argument(
            "--title", type=str, default=None,
            help=textwrap.dedent(f'''\
                \033[1;36m^*星辰序列*^\033[0m
                -------------------------
                - 设置报告主标题，便于区分不同测试任务的上下文。

            ''')
        )
        minor_group.add_argument(
            "--atlas", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;36m^*涟漪视界*^\033[0m
                -------------------------
                - 任务完成后自动生成结构化图表报告，实现一体化流程。

            ''')
        )

        minor_group.add_argument(
            "--layer", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;36m^*极昼极夜*^\033[0m
                -------------------------
                - 在分析阶段区分 **前台** 与 **后台** 阶段内存数据。
                - 输出分段图表，提升可视化精度。

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
    def parse_decimal(value: typing.Any) -> float:
        """
        安全解析浮点值，自动将负数归零，失败时返回默认值 0.0。
        """
        try:
            return round(max(0.0, float(value)), 2)
        except (TypeError, ValueError):
            return 0.0


if __name__ == '__main__':
    pass
