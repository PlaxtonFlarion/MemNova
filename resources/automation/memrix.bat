::  __  __                     _
:: |  \/  | ___ _ __ ___  _ __(_)_  __
:: | |\/| |/ _ \ '_ ` _ \| '__| \ \/ /
:: | |  | |  __/ | | | | | |  | |>  <
:: |_|  |_|\___|_| |_| |_|_|  |_/_/\_\
::
:: 版权所有 (c) 2024  Memrix(记忆星核)
:: 此文件受 Memrix(记忆星核) 许可证的保护。您可以在 LICENSE.md 文件中查看详细的许可条款。
::
:: Copyright (c) 2024  Memrix(记忆星核)
:: This file is licensed under the Memrix(记忆星核) License. See the LICENSE.md file for more details.
::

@echo off

:: 设置路径
set EXE_PATH="%~dp0memrix.dist\memrix.exe"

:: 检查是否存在
if not exist %EXE_PATH% (
    echo WARN: not found %EXE_PATH%
    pause
    exit /b
)

:: 运行
%EXE_PATH% --help

:: 请按任意键继续
pause