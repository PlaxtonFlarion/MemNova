#   ____        _ _     _
#  | __ ) _   _(_) | __| |
#  |  _ \| | | | | |/ _` |
#  | |_) | |_| | | | (_| |
#  |____/ \__,_|_|_|\__,_|
#
# 版权所有 (c) 2024  Memrix(记忆星核)
# 此文件受 Memrix(记忆星核) 许可证的保护。您可以在 LICENSE.md 文件中查看详细的许可条款。
#
# Copyright (c) 2024  Memrix(记忆星核)
# This file is licensed under the Memrix(记忆星核) License. See the LICENSE.md file for more details.
#

import os
import sys
import shutil
import typing
import asyncio
from pathlib import Path
from rich.progress import (
    BarColumn, TimeElapsedColumn,
    Progress, SpinnerColumn, TextColumn,
)

from engine.tackle import (
    Grapher, Terminal
)
from memnova import const


async def packaging() -> tuple["Path", typing.Union["Path"], typing.Union["Path"]]:
    operation_system, exe = sys.platform, sys.executable

    venv_base_path, site_packages, target = Path(".venv") if Path(".venv").exists() else Path("venv"), None, None

    compile_cmd = [exe, "-m", "nuitka", "--standalone"]

    if operation_system == "win32":
        if (lib_path := venv_base_path / "Lib" / "site-packages").exists():
            program = Path(f"applications/{const.APP_DESC}.dist")
            site_packages, target, compile_cmd = lib_path.resolve(), program, compile_cmd + [
                "--windows-icon-from-ico=resources/icons/memrix_icn_1.ico",
            ]

    elif operation_system == "darwin":
        if (lib_path := venv_base_path / "lib").exists():
            for sub in lib_path.iterdir():
                if "site-packages" in str(sub):
                    program = Path(f"applications/{const.APP_DESC}.app/Contents/MacOS")
                    site_packages, target, compile_cmd = sub.resolve(), program, compile_cmd + [
                        "--macos-create-app-bundle",
                        f"--macos-app-name={const.APP_DESC}",
                        f"--macos-app-version={const.APP_VERSION}",
                        "--macos-app-icon=resources/images/macos/memrix_macos_icn.png",
                    ]

    else:
        raise RuntimeError(f"Unsupported platforms: {operation_system}")

    compile_cmd += [
        "--nofollow-import-to=uiautomator2",
        "--include-module=deprecation",
        "--include-package=adbutils,pygments",
        "--show-progress", "--show-memory", "--output-dir=applications", f"{const.APP_NAME}.py"
    ]

    return site_packages, target, compile_cmd


async def post_build() -> typing.Coroutine | None:

    async def input_stream() -> typing.Coroutine | None:
        """读取标准流"""
        async for line in transports.stdout:
            line_fmt = line.decode(encoding=const.ENCODING, errors="ignore").strip()
            Grapher.console.print(f"[bold]{const.APP_DESC} | [bold #FFAF5F]Compiler[/] | {line_fmt}")

    async def error_stream() -> typing.Coroutine | None:
        """读取异常流"""
        async for line in transports.stderr:
            line_fmt = line.decode(encoding=const.ENCODING, errors="ignore").strip()
            Grapher.console.print(f"[bold]{const.APP_DESC} | [bold #FFAF5F]Compiler[/] | {line_fmt}")

    async def examine_dependencies() -> typing.Coroutine | None:
        """自动查找虚拟环境中的 site-packages 路径，仅支持 Windows 与 macOS，兼容 .venv / venv。 """
        if not site_packages or not target:
            raise FileNotFoundError(f"Site packages path not found in virtual environment")

        for dep in dependencies:
            src, dst = site_packages / dep, target / dep
            if src.exists():
                done_list.append((src, dst))
            else:
                fail_list.append(dep)
                Grapher.console.print(f"[bold #FF6347][!] Dependency not found -> {dep}")

        if schematic.exists():
            done_list.append(schematic.name)
        else:
            fail_list.append(schematic.name)
            Grapher.console.print(f"[bold #FF6347][!] Dependency not found -> {schematic.name}")

        if len(done_list) != len(dependencies + [schematic.name]):
            raise FileNotFoundError(f"Incomplete dependencies required {fail_list}")

    async def forward_dependencies() -> typing.Coroutine | None:
        """将指定依赖从虚拟环境复制到目标目录。"""
        with Progress(
                TextColumn(
                    text_format=f"[bold #80C0FF]{const.APP_DESC} | {{task.description}}", justify="right"
                ),
                SpinnerColumn(
                    style="bold #FFA07A", speed=1, finished_text="[bold #7CFC00]✓"
                ),
                BarColumn(
                    bar_width=int(Grapher.console.width * 0.5), style="bold #ADD8E6",
                    complete_style="bold #90EE90", finished_style="bold #00CED1"
                ),
                TimeElapsedColumn(),
                TextColumn(
                    "[progress.percentage][bold #F0E68C]{task.completed:>2.0f}[/]/[bold #FFD700]{task.total}[/]"
                ),
                expand=False
        ) as progress:

            task = progress.add_task("Copy Dependencies", total=len(dependencies))

            for src, dst in done_list:
                shutil.copytree(src, dst, dirs_exist_ok=True)
                progress.advance(task)

            shutil.copytree(schematic, target.joinpath(const.SCHEMATIC), dirs_exist_ok=True)
            progress.advance(task)

        # 文件夹重命名
        shutil.move(target, rename := Path(target.parent).joinpath(const.APP_DESC))
        Grapher.console.print(f"[bold #00D787][✓] Rename completed {target.name} → {rename.name}")

    done_list, fail_list = [], []

    schematic, dependencies = Path(os.path.dirname(__file__)).joinpath(const.SCHEMATIC), [
        "uiautomator2"
    ]

    site_packages, target, compile_cmd = await packaging()

    await examine_dependencies()

    Grapher.active("INFO")

    transports = await Terminal.cmd_link(compile_cmd)
    await asyncio.gather(
        *(asyncio.create_task(task()) for task in [input_stream, error_stream])
    )
    await transports.wait()

    await forward_dependencies()


if __name__ == "__main__":
    asyncio.run(post_build())
