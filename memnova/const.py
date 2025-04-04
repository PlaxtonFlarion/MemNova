#  __  __                     _
# |  \/  | ___ _ __ ___  _ __(_)_  __
# | |\/| |/ _ \ '_ ` _ \| '__| \ \/ /
# | |  | |  __/ | | | | | |  | |>  <
# |_|  |_|\___|_| |_| |_|_|  |_/_/\_\
#
# 版权所有 (c) 2024  Memrix(记忆星核)
# 此文件受 Memrix(记忆星核) 许可证的保护。您可以在 LICENSE.md 文件中查看详细的许可条款。
#
# Copyright (c) 2024  Memrix(记忆星核)
# This file is licensed under the Memrix(记忆星核) License. See the LICENSE.md file for more details.
#

APP_NAME: str = f"memrix"
APP_DESC: str = f"Memrix"
APP_CN: str = f"记忆星核"
APP_VERSION: str = f"1.0.0"
APP_LICENSE: str = r"MIT"
APP_URL: str = f"https://github.com/PlaxtonFlarion/MemNova"
APP_DECLARE: str = f"[bold]^* {APP_DESC}({APP_CN}) version [bold #FFAA33]{APP_VERSION}[/] Copyright (c) 2024 the {APP_DESC} developers *^[/]\n"

AUTHOR: str = r"AceKeppel"
EMAIL: str = r"AceKeppel@outlook.com"

ENCODING: str = f"UTF-8"
LOG_FORMAT: str = f"{APP_DESC} {{time:YYYY-MM-DD HH:mm:ss}} | {{level}} | {{message}}"

SUMMARY: str = f"Summary"
TEMPLATE_DIR: tuple[str, str] = f"schematic", f"templates"
TEMPLATE_FILE: str = f"memory.html"


if __name__ == '__main__':
    pass
