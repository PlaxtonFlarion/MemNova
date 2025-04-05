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
import textwrap
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
            const.APP_NAME, usage=None, description=textwrap.dedent(f'''\
                \033[1;32mMemrix · 记忆星核\033[0m
                \033[1m-----------------------------\033[0m
                \033[1;32mCommand Line Arguments {const.APP_DESC}\033[0m
            '''),
            formatter_class=argparse.RawTextHelpFormatter
        )

        items_group = parser.add_mutually_exclusive_group()
        items_group.add_argument(
            "--memory", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;34m<核心操控> - ^*记忆风暴*^\033[0m
                -------------------------
                启动 **记忆风暴模式**，以持续的周期性方式拉取目标应用的内存使用情况，并将数据写入本地数据库中，供后续报告分析与可视化展示使用。
                可通过 `--sylora` 指定目标应用包名，通过配置文件自定义拉取频率（默认 1 秒，可设定范围为 1~10 秒）。
                适用于长时间稳定性监控、内存波动追踪、异常捕捉及前后台行为对比等复杂测试场景。
                手动中断（Ctrl+C）。
                
            ''')
        )
        items_group.add_argument(
            "--script", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;34m<核心操控> - ^*巡航引擎*^\033[0m 
                -------------------------
                启动 **巡航引擎模式**，读取指定的 **JSON** 文件，根据其中定义的关键步骤，执行 **UI** 自动化操作。
                **Memrix** 会在执行过程中使用 **异步协程机制**，持续实时检测内存状态，确保测试流程与内存监控同步进行。
                **JSON** 脚本需符合自动化指令格式规范（如点击、滑动、输入、等待等），可结合 **UI** 控制引擎使用。
                该命令适用于复杂场景模拟、自动化行为验证、压力场景下的内存异常捕捉等任务。
                手动中断（Ctrl+C）。
                
            ''')
        )
        items_group.add_argument(
            "--report", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;34m<核心操控> - ^*真相快照*^\033[0m 
                -------------------------
                启动 **真相快照模式**，从测试过程中记录的本地数据库中提取原始数据，执行统计分析（如均值、峰值、波动区段）。
                自动生成结构化、可视化的 **HTML** 格式报告，包含内存曲线图、异常区域标记、基本统计指标、测试元信息等。
                支持配合 `--sylora` 限定输出指定批次的数据报告。
                
            ''')
        )
        items_group.add_argument(
            "--config", action="store_true",
            help=textwrap.dedent(f'''\
                \033[1;34m<核心操控> - ^*星核蓝图*^\033[0m 
                -------------------------
                启动 **星核蓝图模式**，**Memrix** 将自动调用系统内置的文本编辑器，打开主配置文件（YAML 格式）。
                文件将以格式化、美观、带注释的方式呈现，便于修改参数行为、默认模式、报告设置等。
                完成编辑并保存后，**Memrix** 会在下次启动时自动加载该配置。
                配置文件是 **Memrix** 的“星核蓝图”，定义了程序的运行地图、参数注入与行为预设。
                
            ''')
        )

        parser.add_argument(
            "--sylora", type=str, default=None,
            help=textwrap.dedent(f'''\
                \033[1;36m<环境桥接> - ^*数据魔方*^\033[0m 
                -------------------------
                用于传递关键上下文信息，根据核心操控命令的不同将自动转换为对应的上下文用途，提供结构化参数支持。
                **记忆风暴模式** 传递 -> **应用程序包名**
                **巡航引擎模式** 传递 -> **脚本文件路径**
                **真相快照模式** 传递 -> **指定报告编号**
                
            ''')
        )
        parser.add_argument(
            "--serial", type=str, default=None,
            help=textwrap.dedent(f'''\
                \033[1;36m<环境桥接> - ^*宿主代号*^\033[0m 
                -------------------------
                指定目标设备的唯一序列号（Serial Number），当连接多个设备或自动识别失败时强制绑定目标设备。
                它是 **Memrix** 与设备之间的“精确信标”，确保测试任务落在指定设备之上，防止误测、多测或设备错位操作。
                
            ''')
        )

        return parser.parse_args()


if __name__ == '__main__':
    pass
