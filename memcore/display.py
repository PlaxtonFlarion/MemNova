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
import random
from rich.text import Text
from rich.tree import Tree
from rich.live import Live
from memnova import const
from engine.tackle import Grapher


class Display(object):
    """
    终端视觉交互显示类，为 Memrix 提供界面标识、启动动画与状态提示输出。
    """

    @staticmethod
    def show_logo() -> None:
        """
        显示 Memrix 的项目 LOGO（ASCII banner），使用 rich 渲染。
        """
        banner = f"""\
 __  __                     _     
|  \\/  | ___ _ __ ___  _ __(_)_  __
| |\\/| |/ _ \\ '_ ` _ \\| '__| \\ \\/ /
| |  | |  __/ | | | | | |  | |>  < 
|_|  |_|\\___|_| |_| |_|_|  |_/_/\\_\\
        """
        Grapher.console.print(f"[bold #00D7AF]{banner}")

    @staticmethod
    def show_license() -> None:
        """
        显示授权声明或使用说明，内容来自 const.APP_DECLARE。
        """
        Grapher.console.print(const.APP_DECLARE)

    @staticmethod
    def show_done() -> None:
        """
        显示任务完成提示信息（使用 task_done 文案）。
        """
        task_done = fr"""[bold #00FF88]
+----------------------------------------+
|            {const.APP_DESC} Task Done            |
+----------------------------------------+
        """
        Grapher.console.print(task_done)

    @staticmethod
    def show_exit() -> None:
        """
        显示任务退出提示信息（使用 task_exit 文案）。
        """
        task_exit = fr"""[bold #FFEE55]
+----------------------------------------+
|            {const.APP_DESC} Task Exit            |
+----------------------------------------+
        """
        Grapher.console.print(task_exit)

    @staticmethod
    def show_fail() -> None:
        """
        显示任务失败或异常提示（使用 task_fail 文案）。
        """
        task_fail = fr"""[bold #FF4444]
+----------------------------------------+
|            {const.APP_DESC} Task Fail            |
+----------------------------------------+
        """
        Grapher.console.print(task_fail)

    @staticmethod
    def show_animate() -> None:
        """
        播放项目加载启动动画。
        """
        loading_frames = [
            f"""\
     ~~~         ~~~        ~~~        ~~~
   /     \\     /     \\    /     \\    /     \\
  | (• •) |---| (• •) |--| (• •) |--| (• •) |
   \\_v__/_     \\__v__/    \\__v__/    \\__v__/
     |||         |||        |||        |||
     ===         ===        ===        ===    """,
            f"""\
     ~~~        ~~~         ~~~        ~~~
  /     \\    /     \\     /     \\    /     \\
 | (• •) |--| (• •) |---| (• •) |--| (• •) |
  \\__v__/    \\_v__/_     \\__v__/    \\__v__/
     |||         |||        |||        |||
     ===         ===        ===        ===    """,
            f"""\
     ~~~        ~~~        ~~~         ~~~
  /     \\    /     \\    /     \\     /     \\
 | (• •) |--| (• •) |--| (• •) |---| (• •) |
  \\__v__/    \\__v__/    \\_v__/_     \\__v__/
     |||         |||        |||        |||
     ===         ===        ===        ===    """]

        color_palettes = [
            ["#00F5FF", "#7CFC00", "#FFD700"],  # 赛博霓虹
            ["#FF69B4", "#FF1493", "#8A2BE2"],  # 梦幻脉冲
            ["#ADFF2F", "#00FA9A", "#20B2AA"],  # 量子绿链
            ["#FFA500", "#FF6347", "#DC143C"],  # 熔岩能核
            ["#00BFFF", "#1E90FF", "#4169E1"],  # 深海引擎
            ["#DDA0DD", "#BA55D3", "#9400D3"],  # 紫色波段
            ["#FFE4B5", "#FFFACD", "#FAFAD2"],  # 柔光黄波
            ["#B0E0E6", "#ADD8E6", "#E0FFFF"],  # 冰晶流
            ["#66CDAA", "#8FBC8F", "#2E8B57"],  # 冷系脉络
            ["#FFB6C1", "#FFC0CB", "#F08080"],  # 粉调超导
        ]

        palette = random.choice(color_palettes)

        with Live(console=Grapher.console, refresh_per_second=30) as live:
            for _ in range(5):
                for index, i in enumerate(loading_frames):
                    live.update(
                        f"[bold {palette[index]}]{Text.from_markup(i)}"
                    )
                    time.sleep(0.2)

        Grapher.console.print(
            f"[bold #00FF87]{{ {const.APP_DESC} Wave Linking... Aligning... Done. }}"
        )
        Grapher.console.print(
            f"[bold #00FF87]{{ {const.APP_DESC} Core Initialized. }}\n"
        )

    @staticmethod
    def compile_animation() -> None:
        """
        星核脉冲动画（MemCore Pulse）。
        """
        compile_frames = [
            f"""\
    [ ]      [ ]      [ ]
    [ ]      [ ]      [ ]
    [ ]      [ ]      [ ]
        """,
            f"""\
    [■]      [ ]      [ ]
    [ ]      [■]      [ ]
    [ ]      [ ]      [■]
        """,
            f"""\
    [■]      [■]      [ ]
    [■]      [■]      [■]
    [ ]      [■]      [■]
        """,
            f"""\
    [■]      [■]      [■]
    [■]   CORE LINK   [■]
    [■]      [■]      [■]
        """,
            f"""\
    [●]      [●]      [●]
    [●]  {const.APP_DESC} BOOT  [●]
    [●]      [●]      [●]
        """
        ]

        soft_palettes = [
            # 晴雾蓝调（Mist Blue）
            ["#D0EFFF", "#B0DFF0", "#A0CFDF", "#90BFCE", "#80AFBD"],
            # 春风粉雾（Blush Breeze）
            ["#FFE5EC", "#FFD6E0", "#FFC8D5", "#FFB8CA", "#FFA8BF"],
            # 柔光森林（Mint Forest）
            ["#D8F3DC", "#B7E4C7", "#95D5B2", "#74C69D", "#52B788"],
        ]
        colors = random.choice(soft_palettes)

        with Live(console=Grapher.console, refresh_per_second=30) as live:
            for _ in range(6):
                for index, i in enumerate(compile_frames[:-1]):
                    live.update(
                        Text.from_markup(f"[bold {colors[index]}]{i}")
                    )
                    time.sleep(0.2)
            live.update(
                Text.from_markup(f"[bold {colors[-1]}]{compile_frames[-1]}")
            )

        Display.show_logo()
        Display.show_license()

    @staticmethod
    def build_file_tree(file_path: str) -> None:
        """
        显示树状图。
        """
        parts = os.path.abspath(file_path).split(os.sep)

        tree = Tree(f"[bold #AFD7FF]{parts[0]}[/]", guide_style="bold")  # 根节点
        current_path = parts[0]
        current_node = tree

        for part in parts[1:-1]:  # 处理中间的文件夹
            current_path = os.path.join(current_path, part)
            current_node = current_node.add(f"[bold #E4E4E4]{part}[/]", guide_style="bold #87D75F")

        current_node.add(f"[bold #FFAF87]{parts[-1]}[/]")

        Grapher.console.print("\n", tree, "\n")


if __name__ == "__main__":
    pass
