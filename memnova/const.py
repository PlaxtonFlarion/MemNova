#    ____                _
#   / ___|___  _ __  ___| |_
#  | |   / _ \| '_ \/ __| __|
#  | |__| (_) | | | \__ \ |_
#   \____\___/|_| |_|___/\__|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

# ========【应用基础信息】========
APP_ITEM         = r"MemNova"
APP_NAME         = r"memrix"
APP_DESC         = r"Memrix"
APP_CN           = r"记忆星核"
APP_VERSION      = r"1.0.0"
APP_YEAR         = r"2024"
APP_LICENSE      = r"Proprietary License"
CHARSET          = r"UTF-8"

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
ALIGN           = f"{APP_NAME}_align.yaml"
LIC_FILE        = f"{APP_NAME}_signature.lic"

SCHEMATIC       = r"schematic"
SUPPORTS        = r"supports"
TEMPLATES       = r"templates"
STRUCTURE       = r"Structure"
SRC_OPERA_PLACE = f"{APP_DESC}_Mix"
SRC_TOTAL_PLACE = f"{APP_DESC}_Report"

# ========【日志与显示设置】========
SHOW_LEVEL    = r"WARNING"
NOTE_LEVEL    = r"INFO"

SUC           = f"[bold #FFFFFF on #32CD32]"
WRN           = f"[bold #000000 on #FFFF00]"
ERR           = f"[bold #FFFFFF on #FF6347]"

PRINT_HEAD    = f"[bold #EEEEEE]{APP_DESC} ::[/]"
OTHER_HEAD    = f"{APP_DESC} ::"
ADAPT_HEAD    = f"{APP_DESC} :"

PRINT_FORMAT  = f"<level>{{level: <8}}</level> | <level>{{message}}</level>"
WRITE_FORMAT  = f"{OTHER_HEAD} <green>{{time:YYYY-MM-DD HH:mm:ss.SSS}}</green> | <level>{{level: <8}}</level> | <level>{{message}}</level>"
WHILE_FORMAT  = f"{OTHER_HEAD} <green>{{time:YYYY-MM-DD HH:mm:ss.SSS}}</green> | <level>{{level: <8}}</level> | {{name}}:{{function}}:{{line}} - <level>{{message}}</level>"

# ========【应用授权】========
BOOTSTRAP_URL      = f"https://appserver-u7hd.onrender.com/bootstrap"
TEMPLATE_META_URL  = f"https://appserver-u7hd.onrender.com/template-meta"
BUSINESS_CASE_URL  = f"https://appserver-u7hd.onrender.com/business-case"
SPEECH_VOICE_URL   = f"https://appserver-u7hd.onrender.com/speech-voice"
X_TEMPLATE_VERSION = f"x_template_version.json"

BASIC_HEADERS = {
    "User-Agent": f"{APP_DESC}@{APP_VERSION}",
    "Content-Type": f"application/json",
    "X-App-ID": PUBLISHER,
    "X-App-Token": f"eyJkYXRhIjogImV5SmhJam9pVFdWdGNtbDRJRlJsWTJodWIyeHZaMmxsY3lCSmJtTXVJaXdpZENJNklqRTNORFUyUVVaRk16RkdPU0lzSW00aU9pSkJORGN5UmtZeFJUSkVSRFFpTENKc2FXTmxibk5sWDJsa0lqb2lSRGRGT1RFeE1EUkJOemszTmtJME1pSjkiLCAic2lnbmF0dXJlIjogImtTOEhrbGRwNmRkUndXVHJCcXFtaHRsbjNwNjJEUzdCMk9XaUdaeHdTYzgreFBxNHJoNFNOa0FaSUlmL0wrc2xONG5yek5EREFLbTJQWWZUbWFBQTM2RjhsUjU3Y2NhSFZ6RHhxeWgxNmNVRXBwVWt2MStTQ0hTVCt1RGIxVWI1T25PaC8wREtZaFlCWUU2NFQ3VmppazNvcDQwQTNkS2VzRzl4OVZPcnhkUGt6akU4UElqVEdieGFIYlNKVG5vSUZRK296OHZCd0pDUXowck12Nk5xa1hCUHhxeEZMUVQzVXJRenR0V2ptUHpsZFQ4SkdLc21GL0QyaDhRbFZMTUM2a3RLY0x5QndkWFpaSmM4eUdwdjZvU3dPdFBxSXg1KzdQVERyOUtUczNSb0hGQXd6SVBiYUtCUXVRRUlxR0thekkxK2tlWTlHVUFsaVdrellmMllvZz09In0=",
    "X-App-Region": f"Global",
    "X-App-Version": f"v{APP_VERSION}"
}

PUBLIC_KEY: bytes = b'''
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA05gFg8awaj6wzvrEgizQ
L3OvK4DrBqOqiFRqR7wKvIN9oq5M+p1IZc1N2k7uPM6cexIvMqzY1ajtyTcDJNhF
ffJpLEDtVWIzH1RO1qzLx3loYo4VfcqlLgWZmB/qa+NWgFenyxMhcNqAOuIYSgN9
36QXFDKL2E1pqI1hhKjPNM4UffXxJB44tUBWixA6D0JG8ws30AzTGQ+h6V1Zjes5
Ki08zaPOQ2qe1r0LS3uXXaOCH8urZtjzKQNmRJKAsDqkTfbU8CLHMadr4Nfq6EkL
4qKs1VUuS+XdmmXdzeNC4RKl9hOWq/vcFE6L2i26zX3JRkH47O8D8GXZPPlneqlD
YQIDAQAB
-----END PUBLIC KEY-----
'''


if __name__ == '__main__':
    pass
