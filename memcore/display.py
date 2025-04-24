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

import time
import random
import asyncio
from pathlib import Path
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
        color_schemes = {
            "Ocean Breeze": ["#AFD7FF", "#87D7FF", "#5FAFD7"],  # 根 / 中间 / 文件
            "Forest Pulse": ["#A8FFB0", "#87D75F", "#5FAF5F"],
            "Neon Sunset": ["#FFAF87", "#FF875F", "#D75F5F"],
            "Midnight Ice": ["#C6D7FF", "#AFAFD7", "#8787AF"],
            "Cyber Mint": ["#AFFFFF", "#87FFFF", "#5FD7D7"]
        }
        file_icons = {
            "folder": "📁",
            ".json": "📦",
            ".yaml": "🧾",
            ".yml": "🧾",
            ".md": "📝",
            ".log": "📄",
            ".html": "🌐",
            ".sh": "🔧",
            ".bat": "🔧",
            ".db": "🗃️",
            ".sqlite": "🗃️",
            ".zip": "📦",
            ".tar": "📦",
            "default": "📄"
        }
        text_color = random.choice([
            "#8A8A8A", "#949494", "#9E9E9E", "#A8A8A8", "#B2B2B2"
        ])

        root_color, folder_color, file_color = random.choice(list(color_schemes.values()))

        choice_icon: callable = lambda x: file_icons["folder"] if (y := Path(x)).is_dir() else (
            file_icons[n] if (n := y.name.lower()) in file_icons else file_icons["default"]
        )

        parts = Path(file_path).parts

        # 根节点
        root = parts[0]
        tree = Tree(
            f"[bold {text_color}]{choice_icon(root)} {root}[/]", guide_style=f"bold {root_color}"
        )
        current_path = parts[0]
        current_node = tree

        # 处理中间的文件夹
        for part in parts[1:-1]:
            current_path = Path(current_path, part)
            current_node = current_node.add(
                f"[bold {text_color}]{choice_icon(current_path)} {part}[/]", guide_style=f"bold {folder_color}"
            )

        ext = (file := Path(parts[-1])).suffix.lower()
        current_node.add(f"[bold {file_color}]{choice_icon(ext)} {file.name}[/]")

        Grapher.console.print("\n", tree, "\n")

    @staticmethod
    async def flame_manifest() -> None:
        """
        启动动画。
        """
        startup_banners = random.choice([
            "initializing memory scanner ...",
            "calibrating baseline thresholds ...",
            "activating neural sweep engine ...",
            "preparing core diagnostic grid ...",
            "linking system memory streams ...",
            "verifying test environment ...",
            "scanning system layout ...",
            "syncing memory sensors ...",
            "establishing memory context ...",
            "priming analytic subsystems ..."
        ])

        completion_banners = random.choice([
            "memory baseline captured successfully.",
            "all memory ranges verified.",
            "scan complete — no anomalies detected.",
            "test finished with optimal memory state.",
            "system passed baseline integrity check.",
            "memory sweep concluded without error.",
            "core scan confirmed baseline signature.",
            "no memory drift detected in target range.",
            "test sequence completed successfully.",
            "diagnostic grid returned stable metrics."
        ])

        Grapher.console.print(
            f"\n[bold #5FD7FF][{const.APP_DESC}::Engine] {const.APP_DESC} {startup_banners}\n"
        )

        width, height = 30, 5
        frames, interval = 60, 0.06

        particles = ["█", "▇", "▓", "▒", "░"]

        flame_presets = {
            "phoenix_ember": ["#FFE082", "#FFB300", "#FB8C00", "#E65100", "#BF360C"],
            "glacier_soul": ["#B3E5FC", "#4FC3F7", "#0288D1", "#01579B", "#002F6C"],
            "forest_will": ["#B9F6CA", "#69F0AE", "#00E676", "#00C853", "#1B5E20"],
            "storm_core": ["#E1BEE7", "#BA68C8", "#9C27B0", "#6A1B9A", "#4A148C"],
            "void_flare": ["#80D8FF", "#40C4FF", "#0091EA", "#263238", "#121212"],
        }

        flame_colors = flame_presets[random.choice(list(flame_presets.keys()))]

        brand = list(const.APP_DESC)

        state = [[None for _ in range(width)] for _ in range(height)]

        positions = {ch: [random.randint(0, height - 1), random.randint(0, width - 1)] for ch in brand}
        center_row, center_col = height // 2, width // 2 - len(brand) // 2
        targets = {ch: [center_row, center_col + i] for i, ch in enumerate(brand)}

        # 计算最大收束距离
        max_distance = max(
            abs(positions[ch][0] - targets[ch][0]) + abs(positions[ch][1] - targets[ch][1])
            for ch in brand
        )

        converge_start = frames - max_distance - int(width * 0.2)

        generate_fire_row: callable = lambda: [
            0 if random.random() < 0.5 else None for _ in range(width)
        ]

        fade_particle: callable = lambda x: None if x is None else (
            x + 1 if x + 1 < len(particles) else None
        )

        async def move_forward(src: list, dst: list) -> list:
            sr, sc = src
            dr, dc = dst

            if sr < dr:
                sr += 1
            elif sr > dr:
                sr -= 1

            if sc < dc:
                sc += 1
            elif sc > dc:
                sc -= 1

            return [sr, sc]

        async def render_frame() -> "Text":
            for ch in brand:
                if frame >= converge_start:
                    positions[ch] = await move_forward(positions[ch], targets[ch])
                else:
                    r, c = positions[ch]
                    r, c = r + random.choice([-1, 0, 1]), c + random.choice([-1, 0, 1])
                    positions[ch] = [max(0, min(height - 1, r)), max(0, min(width - 1, c))]

            letter_positions = {tuple(pos): ch for ch, pos in positions.items()}
            colors = ["#FF00FF", "#FF3399", "#FF6600", "#FFCC00", "#66FF66", "#00FFFF"]
            random.shuffle(colors)

            padding, lines = " " * 8, []
            for r in range(height):
                line = ""
                for c in range(width):
                    if (r, c) in letter_positions:
                        ch = letter_positions[(r, c)]
                        line += f"[bold {colors.pop()}]{ch}[/]"
                    else:
                        idx = state[r][c]
                        if idx is not None:
                            char = particles[idx]
                            color = flame_colors[idx]
                            line += f"[{color}]{char}[/]"
                        else:
                            line += " "
                lines.append(padding + line)

            return Text.from_markup("\n".join(lines))

        with Live(console=Grapher.console, refresh_per_second=int(1 / interval)) as live:
            for frame in range(frames):
                for i in range(height - 1, 0, -1):
                    for j in range(width):
                        state[i][j] = fade_particle(state[i - 1][j])
                state[0] = generate_fire_row()
                live.update(await render_frame())
                await asyncio.sleep(interval)

            await asyncio.sleep(0.2)

        Grapher.console.print(
            f"\n[bold #5FFF87][{const.APP_DESC}::Engine] {const.APP_DESC} {completion_banners}\n"
        )


if __name__ == "__main__":
    pass
