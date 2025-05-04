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
import typing
import random
import asyncio
import textwrap
from pathlib import Path
from rich.text import Text
from rich.tree import Tree
from rich.live import Live
from rich.console import Console
from memnova import const


class Display(object):
    """
    终端视觉交互显示类，提供界面标识、启动动画与状态提示输出。
    """
    console: typing.Optional["Console"] = Console()

    def __init__(self, display_level: str):
        self.display_level = display_level

    @staticmethod
    def view(msg: typing.Any) -> None:
        """
        输出一条结构化视图日志消息，格式为：[时间] | VIEW | 消息内容。

        常用于关键提示信息、结果确认、用户交互回显等视觉日志展示，
        通过 rich 格式美化输出，提升终端体验。

        Parameters
        ----------
        msg : Any
            要显示的日志内容（可为字符串、对象、异常等）。
        """
        Display.console.print(
            f"{const.APP_DESC} {time.strftime('%Y-%m-%d %H:%M:%S')} | [#00D787]VIEW[/] | {msg}"
        )

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
        Display.console.print(f"[bold #00D7AF]{banner}")

    @staticmethod
    def show_license() -> None:
        """
        显示授权声明或使用说明，内容来自 const.APP_DECLARE。
        """
        Display.console.print(const.APP_DECLARE)

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
        Display.console.print(task_done)

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
        Display.console.print(task_exit)

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
        Display.console.print(task_fail)

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

        with Live(console=Display.console, refresh_per_second=30) as live:
            for _ in range(5):
                for index, i in enumerate(loading_frames):
                    live.update(
                        f"[bold {palette[index]}]{Text.from_markup(i)}"
                    )
                    time.sleep(0.2)

        Display.console.print(
            f"[bold #00FF87]{{ {const.APP_DESC} Wave Linking... Aligning... Done. }}"
        )
        Display.console.print(
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

        with Live(console=Display.console, refresh_per_second=30) as live:
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

        Display.console.print("\n", tree, "\n")

    @staticmethod
    async def flame_manifest() -> typing.Coroutine | None:
        """
        模拟火焰动效，启动动画。
        """
        start_banners = random.choice([
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

        close_banners = random.choice([
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

        Display.console.print(
            f"\n[bold #5FD7FF][{const.APP_DESC}::Engine] {const.APP_DESC} {start_banners}\n"
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

        def move_forward(src: list, dst: list) -> list:
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

        def render_frame() -> "Text":
            for ch in brand:
                if frame >= converge_start:
                    positions[ch] = move_forward(positions[ch], targets[ch])
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

        with Live(console=Display.console, refresh_per_second=int(1 / interval)) as live:
            for frame in range(frames):
                for i in range(height - 1, 0, -1):
                    for j in range(width):
                        state[i][j] = fade_particle(state[i - 1][j])
                state[0] = generate_fire_row()
                live.update(render_frame())
                await asyncio.sleep(interval)

            await asyncio.sleep(0.2)

        Display.console.print(
            f"\n[bold #5FFF87][{const.APP_DESC}::Engine] {const.APP_DESC} {close_banners}\n"
        )

    async def system_disintegrate(self) -> typing.Coroutine | None:
        """
        系统解体风格，收尾动画。
        """
        if self.display_level != const.DISPLAY_LEVEL:
            return None

        width, steps, delay = 42, 6, 0.04
        fade_chars, cursor = list(" .:*%#@!?/▩▨░▒▓"), "▌"

        base_line = f">>> {(text := const.APP_DESC)} | {const.APP_CN} <<<"
        chars = list(base_line)
        statuses = [0] * len(chars)  # 0: 原始, 1: 扰动中, 2: 熄灭

        color = random.choice([
            "#00CFFF",  # 霓光蓝
            "#00FFD5",  # 星舰青
            "#FF7A00",  # 烈焰橙
            "#D66AFF",  # 粉电紫
            "#AAAAAA",  # 远山灰
            "#C9B458",  # 枯金
            "#0066CC",  # 深空蓝
            "#F0F0F0",  # 光子白
            "#00FF88",  # 绿焰
            "#FF3355",  # 赤焰红
            "#FFFF66",  # 电子黄
            "#5D3FD3",  # 黑曜紫
        ])

        def generate_frame() -> "Text":
            line = ""
            for index, char in enumerate(chars):
                if statuses[index] == 2:
                    line += " "
                elif statuses[index] == 1:
                    line += random.choice(fade_chars)
                else:
                    line += char
            return Text(line, style=f"bold {color}")

        with Live(console=self.console, refresh_per_second=30) as live:
            # 打字机 + 光标效果
            current = ""
            for i, c in enumerate(base_line):
                for _ in range(2):  # 光标闪两下
                    blink = current + c + cursor
                    live.update(Text(blink, style=f"bold {color}"))
                    await asyncio.sleep(0.01)
                    live.update(Text((current + c + " "), style=f"bold {color}"))
                    await asyncio.sleep(0.01)
                current += c

            # 最后一个光标闪烁结束
            for _ in range(2):
                live.update(Text((current + cursor), style=f"bold {color}"))
                await asyncio.sleep(0.01)
                live.update(Text((current + " "), style=f"bold {color}"))
                await asyncio.sleep(0.01)

            # 分步熄灭
            for _ in range(steps):
                for i in range(len(chars)):
                    if statuses[i] == 0 and random.random() < 0.3:
                        statuses[i] = 1  # 开始扰动
                    elif statuses[i] == 1 and random.random() < 0.5:
                        statuses[i] = 2  # 熄灭
                live.update(generate_frame())
                await asyncio.sleep(delay)

            # 灰影停顿
            ghost_line = base_line.replace(text, "".join(text))  # 原样灰化
            live.update(Text(ghost_line, style=f"dim {color}"))
            await asyncio.sleep(0.1)

            # 闪灭
            for _ in range(2):
                live.update(Text(" " * width))
                await asyncio.sleep(0.01)
                live.update(Text(ghost_line, style=f"dim {color}"))
                await asyncio.sleep(0.01)

    async def memory_wave(self, memories: dict, dump_close_event: "asyncio.Event") -> typing.Coroutine | None:
        """
        动态内存波动动画，支持状态切换、LOGO淡入淡出、呼吸灯探针。
        """
        if self.display_level != const.DISPLAY_LEVEL:
            return None

        start_banner = [
            "Launching quantum sweep of address space.",
            "Calibrating neural lanes for low-latency tracking.",
            "Activating dimensional scan of memory substrata.",
            "Deploying spectral probes into RAM topology.",
            "Scanning volatile structures for temporal drift.",
            "Engaging parallel memory channels with adaptive sync.",
            "Spooling deep memory resonance patterns.",
            "Establishing vector phase for signal propagation."
        ]

        close_banner = [
            "Memory scan complete. No anomalies detected.",
            "Has successfully charted volatile domains.",
            "Pulse mapping concluded. All nodes synchronized.",
            "Core resonance stabilized. Exiting scan mode.",
            "Signal integrity confirmed across memory grid.",
            "Temporal coherence locked. Diagnostic idle.",
            "Dynamic memory matrix resolved successfully.",
            "All probes disengaged. Standby mode initiated."
        ]

        self.console.print(
            f"\n[bold #00D7FF]{const.APP_DESC} :: {random.choice(start_banner)}\n"
        )

        center_r, center_c = (rows := 5) // 2, (cols := 17) // 2
        symbol, highlight, padding, brand = "◌", "▣", " " * 4, const.APP_DESC

        # 配色方案
        palette = {
            "foreground": [
                "#00FFD1", "#00E6B8", "#00CCAA", "#00B299", "#009988", "#007F77", "#006666"
            ],
            "background": [
                "#1A1A1A", "#2E2E3A", "#3F3F4F", "#4F4F5F", "#606070", "#757580", "#8A8A99"
            ],
            "logo": {
                "foreground": ["#39FF14", "#00FFFF", "#FF00FF", "#FFFF33", "#87F9A7", "#33FFDD"],
                "background": ["#888888", "#AAAAAA", "#CCCCCC", "#B0C4DE", "#D3D3D3", "#D8BFD8"]
            },
            "pulse": {
                "foreground": ["#FFD700", "#FFE066", "#FFF799", "#FFE066"],
                "background": ["#5F5F87", "#70708F", "#8A8AB0", "#70708F"]
            }
        }

        # 初始化状态
        previous_state = memories["mode"]
        pulse_frame, frame_count, logo_transition, max_transition = 0, 0, 0, 6

        # 分层（曼哈顿距离）
        layers = [[] for _ in range(center_r + center_c + 1)]
        for r_ in range(rows):
            for c_ in range(cols):
                d_ = abs(r_ - center_r) + abs(c_ - center_c)
                layers[d_].append((r_, c_))

        def make_header(current_mode: str) -> str:
            sc = "#00FFAA" if memories["mode"].lower().startswith("f") else "#FF99CC"
            return textwrap.dedent(f"""\
                [bold #EEEEEE]Mode: [{sc}]{current_mode}[/]
                Foreground Pulled: [#00FFAA]{memories['foreground']}[/]
                Background Pulled: [#FF99CC]{memories['background']}[/]
            """)

        def render_grid() -> "Text":
            colors = palette[memories["mode"]]
            grid = [["[dim #003333]·[/]" for _ in range(cols)] for _ in range(rows)]

            # 当前活跃区域（除中心）
            active_positions = []
            for d in range(depth + 1):
                active_positions.extend(layers[d])
            active_positions = [p for p in active_positions if p != (center_r, center_c)]

            embed_map = {}
            if len(active_positions) >= len(brand) * 4:
                letters = list(brand)
                base_colors = palette["logo"][memories["mode"]]

                # 淡入淡出处理
                if logo_transition > 0:
                    t = logo_transition / max_transition
                    alpha = 1.0
                    alpha = 2 * (1 - t) if t > 0.5 else 2 * t

                    embed_colors = []
                    for c in base_colors[:len(letters)]:
                        r = int(int(c[1:3], 16) * alpha)
                        g = int(int(c[3:5], 16) * alpha)
                        b = int(int(c[5:7], 16) * alpha)
                        embed_colors.append(f"#{r:02X}{g:02X}{b:02X}")
                else:
                    embed_colors = base_colors[:len(letters)]

                random.shuffle(active_positions)
                embed_targets = active_positions[:len(letters)]
                embed_map = {
                    pos: (ch, col) for pos, ch, col in zip(embed_targets, letters, embed_colors)
                }

            # 渲染图层
            for d in range(depth + 1):
                color = colors[min(d, len(colors) - 1)]
                for r, c in layers[d]:
                    if (r, c) == (center_r, center_c):
                        continue
                    if (r, c) in embed_map:
                        ch, col = embed_map[(r, c)]
                        grid[r][c] = f"[bold {col}]{ch}[/]"
                    else:
                        ch = symbol if not fade else "·"
                        grid[r][c] = f"[bold {color}]{ch}[/]"

            # 呼吸灯中心探针
            pulse_colors = palette["pulse"][memories["mode"]]
            pulse_color = pulse_colors[pulse_frame % len(pulse_colors)]
            grid[center_r][center_c] = f"[bold {pulse_color}]{highlight}[/]"

            lines = [padding + " ".join(row) for row in grid]
            return Text.from_markup(make_header(memories["mode"].upper()) + "\n" + "\n".join(lines))

        async def render_exit_sequence() -> typing.AsyncGenerator[None, str]:
            final_text = f"{brand} Engine"
            visual_center = (cols * 2 - 1) // 2
            pad = " " * (visual_center - (len(final_text) // 2))
            loc = make_header("[bold #FFAF87]END[/]") + "\n" + padding

            cursor_frames = ["▍", "|", "▌", "▎"]
            cursor = cursor_frames[frame_count % len(cursor_frames)]

            for i in range(1, len(final_text) + 1):
                typed = f"{pad}[bold #00D7FF]{final_text[:i]}[/][dim #444444]{cursor}[/]"
                yield Text.from_markup(loc + typed)
                await asyncio.sleep(0.02)

            for _ in range(2):
                yield Text.from_markup(loc + f"{pad}[bold #00D7FF]{final_text}[/]")
                await asyncio.sleep(0.1)
                yield Text.from_markup(loc + f"{pad}[bold #00D7FF]{final_text}[/][dim #00D7FF]▓[/]")
                await asyncio.sleep(0.1)

        live = Live(console=self.console, refresh_per_second=30)
        live.start()

        try:
            depth, direction, depth_max = 0, 1, center_r + center_c

            while not dump_close_event.is_set():
                fade = direction == -1
                live.update(render_grid())
                await asyncio.sleep(0.04)

                pulse_frame += 1
                frame_count += 1
                depth += direction

                # 检测切换 → 启动 LOGO 渐隐/渐显
                if (state := memories["mode"]) != previous_state:
                    logo_transition = max_transition
                    previous_state = state

                if logo_transition > 0:
                    logo_transition -= 1

                if depth >= depth_max:
                    direction = -1
                elif depth <= 0:
                    direction = 1

        except asyncio.CancelledError:
            async for frame in render_exit_sequence():
                live.update(frame)
            live.stop()

        finally:
            self.console.print(
                f"\n[bold #00FF5F]>>> {const.APP_DESC} :: {random.choice(close_banner)} <<<\n"
            )


if __name__ == "__main__":
    pass
