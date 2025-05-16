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

# ========【应用基础信息】========
APP_ITEM         = r"MemNova"
APP_NAME         = r"memrix"
APP_DESC         = r"Memrix"
APP_CN           = r"记忆星核"
APP_VERSION      = r"1.0.0"
APP_YEAR         = r"2024"
APP_LICENSE      = r"Proprietary License"
ENCODING         = r"UTF-8"

AUTHOR           = r"AceKeppel"
EMAIL            = r"AceKeppel@outlook.com"
APP_URL          = r"https://github.com/PlaxtonFlarion/SoftwareCenter"

PUBLISHER        = f"{APP_DESC} Technologies Inc."
COPYRIGHT        = f"Copyright (C) {APP_YEAR} {APP_DESC}. All rights reserved."

DECLARE = f"""\
[bold][bold #00D7AF]>>> {APP_DESC} :: {APP_CN} <<<[/]
[bold #FF8787]Copyright (C)[/] {APP_YEAR} {APP_DESC}. All rights reserved.
Version [bold #FFD75F]{APP_VERSION}[/] :: Licensed software. Authorization required.
{'-' * 59}
"""

# ========【路径与资源配置】========
TOTAL_DIR       = f"{APP_DESC}_Library"
SUBSET_DIR      = r"Tree"
SUMMARY         = r"Summary"
DB_FILE         = f"{APP_NAME}_data.db"
CONFIG          = f"{APP_NAME}_config.yaml"
LIC_FILE        = f"{APP_NAME}_signature.lic"

SCHEMATIC       = r"schematic"
STRUCTURE       = r"Structure"
SRC_OPERA_PLACE = f"{APP_DESC}_Mix"
SRC_TOTAL_PLACE = f"{APP_DESC}_Report"

# ========【日志与显示设置】========
DISPLAY_LEVEL = r"WARNING"

SUC           = f"[bold #FFFFFF on #32CD32]"
WRN           = f"[bold #000000 on #FFFF00]"
ERR           = f"[bold #FFFFFF on #FF6347]"

PRINT_HEAD    = f"[bold #EEEEEE]{APP_DESC} ::[/]"
OTHER_HEAD    = f"{APP_DESC} ::"
ADAPT_HEAD    = f"{APP_DESC} :"

PRINT_FORMAT  = f"<level>{{level: <8}}</level> | <level>{{message}}</level>"
WRITE_FORMAT  = f"{OTHER_HEAD} <green>{{time:YYYY-MM-DD HH:mm:ss.SSS}}</green> | <level>{{level: <8}}</level> | <level>{{message}}</level>"
WHILE_FORMAT  = f"{OTHER_HEAD} <green>{{time:YYYY-MM-DD HH:mm:ss.SSS}}</green> | <level>{{level: <8}}</level> | {{name}}:{{function}}:{{line}} - <level>{{message}}</level>"


if __name__ == '__main__':
    pass
