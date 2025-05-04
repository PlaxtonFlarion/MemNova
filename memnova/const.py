#    ____                _
#   / ___|___  _ __  ___| |_
#  | |   / _ \| '_ \/ __| __|
#  | |__| (_) | | | \__ \ |_
#   \____\___/|_| |_|___/\__|
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
APP_DECLARE: str = f"[bold]^* [bold #00D7AF]{APP_DESC}[/]({APP_CN}) [bold #FFAA33]V{APP_VERSION}[/] Copyright (c) 2024 the {APP_DESC} developers *^[/]\n"

AUTHOR: str = r"AceKeppel"
EMAIL: str = r"AceKeppel@outlook.com"

ENCODING: str = f"UTF-8"
LOG_FORMAT: str = f"{APP_DESC} {{time:YYYY-MM-DD HH:mm:ss}} | {{level}} | {{message}}"

TOTAL_DIR: str = f"{APP_DESC}_Library"
SUBSET_DIR: str = f"Tree"
DB_FILE: str = f"{APP_NAME}_data.db"

SUMMARY: str = f"Summary"

SCHEMATIC: str = f"schematic"
STRUCTURE: str = f"Structure"

SRC_OPERA_PLACE: str = f"{APP_DESC}_Mix"
SRC_TOTAL_PLACE: str = f"{APP_DESC}_Report"

DISPLAY_LEVEL: str = f"WARNING"


if __name__ == '__main__':
    pass
