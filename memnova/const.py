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
M_SUBSET_DIR    = r"MEM_Tree"
F_SUBSET_DIR    = r"GFX_Tree"
SUMMARY         = r"Summary"
DB_FILE         = f"{APP_NAME}_data.db"
ALIGN           = f"{APP_NAME}_align.yaml"
LIC_FILE        = f"{APP_NAME}_signature.lic"
VOICES          = r"voices"
WAVERS          = r"mp3"

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
BOOTSTRAP_URL      = f"https://api.appserverx.com/bootstrap"
TEMPLATE_META_URL  = f"https://api.appserverx.com/template-meta"
BUSINESS_CASE_URL  = f"https://api.appserverx.com/business-case"
SPEECH_META_URL    = f"https://api.appserverx.com/speech-meta"
SPEECH_VOICE_URL   = f"https://api.appserverx.com/speech-voice"
GLOBAL_CF_URL      = f"https://api.appserverx.com/global-configuration"
PREDICT_URL        = r""
TOOLKIT_META_URL   = r"https://api.appserverx.com/toolkit-meta"
MODEL_META_URL     = r""
X_TEMPLATE_VERSION = f"x_template_version.json"

BASIC_HEADERS = {
    "User-Agent": f"{APP_DESC}@{APP_VERSION}",
    "Content-Type": f"application/json",
    "X-App-ID": PUBLISHER,
    "X-App-Token": f"eyJkYXRhIjogImV5SmhjSEFpT2lKTlpXMXlhWGdnVkdWamFHNXZiRzluYVdWeklFbHVZeTRpTENKMGFXMWxJam9pTXpZd01qVkJRVEV5TVVSRElpd2libTl1WTJVaU9pSXpOVVZCT1RaQ1FrRXlRelFpTENKc2FXTmxibk5sWDJsa0lqb2lNek0wTlRJMU1qUkNSakZDTURGRU1pSjkiLCAic2lnbmF0dXJlIjogInlzQVB0dHVlSmIwZ2ZMSnh0Rm5Dd2trSjdOb3hXeVBvdGc4dm04VnpONEt3ZFUweU91NnI2K2tqaU9BTjFsWkhyOFBZNjRrdHlEUmd4dmVtZmFNVzF5dUE2SHBEajY0NHdDdUVQNDVmMGxiV1dpa0dRYUVXdTBkUGdHZDhjMVRUanErTG5pVGt0d0RGUmErZXZmRFRmbXRoSC8renIrRVc3S3VCcG5CWkMrN2hoeThSUk1WUG1LbjV2SnFhR3RKMWhVWEgrZ2pIbCtUc2JCL3dUT2dpRFRCaTg1WHJqSHF4c3lYajhyN2xoVllYeHIxcDF5Y0pNQ3JYMTk4TTA0cnFEd01POGN4MzRBRUtaNmJ0OUx3NERHemVEVkZneUJqTTB5MFA3NmFtZGRpRXZYZlhaeWZxY2xFS3k5MHBya3NBNW1IdCtseTNxeERKZHJPYWhlc1RRUT09In0=",
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
