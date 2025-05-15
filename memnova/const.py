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

APP_ITEM = r"MemNova"
APP_NAME = r"memrix"
APP_DESC = r"Memrix"
APP_CN = r"记忆星核"
APP_VERSION = r"1.0.0"
APP_LICENSE = r"MIT"
APP_URL = r"https://github.com/PlaxtonFlarion/MemNova"
APP_DECLARE = f"""\
[bold][bold #FF8787](c)[/] [bold #FFAA33]2024[/] [bold #00D7AF]{APP_DESC} :: {APP_CN}[/]
Licensed under the Starbound Intelligence Charter.
Redistribute freely :: let memory echo through every fork.[/]
"""

AUTHOR = r"AceKeppel"
EMAIL = r"AceKeppel@outlook.com"

ENCODING = f"UTF-8"

SUC = f"[bold #FFFFFF on #32CD32]"
WRN = f"[bold #000000 on #FFFF00]"
ERR = f"[bold #FFFFFF on #FF6347]"

TOTAL_DIR = f"{APP_DESC}_Library"
SUBSET_DIR = f"Tree"
DB_FILE = f"{APP_NAME}_data.db"

SUMMARY = f"Summary"

SCHEMATIC = f"schematic"
STRUCTURE = f"Structure"

SRC_OPERA_PLACE = f"{APP_DESC}_Mix"
SRC_TOTAL_PLACE = f"{APP_DESC}_Report"
CONFIG = f"{APP_NAME}_config.yaml"
LIC_FILE = f"{APP_NAME}_signature.lic"

DISPLAY_LEVEL = f"WARNING"

PRINT_HEAD = f"[bold #EEEEEE]{APP_DESC} ::[/]"
OTHER_HEAD = f"{APP_DESC} ::"
ADAPT_HEAD = f"{APP_DESC} :"

PRINT_FORMAT = f"<level>{{level: <8}}</level> | <level>{{message}}</level>"
WRITE_FORMAT = f"{OTHER_HEAD} <green>{{time:YYYY-MM-DD HH:mm:ss.SSS}}</green> | <level>{{level: <8}}</level> | <level>{{message}}</level>"
WHILE_FORMAT = f"{OTHER_HEAD} <green>{{time:YYYY-MM-DD HH:mm:ss.SSS}}</green> | <level>{{level: <8}}</level> | {{name}}:{{function}}:{{line}} - <level>{{message}}</level>"


if __name__ == '__main__':
    pass
