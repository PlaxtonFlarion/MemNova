#   ____  _           _
#  |  _ \(_)___ _ __ | | __ _ _   _
#  | | | | / __| '_ \| |/ _` | | | |
#  | |_| | \__ \ |_) | | (_| | |_| |
#  |____/|_|___/ .__/|_|\__,_|\__, |
#              |_|            |___/
#
# 版权所有 (c) 2024  Memrix(记忆星核)
# 此文件受 Memrix(记忆星核) 许可证的保护。您可以在 LICENSE.md 文件中查看详细的许可条款。
#
# Copyright (c) 2024  Memrix(记忆星核)
# This file is licensed under the Memrix(记忆星核) License. See the LICENSE.md file for more details.
#

import os
import time
from memnova import const
from engine.tackle import Grapher


loading_frames = [
    """[bold #39FFE4]     ~~~         ~~~        ~~~        ~~~
   /     \\     /     \\    /     \\    /     \\
  | (• •) |---| (• •) |--| (• •) |--| (• •) |
   \\_v__/_     \\__v__/    \\__v__/    \\__v__/
     |||         |||        |||        |||
     ===         ===        ===        ===    """,
    """[bold #00FF9F]     ~~~        ~~~         ~~~        ~~~
  /     \\    /     \\     /     \\    /     \\
 | (• •) |--| (• •) |---| (• •) |--| (• •) |
  \\__v__/    \\_v__/_     \\__v__/    \\__v__/
     |||         |||        |||        |||
     ===         ===        ===        ===    """,
    """[bold #99FFCC]     ~~~        ~~~        ~~~         ~~~
  /     \\    /     \\    /     \\     /     \\
 | (• •) |--| (• •) |--| (• •) |---| (• •) |
  \\__v__/    \\__v__/    \\_v__/_     \\__v__/
     |||         |||        |||        |||
     ===         ===        ===        ===    """
]

banner = r"""[bold #00D7AF] __  __                     _     
|  \/  | ___ _ __ ___  _ __(_)_  __
| |\/| |/ _ \ '_ ` _ \| '__| \ \/ /
| |  | |  __/ | | | | | |  | |>  < 
|_|  |_|\___|_| |_| |_|_|  |_/_/\_\
"""

task_done = fr"""[bold #00FF88]
+----------------------------------------+
|            {const.APP_DESC} Task Done            |
+----------------------------------------+
"""

task_fail = fr"""[bold #FF4444]
+----------------------------------------+
|            {const.APP_DESC} Task Fail            |
+----------------------------------------+
"""


class Display(object):
    """
    终端视觉交互显示类，为 Memrix 提供界面标识、启动动画与状态提示输出。

    使用 rich 控制台进行彩色渲染，封装常用的显示行为，包括启动 Logo、版权声明、
    成功/失败提示、屏幕清理以及加载动画。
    """

    @staticmethod
    def clear_screen() -> None:
        """清空终端内容，自动适配平台，Windows 使用 'cls'，其他平台使用 'clear'。"""
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def show_logo() -> None:
        """显示 Memrix 的项目 LOGO（ASCII banner），使用 rich 渲染。"""
        Grapher.console.print(banner)

    @staticmethod
    def show_license() -> None:
        """显示授权声明或使用说明，内容来自 const.APP_DECLARE。"""
        Grapher.console.print(const.APP_DECLARE)

    @staticmethod
    def show_done() -> None:
        """显示任务完成提示信息（使用 task_done 文案）。"""
        Grapher.console.print(task_done)

    @staticmethod
    def show_fail() -> None:
        """显示任务失败或异常提示（使用 task_fail 文案）。"""
        Grapher.console.print(task_fail)

    @staticmethod
    def show_animate() -> None:
        """
        播放项目加载启动动画。

        - 循环打印帧图 loading_frames
        - 模拟初始化过程的视觉反馈
        - 播放后输出 “Core Initialized” 提示
        """

        Display.clear_screen()

        for _ in range(3):
            for frame in loading_frames:
                Display.clear_screen()
                Grapher.console.print(frame)
                time.sleep(0.2)

        Grapher.console.print(
            f"[bold #00FF87]{{ {const.APP_DESC} Wave Linking... Aligning... Done. }}"
        )
        Grapher.console.print(
            f"[bold #00FF87]{{ {const.APP_DESC} Core Initialized. }}\n"
        )


if __name__ == "__main__":
    pass
